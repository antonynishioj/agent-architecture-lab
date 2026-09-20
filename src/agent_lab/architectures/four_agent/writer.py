from agent_lab.llm.base import LLM, LLMResponse


class FourAgentWriter:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(
        self,
        question: str,
        fact_check_report: str,
        critique: str,
    ) -> LLMResponse:

        prompt = f"""
You are the Writer Agent in a four-agent research system.

Your only responsibility is writing the final answer.

Use the fact-checking report and critic's recommendations
to produce the best supported answer to the original question.

Your responsibilities are:

1. Answer the original question directly.
2. Use information supported by the research process.
3. Respect the fact-checking findings.
4. Incorporate relevant recommendations from the critic.
5. Present the answer clearly and coherently.
6. Avoid unsupported claims or invented information.

Do NOT perform new research.
Do NOT perform additional research.
Do NOT expose the internal multi-agent workflow to the user.

Original question:
{question}

Fact-checking report:
{fact_check_report}

Critic's recommendations:
{critique}

Important evidence rule:

Use the fact-checking report and critic's recommendations as the
available evidence.

Do not introduce factual information from your pretrained knowledge
that is not supported by the research process.

You may make reasonable conclusions or inferences that directly
follow from the supported evidence.

If the available evidence does not support a factual claim, do not
fill the gap using general knowledge.

Instead, omit the claim or clearly communicate the uncertainty
or limitation.

Do not add external examples, technical concepts, statistics,
mechanisms, or terminology merely because they are generally known.

If the research contains conflicting evidence, preserve the
distinction and uncertainty in the final answer.

Return only the final user-facing answer.
"""

        return self.llm.generate(prompt)