from abc import ABC, abstractmethod

from app.schemas.risk import RiskCheckRequest, RiskResult


class RiskGuardBase(ABC):
    @abstractmethod
    def check(self, request: RiskCheckRequest) -> RiskResult:
        raise NotImplementedError
