from dataclasses import dataclass


@dataclass(frozen=True)
class AgentGroup:
    responsibilities: tuple[str, ...]


@dataclass(frozen=True)
class Architecture:
    name: str
    agents: tuple[AgentGroup, ...]

    @property
    def agent_count(self) -> int:
        return len(self.agents)


ARCHITECTURE_1 = Architecture(
    name="1-agent",
    agents=(
        AgentGroup(("research", "fact_check", "critic", "writer")),
    ),
)

ARCHITECTURE_2 = Architecture(
    name="2-agent",
    agents=(
        AgentGroup(("research", "fact_check")),
        AgentGroup(("critic", "writer")),
    ),
)

ARCHITECTURE_3 = Architecture(
    name="3-agent",
    agents=(
        AgentGroup(("research",)),
        AgentGroup(("fact_check", "critic")),
        AgentGroup(("writer",)),
    ),
)

ARCHITECTURE_4 = Architecture(
    name="4-agent",
    agents=(
        AgentGroup(("research",)),
        AgentGroup(("fact_check",)),
        AgentGroup(("critic",)),
        AgentGroup(("writer",)),
    ),
)


ARCHITECTURES = (
    ARCHITECTURE_1,
    ARCHITECTURE_2,
    ARCHITECTURE_3,
    ARCHITECTURE_4,
)