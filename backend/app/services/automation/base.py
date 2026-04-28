from abc import ABC, abstractmethod

from app.schemas.automation import AutomationRunRequest, AutomationRunResponse


class AutomationFlowBase(ABC):
    @abstractmethod
    def run(self, request: AutomationRunRequest) -> AutomationRunResponse:
        raise NotImplementedError
