from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import docker, asyncio, os
from app.agent.services import agent_service
from app.backend.core.state import logger

app = FastAPI()
security = HTTPBearer()
AGENT_TOKEN = os.getenv("AGENT_TOKEN", "")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != AGENT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

client = docker.from_env()

@app.get("/health", dependencies=[Depends(verify_token)])
def health_check():
    client.ping()
    return {"status": "ok", "host": os.getenv("AGENT_HOSTNAME", "unknown")}

@app.get("/containers", dependencies=[Depends(verify_token)])
def list_containers():
    return agent_service.getContainers(client)

@app.post("/containers/{name}/restart", dependencies=[Depends(verify_token)])
def restart_container(name: str):
    try:
        return agent_service.restartContainer(client, name)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/events/stream", dependencies=[Depends(verify_token)])
async def event_stream():
    from fastapi.responses import StreamingResponse
    return StreamingResponse(agent_service.getEvents(client, logger), media_type="text/event-stream")