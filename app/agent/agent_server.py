from __future__ import annotations
from typing import TYPE_CHECKING
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import docker
import uvicorn
from app.agent.services import AgentService
from logging import Logger
from docker.errors import NotFound, APIError

if TYPE_CHECKING:
    from app.backend.core import Config
    
class AgentServer:
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.app = FastAPI()
        self.docker_client = docker.from_env()
        self.service = AgentService(self.docker_client, self.logger)
        self._setup_routes()


    def _setup_routes(self):
        app = self.app
        config = self.config
        logger = self.logger

        security = HTTPBearer()

        def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
            if credentials.credentials != config.agent_token:
                raise HTTPException(status_code=403, detail="Invalid token")

        def get_docker_client(self):
            return self.docker_client

        @app.get("/health", dependencies=[Depends(verify_token)])
        def health_check(client=Depends(get_docker_client)):
            client.ping()
            return {"status": "ok", "host": config.agent_host}

        @app.get("/containers", dependencies=[Depends(verify_token)])
        def list_containers():
            return self.service.list_containers()

        @app.get('/containers/search', dependencies=[Depends(verify_token)])
        def get_container(id: str | None = None):
            if not id:
                raise HTTPException(status_code=400, detail="Either name or id must be provided")
            return self.service.get_container(id)

        @app.get('/containers/logs', dependencies=[Depends(verify_token)])
        def get_container_logs(id: str | None = None, tail: int = 10):
            if not id:
                raise HTTPException(status_code=400, detail="Either name or id must be provided")
            return self.service.get_logs(id, tail)

        @app.post("/containers/restart", dependencies=[Depends(verify_token)])
        def restart_container(id: str | None = None):
            if not id:
                raise HTTPException(status_code=400, detail="Either name or id must be provided")
            try:
                return self.service.restart_container(id)
            except NotFound:
                raise HTTPException(status_code=404, detail="Container not found")
            except APIError as e:
                raise HTTPException(status_code=500, detail=str(e))
            

        @app.get("/events/stream", dependencies=[Depends(verify_token)])
        async def event_stream():
            from fastapi.responses import StreamingResponse
            return StreamingResponse(
                self.service.stream_events(), 
                media_type="text/event-stream"
            )

    def run(self):
        if self.config.agent_host is None or self.config.agent_port is None:
            self.logger.warning("Unable to start Agent server. Agent Host and Agent Port not specified")
            return

        uvicorn.run(
            self.app,
            host= self.config.agent_host,
            port= self.config.agent_port
        )