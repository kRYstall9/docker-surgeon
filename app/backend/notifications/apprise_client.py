from threading import Lock
from apprise import Apprise

class AppriseClient():
    _instance = None
    _lock = Lock()

    def __new__(cls, urls: list[str]):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.apprise_client = Apprise()
            
                for url in  urls:
                    cls._instance.apprise_client.add(url)
                
            return cls._instance
    
    def send(self, title:str, body:str):
        self.apprise_client.notify(body=body, title=title)