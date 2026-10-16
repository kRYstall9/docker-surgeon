# type: ignore # Solves lint errors on client attribute functions

from __future__ import annotations
from logging import Logger
from typing import AsyncIterator, Dict, List, Any
from docker import DockerClient

from app.backend.events import Event
from app.backend.models import ContainerProxy
from app.backend.providers import ContainerProvider


class DockerClientProvider(ContainerProvider):

    def __init__(self, client: DockerClient, logger: Logger | None = None):
        super().__init__(client)
        self.logger = logger

    async def get_container(self, id: str):
        container = self.client.containers.get(id)
        return ContainerProxy.from_docker(container, self)

    async def list_containers(self, all: bool = True, filters: dict = {}):
        containers = self.client.containers(all=all, filters=filters)
        return list(ContainerProxy.from_docker(c, self) for c in containers)

    async def restart_container(self, id: str):
        container = self.client.containers.get(id)
        return container.restart()

    async def get_logs(self, id: str, logs_amount: int):
        return self.client.containers.get(id).logs(tail=logs_amount).decode('utf8',errors='ignore')

    async def stream_events(self) -> AsyncIterator[Event]:
        for raw in self.client.events(decode=True):
            id = ''

            if 'id' in raw:
                id = raw['id']
            elif 'Actor' in raw and 'ID' in raw['Actor']:
                id = raw['Actor']['ID']

            yield Event(
                type=raw.get("Action", ''),
                id=id,
                name=raw.get("Actor", {}).get("Attributes", {}).get("name", '')
            )

    async def recreate_container(self, child_id: str, parent_name: str) -> str:
        """Stop, remove, and recreate a container that shares a namespace with its parent.

        Resolves parent_name to the current parent container ID, updates namespace
        references, then recreates the child container.

        Returns the new container ID.
        """
        parent_container = await self.get_container(parent_name)
        if parent_container is None:
            raise Exception(f"Parent container '{parent_name}' not found")

        current_parent_id = parent_container.id

        api = self.client.api
        container_info = api.inspect_container(child_id)

        host_config: Dict[str, Any] = container_info.get("HostConfig", {}) or {}
        config: Dict[str, Any] = container_info.get("Config", {}) or {}

        child_name = container_info.get("Name", child_id)

        for mode_key in ("NetworkMode", "IpcMode", "PidMode"):
            mode_value = host_config.get(mode_key, "") or ""
            if mode_value.startswith("container:"):
                host_config[mode_key] = f"container:{current_parent_id}"

        child_docker_container = self.client.containers.get(child_id)
        child_docker_container.stop()
        child_docker_container.remove(force=True)

        container_kwargs: Dict[str, Any] = {
            "image": config.get("Image"),
            "name": child_name.lstrip("/"),
            "command": config.get("Cmd"),
            "entrypoint": config.get("Entrypoint"),
            "working_dir": config.get("WorkingDir") or None,
            "tty": config.get("Tty", False),
            "stdin_open": config.get("OpenStdin", False),
            "user": config.get("User") or None,
            "labels": self._parse_labels(config.get("Labels", {})),
            "environment": self._parse_env(config.get("Env", [])),
            "healthcheck": config.get("Healthcheck"),
            "ports": self._parse_ports(config.get("ExposedPorts", {})),
            "volumes": list(config.get("Volumes", {}).keys()) if isinstance(config.get("Volumes"), dict) else (config.get("Volumes", []) or []),
        }

        host_config_kwargs = {
            "network_mode": host_config.get("NetworkMode"),
            "ipc_mode": host_config.get("IpcMode"),
            "pid_mode": host_config.get("PidMode"),
            "binds": host_config.get("Binds"),
            "port_bindings": host_config.get("PortBindings"),
            "restart_policy": host_config.get("RestartPolicy"),
            "volumes_from": host_config.get("VolumesFrom"),
            "dns": host_config.get("Dns"),
            "extra_hosts": host_config.get("ExtraHosts"),
            "log_config": host_config.get("LogConfig"),
            "shm_size": host_config.get("ShmSize"),
            "privileged": host_config.get("Privileged", False),
            "read_only": host_config.get("ReadonlyRootfs", False),
            "mem_limit": host_config.get("Memory"),
            "cpu_set": host_config.get("CpusetCpus"),
            "cpu_set_mems": host_config.get("CpusetMems"),
            "cpu_period": host_config.get("CpuPeriod"),
            "cpu_quota": host_config.get("CpuQuota"),
            "cpu_shares": host_config.get("CpuShares"),
            "cap_add": host_config.get("CapAdd"),
            "cap_drop": host_config.get("CapDrop"),
            "auto_remove": host_config.get("AutoRemove", False),
        }

        docker_host_config = api.create_host_config(**host_config_kwargs)

        container_kwargs['host_config'] = docker_host_config

        new_container = api.create_container(**container_kwargs)

        api.start(container=new_container["Id"])

        new_container_id = new_container["Id"]

        return new_container_id

    async def needs_to_be_recreated(self, container: str) -> (bool, str | None):
        try:
            container_config = self.client.api.inspect_container(container)
            self.logger.debug(f"Container {container} config: {container_config}")
            hc = container_config.get("HostConfig", {}) or {}

            for mode_key in ("NetworkMode", "IpcMode", "PidMode"):
                mode = hc.get(mode_key, "") or ""
                if mode.startswith("container:"):
                    return (True, mode.split('container:')[1])

            return (False, None)
        except Exception as e:
            self.logger.error(str(e))
            return (False, None)

    @staticmethod
    def _parse_labels(labels_raw: Any) -> Dict[str, str]:
        """Convert labels from inspect dict to expected format."""
        if not labels_raw:
            return {}
        if isinstance(labels_raw, dict):
            # Filter out None values
            return {k: v for k, v in labels_raw.items() if v is not None}
        return {}

    @staticmethod
    def _parse_env(env_list: Any) -> Dict[str, str]:
        """Convert Env list from inspect to dict."""
        if not env_list:
            return {}
        result = {}
        for item in env_list:
            if "=" in item:
                key, value = item.split("=", 1)
                result[key] = value
            else:
                result[item] = ""
        return result

    @staticmethod
    def _parse_ports(exposed_ports: Any) -> List[int]:
        """Extract port numbers from ExposedPorts dict."""
        if not exposed_ports:
            return []
        result = []
        for port_spec in exposed_ports.keys():
            # port_spec is like "80/tcp" or "443/tcp"
            try:
                port = int(port_spec.split("/")[0])
                result.append(port)
            except (ValueError, IndexError):
                pass
        return result
