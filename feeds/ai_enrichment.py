import json
from datetime import datetime, timezone

import ollama


ENRICHMENT_PROMPT = """You are a cybersecurity analyst reviewing threat intelligence articles.

Analyze the following article and provide a JSON response with these fields:
- summary: A concise 2-3 sentence summary focusing on the key threat
- threat_type: Primary threat category (e.g., "ransomware", "phishing", "vulnerability", "data breach", "malware", "apt", "ddos")
- severity: Risk level ("critical", "high", "medium", "low", "informational")
- affected_tech: Comma-separated list of technologies, products, or vendors mentioned (e.g., "Windows, Apache, Chrome")

Article Title: {title}

Article Summary: {summary}

Respond ONLY with valid JSON. No markdown, no explanation, just the JSON object.
"""


def enrich_article(article, model="qwen2.5:7b"):
    """
    Use Ollama to analyze an article and extract threat intelligence metadata.

    Args:
        article: Article model instance
        model: Ollama model to use for analysis

    Returns:
        dict with ai_summary, threat_type, severity, affected_tech
    """
    prompt = ENRICHMENT_PROMPT.format(
        title=article.title,
        summary=article.summary[:2000] if article.summary else "No summary available"
    )

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a cybersecurity analyst. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.3,
            }
        )

        content = response["message"]["content"].strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)

        return {
            "ai_summary": data.get("summary", ""),
            "threat_type": data.get("threat_type", ""),
            "severity": data.get("severity", ""),
            "affected_tech": data.get("affected_tech", ""),
            "enriched_at": datetime.now(timezone.utc),
        }

    except json.JSONDecodeError as e:
        # Fallback: try to parse partial response
        return {
            "ai_summary": f"Error parsing AI response: {e}",
            "threat_type": "unknown",
            "severity": "unknown",
            "affected_tech": "",
            "enriched_at": datetime.now(timezone.utc),
        }
    except Exception as e:
        return {
            "ai_summary": f"Error during enrichment: {e}",
            "threat_type": "error",
            "severity": "unknown",
            "affected_tech": "",
            "enriched_at": datetime.now(timezone.utc),
        }
