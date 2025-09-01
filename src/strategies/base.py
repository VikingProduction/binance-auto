from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    async def generate_signal(self, df, symbol_info):
        pass
    
    @abstractmethod
    def get_required_indicators(self):
        pass
