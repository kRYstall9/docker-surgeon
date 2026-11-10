from __future__ import annotations
import json
from logging import Logger
from typing import Any, Dict
from docker import DockerClient
from docker.models.containers import Container
from pprint import pformat


class AgentService:
    def __init__(self, client: DockerClient, logger: Logger):
        self.client = client
        self.logger = logger

    def stream_events(self):
        for event in self.client.events(decode=True):
            try:
                if event.get("Type") == "container":
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                self.logger.error(f"Event stream error: {e}")

    def restart_container(self, id: str | None = None):
        try:
            if not id:
                raise ValueError("Either name or id must be provided")

            container = self.client.containers.get(id)
            container.restart()
        except Exception as e:
            raise RuntimeError(f"Error restarting container: {e}")

    def list_containers(self, all: bool = True, filters: dict = {}) -> list[dict]:
        try:
            containers = self.client.containers.list(all=all, filters=filters)
            return [self._serialize_container(container) for container in containers]
        except Exception as e:
            raise RuntimeError(f"Error listing containers: {e}")

    def get_container(self, id: str | None = None) -> dict:
        try:
            if id:
                container = self.client.containers.get(id)
            else:
                raise ValueError("Either name or id must be provided")

            return self._serialize_container(container)
        except Exception as e:
            raise RuntimeError(f"Error getting container: {e}")

    def get_logs(self, id: str | None = None, tail: int = 10) -> str:
        try:
            if not id:
                raise ValueError("Either name or id must be provided")

            container = self.client.containers.get(id)
            logs = container.logs(tail=tail).decode("utf-8", errors="ignore")
            return logs
        except Exception as e:
            raise RuntimeError(f"Error getting container logs: {e}")

    def recreate_container(self, id: str, parent_name: str) -> dict:
        """
        Stop, remove, and recreate a container that shares a namespace with its parent.
        Returns a dict with 'new_container_id' on success.
        Raises RuntimeError if parent not found.
        """
        try:
            # Resolve parent name to current ID
            try:
                parent_container = self.client.containers.get(parent_name)
                current_parent_id = parent_container.id
            except Exception as e:
                raise RuntimeError(f"Parent container '{parent_name}' not found: {e}")

            # Inspect child container
            api = self.client.api
            container_info = api.inspect_container(id)

            host_config: Dict[str, Any] = container_info.get("HostConfig", {}) or {}
            config: Dict[str, Any] = container_info.get("Config", {}) or {}

            child_name = container_info.get("Name", id)

            # Update namespace mode references
            for mode_key in ("NetworkMode", "IpcMode", "PidMode"):
                mode_value = host_config.get(mode_key, "") or ""
                if mode_value.startswith("container:"):
                    host_config[mode_key] = f"container:{current_parent_id}"

            # Stop child
            try:
                child_docker = self.client.containers.get(id)
                child_docker.stop()
                child_docker.remove(force=True)
            except Exception as e:
                self.logger.warning(f"Error stopping/removing child container: {e}")

            # Prepare create kwargs
            def parse_labels(labels):
                if not labels or not isinstance(labels, dict):
                    return {}
                return {k: v for k, v in labels.items() if v is not None}

            def parse_env(env_list):
                if not env_list:
                    return {}
                result = {}
                for item in env_list:
                    if "=" in item:
                        k, v = item.split("=", 1)
                        result[k] = v
                    else:
                        result[item] = ""
                return result

            container_kwargs = {
                "image": config.get("Image"),
                "name": child_name.lstrip("/"),
                "command": config.get("Cmd"),
                "entrypoint": config.get("Entrypoint"),
                "stdin_open": config.get("OpenStdin", False),
                "working_dir": config.get("WorkingDir") or None,
                "tty": config.get("Tty", False),
                "user": config.get("User") or None,
                "labels": parse_labels(config.get("Labels", {})),
                "environment": parse_env(config.get("Env", [])),
                "healthcheck": config.get("Healthcheck"),
                "volumes": (
                    list(config.get("Volumes", {}).keys())
                    if isinstance(config.get("Volumes"), dict)
                    else (config.get("Volumes", []) or [])
                ),
                # Host-independent configuration fields
                "hostname": config.get("Hostname") or None,
                "domainname": config.get("Domainname") or None,
                "stop_signal": config.get("StopSignal"),
                "stop_timeout": host_config.get("StopTimeout"),
                "runtime": host_config.get("Runtime"),
                "mac_address": host_config.get("MacAddress"),
            }

            host_config_kwargs = {
                "network_mode": host_config.get("NetworkMode"),
                "ipc_mode": host_config.get("IpcMode"),
                "pid_mode": host_config.get("PidMode"),
                "binds": (
                    host_config.get("Binds")
                    if not container_info.get("Mounts")
                    else None
                ),
                "mounts": container_info.get("Mounts"),
                "port_bindings": host_config.get("PortBindings"),
                "restart_policy": host_config.get("RestartPolicy"),
                "volumes_from": host_config.get("VolumesFrom"),
                "dns": host_config.get("Dns"),
                "dns_opt": host_config.get("DnsOpt"),
                "dns_search": host_config.get("DnsSearch"),
                "extra_hosts": host_config.get("ExtraHosts"),
                "log_config": host_config.get("LogConfig"),
                "shm_size": host_config.get("ShmSize"),
                "privileged": host_config.get("Privileged", False),
                "read_only": host_config.get("ReadonlyRootfs", False),
                "mem_limit": host_config.get("Memory"),
                "mem_reservation": host_config.get("MemoryReservation"),
                "memswap_limit": host_config.get("MemorySwap"),
                "mem_swappiness": host_config.get("MemorySwappiness"),
                "cpuset_cpus": host_config.get("CpusetCpus"),
                "cpuset_mems": host_config.get("CpusetMems"),
                "cpu_period": host_config.get("CpuPeriod"),
                "cpu_quota": host_config.get("CpuQuota"),
                "cpu_shares": host_config.get("CpuShares"),
                "cap_add": host_config.get("CapAdd"),
                "cap_drop": host_config.get("CapDrop"),
                "auto_remove": host_config.get("AutoRemove", False),
                "devices": host_config.get("Devices"),
                "device_requests": host_config.get("DeviceRequests"),
                "device_cgroup_rules": host_config.get("DeviceCgroupRules"),
                "security_opt": host_config.get("SecurityOpt"),
                "sysctls": host_config.get("Sysctls"),
                "group_add": host_config.get("GroupAdd"),
                "init": host_config.get("Init"),
                "oom_kill_disable": host_config.get("OomKillDisable"),
                "oom_score_adj": host_config.get("OomScoreAdj"),
                "pids_limit": host_config.get("PidsLimit"),
                "userns_mode": host_config.get("UsernsMode"),
                "uts_mode": host_config.get("UtsMode"),
                "isolation": host_config.get("Isolation"),
                "storage_opt": host_config.get("StorageOpt"),
                "publish_all_ports": host_config.get("PublishAllPorts"),
                "tmpfs": host_config.get("Tmpfs"),
            }

            docker_host_config = api.create_host_config(**host_config_kwargs)

            # --- Handle custom network configurations ---
            network_settings = container_info.get("NetworkSettings", {})
            networks = network_settings.get("Networks", {})
            if networks:
                ep_configs: Dict[str, Dict[str, Any]] = {}
                for net_name, net_cfg in networks.items():
                    # Skip container namespace sharing mode and default networks
                    if net_name.startswith("container:"):
                        continue
                    if net_name in ("bridge", "none"):
                        continue
                    # Collect only non-None endpoint settings
                    ipam = net_cfg.get("IPAMConfig", {}) or {}
                    endpoints: Dict[str, Any] = {}
                    if ipam.get("IPv4Address"):
                        endpoints["ipv4_address"] = ipam.get("IPv4Address")
                    if ipam.get("IPv6Address"):
                        endpoints["ipv6_address"] = ipam.get("IPv6Address")
                    aliases = net_cfg.get("Aliases")
                    if aliases:
                        endpoints["aliases"] = aliases
                    links = net_cfg.get("Links")
                    if links:
                        endpoints["links"] = links
                    link_local_ips = net_cfg.get("LinkLocalIPs")
                    if link_local_ips:
                        endpoints["link_local_ips"] = link_local_ips
                    driver_opt = net_cfg.get("DriverOpts")
                    if driver_opt:
                        endpoints["driver_opt"] = driver_opt
                    if endpoints:
                        ep_configs[net_name] = endpoints
                if ep_configs:
                    networking_config = {
                        name: api.create_endpoint_config(**opts)
                        for name, opts in ep_configs.items()
                    }
                    container_kwargs["networking_config"] = (
                        api.create_networking_config(networking_config)
                    )

            container_kwargs["host_config"] = docker_host_config

            self.logger.debug("New container config:\n%s", pformat(container_kwargs))

            new_container = api.create_container(**container_kwargs)

            api.start(container=new_container["Id"])

            new_container_id = new_container["Id"]

            return {"new_container_id": new_container_id}

        except Exception as e:
            raise RuntimeError(f"Error recreating container: {e}")

    def needs_to_be_recreated(self, container_id: str) -> (bool, str | None):
        try:
            container_config = self.client.api.inspect_container(container_id)
            self.logger.debug(f"Container {container_id} config: {container_config}")
            hc = container_config.get("HostConfig", {}) or {}

            for mode_key in ("NetworkMode", "IpcMode", "PidMode"):
                mode = hc.get(mode_key, "") or ""
                if mode.startswith("container:"):
                    return (True, mode.split("container:")[1])

            return (False, None)
        except Exception as e:
            self.logger.error(str(e))
            return (False, None)

    def _serialize_container(self, container: Container) -> dict:
        attrs = container.attrs

        return {
            "id": container.id,
            "name": container.name,
            "labels": container.labels,
            "state": attrs.get("State", {}),
            "health": attrs.get("State", {}).get("Health", {}),
            "health_status": attrs.get("State", {})
            .get("Health", {})
            .get("Status", "unknown"),
            "exit_code": attrs.get("State", {}).get("ExitCode"),
            "status": attrs.get("State", {}).get("Status", "unknown"),
        }
