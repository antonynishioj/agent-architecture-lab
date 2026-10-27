from dataclasses import dataclass


ROLES = ("research", "fact_check", "critic", "writer")


@dataclass(frozen=True)
class AgentGroup:
    responsibilities: tuple[str, ...]


@dataclass(frozen=True)
class Architecture:
    """
    An architecture is only a grouping of the four roles into agents.

    Every architecture covers all four roles in the same order, so the
    number of agents is the only thing that changes between them.
    """

    name: str
    agents: tuple[AgentGroup, ...]
    description: str = ""

    @property
    def agent_count(self) -> int:
        return len(self.agents)

    @property
    def roles(self) -> tuple[str, ...]:
        return tuple(
            role
            for agent in self.agents
            for role in agent.responsibilities
        )


ARCHITECTURE_1 = Architecture(
    name="1-agent",
    agents=(
        AgentGroup(("research", "fact_check", "critic", "writer")),
    ),
    description=(
        "One agent does research, fact-checking, critique, "
        "and writing in a single call."
    ),
)

ARCHITECTURE_2 = Architecture(
    name="2-agent",
    agents=(
        AgentGroup(("research", "fact_check")),
        AgentGroup(("critic", "writer")),
    ),
    description=(
        "Research + fact-checking, then critique + writing."
    ),
)

ARCHITECTURE_3 = Architecture(
    name="3-agent",
    agents=(
        AgentGroup(("research",)),
        AgentGroup(("fact_check", "critic")),
        AgentGroup(("writer",)),
    ),
    description=(
        "Research, then fact-checking + critique, then writing."
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
    description=(
        "A separate agent for each of research, fact-checking, "
        "critique, and writing."
    ),
)


ARCHITECTURES = (
    ARCHITECTURE_1,
    ARCHITECTURE_2,
    ARCHITECTURE_3,
    ARCHITECTURE_4,
)

ARCHITECTURES_BY_NAME = {
    architecture.name: architecture
    for architecture in ARCHITECTURES
}

# Sanity check: every architecture must cover every role exactly once.
for _architecture in ARCHITECTURES:
    assert _architecture.roles == ROLES, _architecture.name
