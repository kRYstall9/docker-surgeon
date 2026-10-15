import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import docker

# Import after docker is available at top level
from app.backend.providers import DockerClientProvider

NEW_PARENT_ID = "newparent99999999999999999999999999999999999999999999999999999999999"
CHILD_ID = "child123"


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
