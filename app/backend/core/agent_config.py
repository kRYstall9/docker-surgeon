from dataclasses import dataclass,field

@dataclass
class AgentConfig:
    name: str | None = None
    host: str | None = None
    port: int | None = None
    token: str | None = field(default=None, repr=False)
    verify_ssl: bool = True
    
    @property
    def base_url(self) -> str:
        if self.host is None:
            return ""

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
            name=data.get("name", ""),
            host=data.get("host", ""),
            port=data.get("port", None),
            token=data.get("token", ""),
            verify_ssl=data.get("verify_ssl", True)
        )
    
    
    