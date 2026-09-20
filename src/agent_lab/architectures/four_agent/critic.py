from agent_lab.llm.base import LLM, LLMResponse


class FourAgentCritic:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(
        self,
        question: str,
        fact_check_report: str,
    ) -> LLMResponse:

        prompt = f"""
You are the Critic Agent in a four-agent research system.

Your only responsibility is critical analysis.

Your responsibilities are:

1. Examine the fact-checking report.
2. Identify weaknesses in the reasoning.
3. Identify missing context that could affect the answer.
4. Identify contradictions or unsupported conclusions.
5. Determine which findings are sufficiently supported for
   the final answer.
6. Provide clear recommendations to the Writer Agent.

Do NOT perform a new web search.
Do NOT rewrite the final answer.
Do NOT focus primarily on writing style.

Original question:
{question}

Fact-checking report:
{fact_check_report}

Important evidence rule:

Base your critique only on the evidence represented in the
fact-checking report.

Do not introduce factual information from your pretrained knowledge
to correct, expand, or supplement the report.

You may identify reasonable conclusions that directly follow from
the evidence.

Do not introduce external facts, examples, technical concepts,
statistics, mechanisms, or terminology merely because they are
generally known.

If the available evidence is insufficient, conflicting, or uncertain,
explicitly preserve that limitation.

Your recommendations must distinguish between:
- claims supported by the evidence,
- claims that require qualification,
- claims that should be removed,
- and information that remains uncertain.

Return a structured critique for the Writer Agent.
"""

        return self.llm.generate(prompt)