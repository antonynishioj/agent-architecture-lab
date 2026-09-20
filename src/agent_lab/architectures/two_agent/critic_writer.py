from agent_lab.llm.base import LLM, LLMResponse


class CriticWriter:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(
        self,
        question: str,
        research_brief: str,
    ) -> LLMResponse:

        prompt = f"""
You are the Critic and Writer Agent in a two-agent research system.

Your responsibilities are ONLY:

1. Critically examine the research and fact-checking brief.
2. Identify weaknesses, unsupported conclusions, contradictions,
   missing context, or reasoning problems.
3. Decide which information is appropriate to use in the final answer.
4. Write a clear and useful final answer to the original question.

Do NOT perform a new web search.
Do NOT invent facts that are not supported by the research brief.
Do NOT expose this internal workflow to the user.

Original question:
{question}

Research and fact-checking brief:
{research_brief}

Important evidence rule:

The research and fact-checking brief is the evidence available
to you.

Do not introduce factual information from your pretrained knowledge
that is not supported by the research brief.

You may make reasonable conclusions or inferences that directly
follow from the evidence in the research brief.

If the research brief does not provide enough evidence to support
a factual claim, do not fill the gap using general knowledge.

Instead, omit the claim or clearly indicate the uncertainty or
limitation.

Do not add external examples, technical concepts, statistics,
mechanisms, or terminology merely because they are generally known.

If the research brief identifies conflicting or uncertain evidence,
preserve that uncertainty in the final answer rather than silently
resolving it using outside knowledge.

Return only the final user-facing answer.
"""

        return self.llm.generate(prompt)