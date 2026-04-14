from dataclasses import dataclass,field

@dataclass
class AgentConfig:
    host: str
    port: int | None = None
    token: str | None = None
    verify_ssl: bool = True
    
    @property
    def base_url(self) -> str:
        if self.host.startswith("http://") or self.host.startswith("https://"):
            protocol = ""
        else:
            protocol = "https://" if (self.port == 443) else "http://"
            
        default_port = 443 if self.host.startswith("https://") else 80
        resolved_port = self.port if self.port is not None else default_port
        
        return f"{protocol}{self.host}:{resolved_port}"

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentConfig':
        return cls(
            host=data.get("host", ""),
            port=data.get("port", None),
            token=data.get("token", ""),
            verify_ssl=data.get("verify_ssl", True)
        )
    
    
    