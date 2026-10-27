"""
The single source of truth for what each role does.

All four architectures build their prompts from these specs, so
the instructions for a role are identical whether that role is
done by a dedicated agent or shared with other roles. This removes
prompt wording as a confounding variable.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleSpec:
    key: str
    title: str
    duties: tuple[str, ...]
    handoff: str


RESEARCH = RoleSpec(
    key="research",
    title="Research",
    duties=(
        "Break the question into the sub-questions that must be answered.",
        "Extract every piece of information from the sources that is relevant to those sub-questions.",
        "Tag every extracted fact with its source ID, for example [S2].",
        "Record where sources disagree, where a source looks outdated, and which sub-questions the sources do not answer.",
    ),
    handoff="A structured research brief: sub-questions, extracted facts with source IDs, disagreements, and gaps.",
)

FACT_CHECK = RoleSpec(
    key="fact_check",
    title="Fact-checking",
    duties=(
        "Check each claim against the sources and label it SUPPORTED, PARTIALLY SUPPORTED, UNSUPPORTED, or CONTRADICTED, with source IDs.",
        "Flag conflicting sources and decide which is better supported (for example newer, more specific, or more authoritative), explaining why.",
        "Check whether the question itself contains a false or unsupported premise.",
        "List claims that must not appear in the final answer because the evidence does not support them.",
    ),
    handoff="A fact-check report: each claim with its verdict and source IDs, conflicts, premise problems, and claims to exclude.",
)

CRITIC = RoleSpec(
    key="critic",
    title="Critique",
    duties=(
        "Judge whether the verified evidence is enough to answer the question fully, partly, or not at all.",
        "Identify missing context, overgeneralisations, and conclusions stronger than the evidence allows.",
        "Identify which parts of the question are still unanswered and must be stated as limitations.",
        "Give concrete recommendations for the structure and content of the final answer.",
    ),
    handoff="A critique: answerability verdict, weaknesses, required caveats, and concrete recommendations for the final answer.",
)

WRITER = RoleSpec(
    key="writer",
    title="Writing",
    duties=(
        "Answer the question directly in the first sentence or two.",
        "Support every factual claim with source citations in the form [S1] or [S1][S3].",
        "Preserve real uncertainty and disagreement between sources instead of silently picking a side.",
        "If the sources do not support an answer, or the question has a false premise, say so clearly instead of guessing.",
        "Be concise and well structured. Do not mention agents, briefs, or the internal process.",
    ),
    handoff="The final answer for the user.",
)


ROLE_SPECS = {
    spec.key: spec
    for spec in (RESEARCH, FACT_CHECK, CRITIC, WRITER)
}


EVIDENCE_RULE = """\
Evidence rule (applies to every role):
- The numbered sources are the ONLY evidence. Do not add facts, examples,
  statistics, mechanisms, or terminology from your own background knowledge,
  even if you believe they are true.
- Reasonable conclusions that follow directly from the sources are allowed.
- If the sources do not support a claim, treat it as unsupported and say so.
- Sources can be wrong, outdated, irrelevant, or in conflict. Treat them critically."""
