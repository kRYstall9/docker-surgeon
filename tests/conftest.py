import pytest
import sys
import os

# Add project root to path so tests can import app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def sample_inspect_data():
    """Full container inspect JSON for a child container that shares network_mode with a parent."""
    return {
        "Id": "child123",
        "Name": "/seanime",
        "Image": "debian:latest",
        "State": {
            "Status": "running",
            "Running": True,
            "Pid": 1234,
            "ExitCode": 0,
        },
        "Created": "2025-01-01T00:00:00.000000Z",
        "Config": {
            "Image": "debian:latest",
            "Labels": {"com.monitor.depends.on": "gluetun", "foo": "bar"},
            "Env": ["MY_ENV=hello", "ANOTHER_VAR=world"],
            "Cmd": ["/bin/bash"],
            "Entrypoint": ["/entrypoint.sh"],
            "WorkingDir": "/app",
            "Tty": False,
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "OpenStdin": False,
            "StdinOnce": False,
            "ExposedPorts": {"80/tcp": {}, "443/tcp": {}},
            "Volumes": {"/data": {}},
            "Healthcheck": {
                "Test": ["CMD", "curl", "-f", "http://localhost:80/health/"],
                "Interval": 30000000000,
                "Timeout": 10000000000,
                "Retries": 3,
                "StartPeriod": 5000000000,
            },
            "User": "1000:1000",
            "Domainname": "",
        },
        "HostConfig": {
            "NetworkMode": "container:oldparent1234567890abcdef0000000000000000000000000000000000000000",
            "IpcMode": "",
            "PidMode": "",
            "Binds": ["/host/data:/container/data:rw"],
            "PortBindings": {"80/tcp": [{"HostIp": "", "HostPort": "8080"}]},
            "RestartPolicy": {"Name": "unless-stopped", "MaximumRetryCount": 0},
            "VolumesFrom": [],
            "Dns": ["8.8.8.8"],
            "ExtraHosts": [],
            "LogConfig": {"Type": "json-file", "Config": {}},
            "ShmSize": 67108864,
            "Privileged": False,
            "ReadonlyRootfs": False,
            "Memory": 536870912,
            "CpusetCpus": "",
            "CpusetMems": "",
            "CpuPeriod": 0,
            "CpuQuota": 0,
            "CpuShares": 0,
            "CapAdd": [],
            "CapDrop": [],
            "AutoRemove": False,
        },
        "NetworkSettings": {
            "Networks": {
                "container:oldparent1234567890abcdef0000000000000000000000000000000000000000": {
                    "IPAMConfig": None,
                    "Links": None,
                    "Aliases": None,
                }
            }
        },
        "GraphDriver": {"Data": {}, "Name": "overlay2"},
        "Mounts": [],
    }
