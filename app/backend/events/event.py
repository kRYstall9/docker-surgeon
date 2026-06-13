class Event:
    def __init__(self, type: str, id: str, name: str):
        self.type = type
        self.container_id = id
        self.container_name = name