class ContainerProxy:
    def __init__(self, data: dict):
        object.__setattr__(self, '_data', data)
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    def get(self, key, default=None):
        return self._data.get(key, default)