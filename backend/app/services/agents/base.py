from abc import ABC, abstractmethod

from app.schemas.research import ResearchReport


class AgentRuntimeBase(ABC):
    @abstractmethod
    def run_research(self, symbol: str) -> ResearchReport:
        raise NotImplementedError
