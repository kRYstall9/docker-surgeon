import httpx, json, asyncio, logging
from typing import Any


class AgentClient:
    def __init__(self, base_url: str, token: str, logger: logging.Logger):
        self.base_url = base_url
        self.token = token
        self.verify_ssl: bool = True
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.logger = logger
        self.http_client = httpx.AsyncClient(verify= self.verify_ssl, headers=self.headers, timeout=30)

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.http_client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error {e.response.status_code} for {method} {url}: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"Error during {method} {url}: {str(e)}")
            raise

    async def health_check(self) -> dict:
        return await self._request("GET", "/health")

    async def list_containers(self) -> list[Any]:
        return await self._request("GET", "/containers")

    async def restart_container(self, name: str | None = None, id: str | None = None) -> dict:
        return await self._request("POST", f"/containers/restart", params={"name": name, "id": id} if name or id else {})

    async def get_container(self, name: str | None = None, id: str | None = None):
        return await self._request("GET", "/containers/search", params={"name": name, "id": id} if name or id else {})

    async def get_container_logs(self, name: str | None = None, id: str | None = None, tail: int = 10) -> str:
        return await self._request("GET", "/containers/logs", params={"name": name, "id": id, "tail": tail} if name or id else {})
    
    async def stream_events(self):
        url = f"{self.base_url}/events/stream"
        delay = 2
        max_delay = 60
        
        while True:
            try:
                try:
                    async with self.http_client.stream("GET", url, headers=self.headers) as response:
                        response.raise_for_status()
                        self.logger.info(f"[Agent {self.base_url}] Connected to event stream")
                        delay = 2  # Reset delay on successful connection
                        async for line in response.aiter_lines():
                            self.logger.debug(f"Received line from event stream: {line}")
                            if line and len(line) > 0:
                                try:
                                    event = json.loads(line[5:].strip())  # Remove "data: " prefix
                                    yield event
                                except json.JSONDecodeError as e:
                                    self.logger.error(f"Failed to decode event: {str(e)}")
                except httpx.HTTPStatusError as e:
                    self.logger.error(f"HTTP error {e.response.status_code} for streaming events: {e.response.text}")
                    raise
                except Exception as e:
                    self.logger.error(f"Error during streaming events: {str(e)}")
                    raise
            except Exception:
                self.logger.info(f"[Agent {self.base_url}] Stream disconnected. Reconnecting to event stream in {delay} seconds...")
                await asyncio.sleep(delay)
                delay = min(delay * 2, max_delay)