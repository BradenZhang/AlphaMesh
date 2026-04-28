from abc import ABC, abstractmethod

from app.schemas.research import ResearchReport


class ResearchAgent(ABC):
    @abstractmethod
    def analyze(self, symbol: str) -> ResearchReport:
        raise NotImplementedError
