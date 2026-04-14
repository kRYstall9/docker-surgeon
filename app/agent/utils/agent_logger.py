import logging

class AgentLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[Agent {self.extra.get('agent_name', 'Unknown')}] {msg}", kwargs