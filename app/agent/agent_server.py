from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import docker, json
from app.backend.core.state import logger, config
from app.agent.services import agent_service
from typing import Any

app = FastAPI()
security = HTTPBearer()
docker_client_from_env = docker.from_env()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if (config.agent_token is None) or (credentials.credentials != config.agent_token):
        raise HTTPException(status_code=403, detail="Invalid token")

def get_docker_client():
    return docker_client_from_env

@app.get("/health", dependencies=[Depends(verify_token)])
def health_check(client=Depends(get_docker_client)):
    client.ping()
    return {"status": "ok", "host": config.agent_host}

@app.get("/containers", dependencies=[Depends(verify_token)])
def list_containers(client=Depends(get_docker_client)):
    return agent_service.getContainers(client)

@app.get('/containers/search', dependencies=[Depends(verify_token)])
def get_container(name: str | None = None, id: str | None = None, client=Depends(get_docker_client)):
    if not name and not id:
        raise HTTPException(status_code=400, detail="Either name or id must be provided")
    return agent_service.getContainer(client, name, id)

@app.get('/containers/logs', dependencies=[Depends(verify_token)])
def get_container_logs(name: str | None = None, id: str | None = None, tail: int = 10, client=Depends(get_docker_client)):
    if not name and not id:
        raise HTTPException(status_code=400, detail="Either name or id must be provided")
    return agent_service.getContainerLogs(client, name, id, tail)

@app.post("/containers/restart", dependencies=[Depends(verify_token)])
def restart_container(name: str | None = None, id: str | None = None, client=Depends(get_docker_client)):
    if not name and not id:
        raise HTTPException(status_code=400, detail="Either name or id must be provided")
    try:
        return agent_service.restartContainer(client, name, id)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/events/stream", dependencies=[Depends(verify_token)])
async def event_stream(client=Depends(get_docker_client)):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(agent_service.getEvents(client, logger), media_type="text/event-stream")