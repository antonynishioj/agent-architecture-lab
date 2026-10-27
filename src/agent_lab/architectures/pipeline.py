import hashlib
from collections.abc import Callable

from pydantic import BaseModel

from agent_lab.architectures.definitions import AgentGroup, Architecture
from agent_lab.architectures.roles import EVIDENCE_RULE, ROLE_SPECS
from agent_lab.llm.base import GenerationConfig, LLM
from agent_lab.research.result import ResearchBundle


# Roles that need the raw sources. Research extracts from them and
# fact-checking verifies against them. Critique and writing work
# from the notes handed over by earlier agents.
SOURCE_ROLES = {"research", "fact_check"}


class AgentStep(BaseModel):
    agent_index: int
    roles: list[str]
    output: str
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    latency_ms: float
    saw_sources: bool


StepCallback = Callable[[AgentStep], None]


def _role_titles(group: AgentGroup) -> str:
    return " + ".join(
        ROLE_SPECS[role].title
        for role in group.responsibilities
    )


class PipelineArchitecture:
    """
    Runs any architecture definition as a sequential pipeline.

    Agent k receives:
    - the question,
    - the sources, if it does research or fact-checking,
    - the notes from every earlier agent (a shared blackboard),
    - the shared role instructions for each of its roles.
    """

    def __init__(
        self,
        definition: Architecture,
        llm: LLM,
        config: GenerationConfig,
    ):
        self.definition = definition
        self.llm = llm
        self.config = config

    def build_prompt(
        self,
        agent_index: int,
        question: str,
        research: ResearchBundle,
        previous: list[AgentStep],
    ) -> str:
        agents = self.definition.agents
        group = agents[agent_index]
        total = len(agents)
        is_final = "writer" in group.responsibilities

        sections: list[str] = []

        if total == 1:
            sections.append(
                "You are a research assistant working alone. You are "
                "responsible for every stage of answering the question."
            )
        else:
            team = "\n".join(
                f"- Agent {index + 1}: {_role_titles(agent)}"
                + (" (you)" if index == agent_index else "")
                for index, agent in enumerate(agents)
            )

            sections.append(
                f"You are Agent {agent_index + 1} of {total} in a research "
                f"team that answers questions using only provided "
                f"evidence. The team works in this order:\n{team}\n\n"
                f"Do only your own responsibilities. Other agents handle "
                f"the rest."
            )

        duties = []

        for role in group.responsibilities:
            spec = ROLE_SPECS[role]
            items = "\n".join(f"  - {duty}" for duty in spec.duties)
            duties.append(f"{spec.title}:\n{items}")

        sections.append(
            "Your responsibilities, in this order:\n\n"
            + "\n\n".join(duties)
        )

        sections.append(EVIDENCE_RULE)

        sections.append(f"Question:\n{question}")

        if SOURCE_ROLES.intersection(group.responsibilities):
            sections.append(
                f"Sources:\n{research.format_sources()}"
            )

        if previous:
            notes = "\n\n".join(
                f"=== Notes from Agent {step.agent_index + 1} "
                f"({_role_titles(AgentGroup(tuple(step.roles)))}) ===\n"
                f"{step.output}"
                for step in previous
            )

            sections.append(f"Notes from earlier agents:\n\n{notes}")

        if is_final:
            sections.append(
                "Output: return ONLY the final answer for the user, "
                "with [S#] citations. Do not include your intermediate "
                "work."
            )
        else:
            next_group = agents[agent_index + 1]
            handoff = "\n".join(
                f"- {ROLE_SPECS[role].handoff}"
                for role in group.responsibilities
            )

            sections.append(
                f"Output: notes for Agent {agent_index + 2} "
                f"({_role_titles(next_group)}). Do NOT write the final "
                f"answer. Keep source IDs on every fact. Provide:\n"
                f"{handoff}"
            )

        return "\n\n".join(sections)

    def run(
        self,
        question: str,
        research: ResearchBundle,
        on_step: StepCallback | None = None,
    ) -> tuple[str, list[AgentStep]]:
        steps: list[AgentStep] = []

        for agent_index, group in enumerate(self.definition.agents):
            prompt = self.build_prompt(
                agent_index=agent_index,
                question=question,
                research=research,
                previous=steps,
            )

            response = self.llm.generate(prompt, self.config)

            step = AgentStep(
                agent_index=agent_index,
                roles=list(group.responsibilities),
                output=response.text.strip(),
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                thinking_tokens=response.thinking_tokens,
                latency_ms=response.latency_ms,
                saw_sources=bool(
                    SOURCE_ROLES.intersection(group.responsibilities)
                ),
            )

            steps.append(step)

            if on_step:
                on_step(step)

        return steps[-1].output, steps


def prompt_fingerprint() -> str:
    """
    Hash of every prompt-shaping constant, stored in the run manifest
    so readers can tell whether two runs used the same prompts.
    """

    import inspect

    from agent_lab.architectures import roles
    from agent_lab.evaluation import llm_judge, ranking_judge

    source = "".join(
        inspect.getsource(module)
        for module in (
            roles,
            llm_judge,
            ranking_judge,
        )
    ) + inspect.getsource(PipelineArchitecture.build_prompt)

    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
