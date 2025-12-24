from typing import Dict, Any, Optional

from logger import Logger


class PromptManagerBase:
    def __init__(self, logging_level: str = "info"):
        self.logger = Logger(self.__class__.__name__, logging_level=logging_level)
        self.schema: Optional[Dict[str, Any]] = None
        self.task: Optional[str] = None
