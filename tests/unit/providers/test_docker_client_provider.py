import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import docker

# Import after docker is available at top level
from app.backend.providers import DockerClientProvider

NEW_PARENT_ID = "newparent99999999999999999999999999999999999999999999999999999999999"
CHILD_ID = "child123"
OLD_PARENT_ID = "oldparent1234567890abcdef0000000000000000000000000000000000000000"


class TestDockerClientProviderIpcPidMode:
    """Test that IpcMode and PidMode are also updated during recreation."""

    def _get_create_api(self, sample_inspect_data):
        mock_api = MagicMock()
        mock_api.inspect_container = MagicMock(return_value=sample_inspect_data)
        mock_api.create_container = MagicMock(return_value={"Id": "newchild456"})
        mock_api.start = MagicMock()
        return mock_api

    def _get_provider(self, sample_inspect_data):
        create_api = self._get_create_api(sample_inspect_data)
        mock_docker_client = MagicMock()
        child_container = MagicMock()
        child_container.stop = MagicMock()
        child_container.remove = MagicMock()
        child_container.name = "/seanime"
        mock_docker_client.containers.get = MagicMock(return_value=child_container)
        provider = DockerClientProvider(mock_docker_client)
        mock_parent_container = MagicMock()
        mock_parent_container.id = NEW_PARENT_ID
        mock_parent_container.name = "gluetun"
        provider.get_container = AsyncMock(return_value=mock_parent_container)
        return provider, create_api, child_container

    @pytest.mark.asyncio
    async def test_recreate_updates_ipc_mode(self, sample_inspect_data):
        """Verify IpcMode is updated from old parent ID to new parent ID."""
        # Modify the sample data to use IpcMode instead of NetworkMode
        sample_inspect_data["HostConfig"]["IpcMode"] = f"container:{OLD_PARENT_ID}"
        sample_inspect_data["HostConfig"]["NetworkMode"] = "default"

        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("ipc") == f"container:{NEW_PARENT_ID}"

    @pytest.mark.asyncio
    async def test_recreate_updates_pid_mode(self, sample_inspect_data):
        """Verify PidMode is updated from old parent ID to new parent ID."""
        sample_inspect_data["HostConfig"]["PidMode"] = f"container:{OLD_PARENT_ID}"
        sample_inspect_data["HostConfig"]["NetworkMode"] = "default"

        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("pid") == f"container:{NEW_PARENT_ID}"

    @pytest.mark.asyncio
    async def test_recreate_updates_all_namespace_modes(self, sample_inspect_data):
        """Verify all three modes are updated when all are present."""
        sample_inspect_data["HostConfig"]["NetworkMode"] = f"container:{OLD_PARENT_ID}"
        sample_inspect_data["HostConfig"]["IpcMode"] = f"container:{OLD_PARENT_ID}"
        sample_inspect_data["HostConfig"]["PidMode"] = f"container:{OLD_PARENT_ID}"

        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("network_mode") == f"container:{NEW_PARENT_ID}"
        assert host_config.get("ipc") == f"container:{NEW_PARENT_ID}"
        assert host_config.get("pid") == f"container:{NEW_PARENT_ID}"


class TestDockerClientProviderConfigPreservation:
    """Test that all container configuration fields are preserved during recreation."""

    def _get_create_api(self, sample_inspect_data):
        mock_api = MagicMock()
        mock_api.inspect_container = MagicMock(return_value=sample_inspect_data)
        mock_api.create_container = MagicMock(return_value={"Id": "newchild456"})
        mock_api.start = MagicMock()
        return mock_api

    def _get_provider(self, sample_inspect_data):
        create_api = self._get_create_api(sample_inspect_data)
        mock_docker_client = MagicMock()
        child_container = MagicMock()
        child_container.stop = MagicMock()
        child_container.remove = MagicMock()
        child_container.name = "/seanime"
        mock_docker_client.containers.get = MagicMock(return_value=child_container)
        provider = DockerClientProvider(mock_docker_client)
        mock_parent_container = MagicMock()
        mock_parent_container.id = NEW_PARENT_ID
        mock_parent_container.name = "gluetun"
        provider.get_container = AsyncMock(return_value=mock_parent_container)
        return provider, create_api, child_container

    @pytest.mark.asyncio
    async def test_recreate_preserves_healthcheck(self, sample_inspect_data):
        """Healthcheck configuration is preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        expected_healthcheck = {
            "Test": ["CMD", "curl", "-f", "http://localhost:80/health/"],
            "Interval": 30000000000,
            "Timeout": 10000000000,
            "Retries": 3,
            "StartPeriod": 5000000000,
        }
        assert create_kwargs.get("healthcheck") == expected_healthcheck

    @pytest.mark.asyncio
    async def test_recreate_preserves_user(self, sample_inspect_data):
        """User configuration is preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        assert create_kwargs.get("user") == "1000:1000"

    @pytest.mark.asyncio
    async def test_recreate_preserves_dns(self, sample_inspect_data):
        """DNS configuration is preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("dns") == ["8.8.8.8"]

    @pytest.mark.asyncio
    async def test_recreate_preserves_shm_size(self, sample_inspect_data):
        """Shared memory size is preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("shm_size") == 67108864

    @pytest.mark.asyncio
    async def test_recreate_preserves_privileged_and_readonly(self, sample_inspect_data):
        """Privileged and readable rootfs flags are preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("privileged") is False
        assert host_config.get("read_only") is False

    @pytest.mark.asyncio
    async def test_recreate_preserves_log_config(self, sample_inspect_data):
        """Log configuration is preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("log_config") == {"Type": "json-file", "Config": {}}

    @pytest.mark.asyncio
    async def test_recreate_preserves_memory_and_cpu_limits(self, sample_inspect_data):
        """Memory and CPU limit configurations are preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("mem_limit") == 536870912
        assert host_config.get("cpu_period") == 0
        assert host_config.get("cpu_quota") == 0
        assert host_config.get("cpu_shares") == 0


class TestDockerClientProviderEdgeCases:
    """Test edge cases and error handling for recreate_container."""

    def _get_provider(self, sample_inspect_data, extra_host_config=None):
        mock_api = MagicMock()
        if extra_host_config:
            sample_inspect_data["HostConfig"].update(extra_host_config)
        mock_api.inspect_container = MagicMock(return_value=sample_inspect_data)
        mock_api.create_container = MagicMock(return_value={"Id": "newchild456"})
        mock_api.start = MagicMock()

        mock_docker_client = MagicMock()
        child_container = MagicMock()
        child_container.stop = MagicMock()
        child_container.remove = MagicMock()
        child_container.name = "/seanime"
        mock_docker_client.containers.get = MagicMock(return_value=child_container)

        provider = DockerClientProvider(mock_docker_client)

        mock_parent_container = MagicMock()
        mock_parent_container.id = NEW_PARENT_ID
        mock_parent_container.name = "gluetun"
        provider.get_container = AsyncMock(return_value=mock_parent_container)

        return provider, mock_api, child_container

    @pytest.mark.asyncio
    async def test_recreate_handles_empty_labels(self):
        """When labels are missing or empty, recreate should still work."""
        sample_inspect_data = {"Config": {"Labels": None}}
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        # Should not crash - empty/None labels should become {}
        assert create_kwargs.get("labels") == {}

    @pytest.mark.asyncio
    async def test_recreate_handles_empty_host_config(self):
        """When HostConfig is missing, recreate should still work."""
        sample_inspect_data = {"HostConfig": None}
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        # Should not crash - None host_config should result in empty dict
        host_config = create_kwargs.get("host_config", {})
        assert isinstance(host_config, dict)

    @pytest.mark.asyncio
    async def test_recreate_handles_missing_config(self):
        """When Config is missing, recreate should still work."""
        sample_inspect_data = {"Config": None}
        create_api = MagicMock()
        create_api.inspect_container = MagicMock(return_value={"HostConfig": {}})
        create_api.create_container = MagicMock(return_value={"Id": "newchild456"})
        create_api.start = MagicMock()

        mock_docker_client = MagicMock()
        child_container = MagicMock()
        child_container.stop = MagicMock()
        child_container.remove = MagicMock()
        mock_docker_client.containers.get = MagicMock(return_value=child_container)

        provider = DockerClientProvider(mock_docker_client)
        mock_parent_container = MagicMock()
        mock_parent_container.id = NEW_PARENT_ID
        mock_parent_container.name = "gluetun"
        provider.get_container = AsyncMock(return_value=mock_parent_container)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        # Should not crash - None config fields should be handled
        assert create_kwargs.get("image") is None
        assert isinstance(create_kwargs.get("labels", {}), dict)

    @pytest.mark.asyncio
    async def test_recreate_only_updates_matching_container_refs(self, sample_inspect_data):
        """Only modes that start with 'container:' should be updated."""
        # Set NetworkMode to something other than container: prefix
        sample_inspect_data["HostConfig"]["NetworkMode"] = "bridge"
        sample_inspect_data["HostConfig"]["IpcMode"] = "host"
        sample_inspect_data["HostConfig"]["PidMode"] = "host"

        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch("docker.APIClient", return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        # bridge should remain bridge
        assert host_config.get("network_mode") == "bridge"
        # host should remain host
        assert host_config.get("ipc") == "host"
        assert host_config.get("pid") == "host"


class TestDockerClientProviderRecreateContainer:

    def _get_create_api(self, sample_inspect_data):
        """Helper to create mock API that returns the given inspect data."""
        mock_api = MagicMock()
        mock_api.inspect_container = MagicMock(return_value=sample_inspect_data)
        # Return a dict to simulate docker API response
        mock_api.create_container = MagicMock(return_value={"Id": "newchild456"})
        mock_api.start = MagicMock()
        return mock_api

    def _get_provider(self, sample_inspect_data):
        """Helper to create a provider with mocked Docker SDK."""
        create_api = self._get_create_api(sample_inspect_data)

        mock_docker_client = MagicMock()

        child_container = MagicMock()
        child_container.stop = MagicMock()
        child_container.remove = MagicMock()
        child_container.name = "/seanime"
        mock_docker_client.containers.get = MagicMock(return_value=child_container)

        provider = DockerClientProvider(mock_docker_client)

        mock_parent_container = MagicMock()
        mock_parent_container.id = NEW_PARENT_ID
        mock_parent_container.name = "gluetun"
        provider.get_container = AsyncMock(return_value=mock_parent_container)

        return provider, create_api, child_container

    @pytest.mark.asyncio
    async def test_recreates_container(self, sample_inspect_data):
        """Basic end-to-end verify: stop, remove, create, start are called in order."""
        provider, create_api, child_container = self._get_provider(sample_inspect_data)

        # Patch docker.APIClient to return our mock API
        with patch('docker.APIClient', return_value=create_api):
            result = await provider.recreate_container(CHILD_ID, "gluetun")

        # Assert: stop and remove were called
        child_container.stop.assert_called_once()
        child_container.remove.assert_called_once_with(force=True)

        # create_container should have been called with updated NetworkMode
        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("network_mode") == f"container:{NEW_PARENT_ID}"

        # start should have been called
        assert create_api.start.called

        assert result == "newchild456"

    @pytest.mark.asyncio
    async def test_recreate_updates_network_mode(self, sample_inspect_data):
        """Verify NetworkMode is updated from old parent ID to new parent ID."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch('docker.APIClient', return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("network_mode") == f"container:{NEW_PARENT_ID}"

    @pytest.mark.asyncio
    async def test_recreate_preserves_labels(self, sample_inspect_data):
        """Labels survive recreation."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch('docker.APIClient', return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        expected_labels = {"com.monitor.depends.on": "gluetun", "foo": "bar"}
        assert create_kwargs.get("labels") == expected_labels

    @pytest.mark.asyncio
    async def test_recreate_preserves_env_vars(self, sample_inspect_data):
        """Environment variables are preserved during recreation."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch('docker.APIClient', return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        expected_env = {"MY_ENV": "hello", "ANOTHER_VAR": "world"}
        assert create_kwargs.get("environment") == expected_env

    @pytest.mark.asyncio
    async def test_recreate_preserves_volumes(self, sample_inspect_data):
        """Volume bindings survive recreate."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch('docker.APIClient', return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("binds") == ["/host/data:/container/data:rw"]

    @pytest.mark.asyncio
    async def test_recreate_preserves_restart_policy(self, sample_inspect_data):
        """RestartPolicy is preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch('docker.APIClient', return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("restart_policy") == {
            "Name": "unless-stopped",
            "MaximumRetryCount": 0,
        }

    @pytest.mark.asyncio
    async def test_recreate_parent_not_found(self, sample_inspect_data):
        """When parent_name resolves to None, the recreate raises an error."""
        provider, _, _ = self._get_provider(sample_inspect_data)
        provider.get_container = AsyncMock(return_value=None)

        with pytest.raises(Exception, match="Parent container .* not found"):
            await provider.recreate_container(CHILD_ID, "gluetun")

    @pytest.mark.asyncio
    async def test_recreate_preserves_port_bindings(self, sample_inspect_data):
        """Port bindings survive recreation."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch('docker.APIClient', return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        host_config = create_kwargs.get("host_config", {})
        assert host_config.get("port_bindings") == {"80/tcp": [{"HostIp": "", "HostPort": "8080"}]}

    @pytest.mark.asyncio
    async def test_recreate_preserves_image_and_command(self, sample_inspect_data):
        """Image, command, entrypoint, and working_dir are preserved."""
        provider, create_api, _ = self._get_provider(sample_inspect_data)

        with patch('docker.APIClient', return_value=create_api):
            await provider.recreate_container(CHILD_ID, "gluetun")

        create_kwargs = create_api.create_container.call_args.kwargs
        # These are top-level kwargs, not under "config"
        assert create_kwargs.get("image") == "debian:latest"
        assert create_kwargs.get("command") == ["/bin/bash"]
        assert create_kwargs.get("entrypoint") == ["/entrypoint.sh"]
        assert create_kwargs.get("working_dir") == "/app"

    @pytest.mark.asyncio
    async def test_restart_container(self):
        """Basic restart_container works."""
        mock_docker_client = MagicMock()
        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container

        provider = DockerClientProvider(mock_docker_client)

        await provider.restart_container(CHILD_ID)

        mock_container.restart.assert_called_once()
