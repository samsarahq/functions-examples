import openai
import json
import httpx
import urllib3
from dataclasses import dataclass
from samsarafnsecrets import get_secrets

# Disable SSL warnings when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create HTTP client with disabled SSL verification
http_client = httpx.Client(verify=False)

client = openai.OpenAI(
    api_key=get_secrets(force_refresh=True)["OPENAI_KEY"], http_client=http_client
)


prompt = """
Analyze this image for Personal Protective Equipment (PPE) compliance. Look for people and check if they are wearing required safety equipment including:
- Hard hats/helmets
- Safety vests/high-visibility clothing
- Safety glasses/goggles
- Gloves (if handling materials)
- Safety boots (if visible)

If no people are visible return false for has_detected_people. 
State a brief explanation of findings during the analysis.

Respond with a JSON object containing:
{
    "has_detected_people": boolean,
    "is_any_ppe_missing": boolean,
    "summary": string
}

Example 1: 
{
    "has_detected_people": true,
    "is_any_ppe_missing": false,
    "summary": "Four people are visible, but all have hard hats, safety vests, safety glasses, gloves, and safety boots."
}

Example 2:
{
    "has_detected_people": true,
    "is_any_ppe_missing": true,
    "summary": "One person is visible, they are not wearing a hard hat."
}
"""


@dataclass
class DetectionResult:
    has_detected_people: bool
    is_any_ppe_missing: bool
    summary: str


fallback_result: DetectionResult = DetectionResult(
    has_detected_people=False,
    is_any_ppe_missing=False,
    summary="",
)


def detect_missing_ppe(image_base64: str) -> DetectionResult:
    response = client.chat.completions.create(
        model="o4-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        max_completion_tokens=10_000,
    )

    result_text = response.choices[0].message.content

    try:
        # Find JSON in the response (it might be wrapped in markdown code blocks)
        json_start = result_text.find("{")
        json_end = result_text.rfind("}") + 1
        return DetectionResult(**json.loads(result_text[json_start:json_end]))
    except Exception:
        print(f"Failed to parse detection message: {result_text}, using fallback")
        return fallback_result
