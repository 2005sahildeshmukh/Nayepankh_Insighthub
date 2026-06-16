import json
from typing import Dict, Any

class PromptTemplates:
    SYSTEM_INSTRUCTION = (
        "You are an expert Decision Intelligence Assistant specializing in helping NGOs optimize their operations.\n"
        "You must follow these strict rules at all times:\n"
        "1. GROUNDING: Use ONLY the provided dataset context. Never invent statistics, counts, percentages, people, organizations, or events.\n"
        "2. NO CAUSATION CLAIMS: Do not claim causation. Express relationships as associations or correlations.\n"
        "3. LIMITATIONS: Explicitly state the limits of the analysis (e.g. data completeness, sample size, observational nature).\n"
        "4. NGO FOCUS: Keep recommendations practical and tailored to NGO operations.\n"
        "5. RESPONSE FORMAT: Return valid JSON matching the requested schema. Do not include markdown code fences (like ```json) in your actual payload if requested to output raw JSON, or ensure valid parsing."
    )

    COPILOT_PROMPT = (
        "Based on the following dataset context, answer this question: '{question}'\n\n"
        "Context:\n{context_json}\n\n"
        "Provide your response in this exact JSON structure (valid JSON only):\n"
        "{{\n"
        "  \"answer\": \"Plain-language response addressing the user's question directly\",\n"
        "  \"evidence\": [\n"
        "    {{\"label\": \"Metric Label (e.g. Total Records)\", \"value\": \"exact metric value from context (e.g. 450)\"}}\n"
        "  ],\n"
        "  \"recommended_actions\": [\n"
        "    \"Specific practical recommendation for the NGO\"\n"
        "  ],\n"
        "  \"limitations\": [\n"
        "    \"Specific limit or caution regarding this analysis\"\n"
        "  ]\n"
        "}}\n"
        "Note: Do not make up any numbers. Every number mentioned in the answer must appear in the evidence list."
    )

    DECISIONS_PROMPT = (
        "Based on the following dataset context, generate exactly three strategic decision recommendations for the NGO.\n\n"
        "Context:\n{context_json}\n\n"
        "Provide your response in this exact JSON structure (valid JSON only):\n"
        "{{\n"
        "  \"decisions\": [\n"
        "    {{\n"
        "      \"priority\": \"high\",\n"
        "      \"title\": \"Title of the decision card\",\n"
        "      \"recommended_action\": \"Specific action the NGO should execute\",\n"
        "      \"evidence\": [\"Observed association or statistic from the context supporting this action\"],\n"
        "      \"expected_impact\": \"What positive change is expected\",\n"
        "      \"confidence\": \"medium\",\n"
        "      \"limitations\": [\"Cautionary note regarding this specific recommendation\"]\n"
        "    }}\n"
        "  ]\n"
        "}}\n"
        "Note: Generate EXACTLY three decision cards. Do not generate more or less. Use priority values: high, medium, low. Use confidence values: high, medium, low."
    )

    REPORT_PROMPT = (
        "Based on the following dataset context, provide executive summary, management interpretations, and limitations text for the sections of a comprehensive PDF report.\n\n"
        "Context:\n{context_json}\n\n"
        "Provide your response in this exact JSON structure (valid JSON only):\n"
        "{{\n"
        "  \"title\": \"NayePankh Dataset Intelligence Report\",\n"
        "  \"generated_at\": \"{generated_at}\",\n"
        "  \"sections\": [\n"
        "    {{\n"
        "      \"heading\": \"Executive Summary\",\n"
        "      \"content\": \"Generative overview summarizing the database context, dataset quality, major findings, and strategic outlook for the NGO.\"\n"
        "    }},\n"
        "    {{\n"
        "      \"heading\": \"Management Interpretation\",\n"
        "      \"content\": \"Deep-dive interpretation explaining how management should interpret these correlations, distributions, or ML models (if any).\"\n"
        "    }},\n"
        "    {{\n"
        "      \"heading\": \"Strategic Recommended Decisions\",\n"
        "      \"content\": \"Generative context explaining the recommended strategic actions.\"\n"
        "    }}\n"
        "  ],\n"
        "  \"limitations\": [\n"
        "    \"Specific data completeness or ML limitation text\"\n"
        "  ]\n"
        "}}"
    )
