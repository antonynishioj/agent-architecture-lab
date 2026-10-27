import json


def parse_json_object(raw_text: str) -> dict:
    """
    Parse a JSON object from an LLM response.

    Structured output normally returns clean JSON, but this also
    tolerates Markdown fences or text around the object.
    """

    text = raw_text.strip()

    if text.startswith("```"):
        text = text.strip("`")

        if text.startswith("json"):
            text = text[4:]

        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                f"Judge did not return valid JSON:\n{raw_text[:500]}"
            )

        return json.loads(text[start : end + 1])
