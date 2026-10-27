import re

from agent_lab.evaluation.result import DeterministicMetrics


BRACKET = re.compile(r"\[([^\[\]]{1,40})\]")
SOURCE_ID = re.compile(r"S\s*(\d+)", re.IGNORECASE)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _citations(text: str) -> list[int]:
    numbers = []

    for group in BRACKET.findall(text):
        numbers.extend(int(number) for number in SOURCE_ID.findall(group))

    return numbers


def compute_metrics(answer: str, source_count: int) -> DeterministicMetrics:
    """
    Checks that need no LLM: citation validity and coverage, and length.

    A citation is invalid if it points to a source number that does
    not exist, which is a cheap, objective hallucination signal.
    """

    citations = _citations(answer)
    invalid = [
        number
        for number in citations
        if number < 1 or number > source_count
    ]

    sentences = [
        sentence
        for sentence in SENTENCE_SPLIT.split(answer)
        if len(sentence.split()) >= 6
    ]

    cited_sentences = [
        sentence
        for sentence in sentences
        if _citations(sentence)
    ]

    return DeterministicMetrics(
        word_count=len(answer.split()),
        citation_count=len(citations),
        distinct_sources_cited=len(
            {number for number in citations if number not in invalid}
        ),
        invalid_citations=len(invalid),
        citation_validity=(
            (len(citations) - len(invalid)) / len(citations)
            if citations
            else 0.0
        ),
        sentence_citation_coverage=(
            len(cited_sentences) / len(sentences)
            if sentences
            else 0.0
        ),
    )
