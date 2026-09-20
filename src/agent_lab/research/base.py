from abc import ABC, abstractmethod

from agent_lab.research.result import ResearchBundle


class ResearchTool(ABC):

    @abstractmethod
    def search(self, query: str) -> ResearchBundle:
        pass