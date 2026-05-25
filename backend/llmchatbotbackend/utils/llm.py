import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "ollama")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "http://localhost:11434/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-r1:1.5b")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

SYSTEM_PROMPT_BASE = (
    "You are an expert AI assistant specialized in waste management and recycling guidance. "
    "Your role is to help users understand how to properly dispose of, recycle, or handle various items. "
    "\n\n"
    "GUIDELINES:\n"
    "1. Provide clear, concise, actionable answers\n"
    "2. Always prioritize safety (especially for hazardous items)\n"
    "3. Use the dataset context provided to give accurate information\n"
    "4. When multiple disposal options exist, explain each clearly\n"
    "5. Include relevant warnings for hazardous materials\n"
    "6. Provide Philippine-specific guidance when relevant\n"
    "7. Be empathetic and encouraging about recycling/proper disposal\n"
    "\n"
    "RESPONSE FORMAT:\n"
    "- Start with the item name and category\n"
    "- State disposal/recycling method clearly\n"
    "- Include important warnings if applicable\n"
    "- Provide decomposition time if relevant\n"
    "- Add environmental or practical context when helpful\n"
)

# FIX: Separate system prompt for follow-ups — suppresses boilerplate that
# was being repeated on every single follow-up turn (bin colour, EPR mention,
# barangay guidelines, decomposition time).
FOLLOW_UP_SYSTEM_PROMPT = (
    "You are an expert AI assistant specialized in waste management and recycling guidance. "
    "You are answering a FOLLOW-UP question in an ongoing conversation.\n\n"
    "STRICT RULES FOR FOLLOW-UPS:\n"
    "1. Do NOT repeat the bin colour — the user already knows it.\n"
    "2. Do NOT mention the EPR / DENR program again unless directly asked.\n"
    "3. Do NOT repeat barangay guidelines — already covered.\n"
    "4. Do NOT repeat decomposition time unless the user specifically asked about it.\n"
    "5. Do NOT repeat the item category or recyclability status.\n"
    "6. Focus ONLY on answering the specific new question asked.\n"
    "7. Build on what was already said — add new value, never repeat.\n"
    "8. Keep the answer concise and directly useful.\n"
)


def get_chat_response(
    message: str,
    context: str = "",
    system_prompt: Optional[str] = None,
    conversation_context: str = ""
) -> str:
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT_BASE

    if context:
        system_prompt += f"\n\nDATASET CONTEXT:\n{context}"

    if conversation_context:
        system_prompt += f"\n\nCONVERSATION CONTEXT:\n{conversation_context}"

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            stream=False,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return f"Error: {str(e)}"


def get_follow_up_response(
    current_question: str,
    previous_response: str,
    item_name: str,
    context: str = ""
) -> str:
    follow_up_prompt = (
        f"The user previously asked about: {item_name}\n"
        f"My previous response was:\n{previous_response}\n\n"
        f"Now they're asking: {current_question}\n\n"
        f"Provide a focused follow-up answer that builds on the previous response. "
        f"Be specific and avoid repeating information unnecessarily."
    )

    # FIX: use FOLLOW_UP_SYSTEM_PROMPT to suppress boilerplate repetition
    system_prompt = (
        FOLLOW_UP_SYSTEM_PROMPT +
        f"\n\nYou are discussing: {item_name}.\n"
        f"Maintain consistency with your previous response while providing only new information."
    )

    if context:
        system_prompt += f"\n\nITEM CONTEXT (for reference only — do not repeat already-mentioned facts):\n{context}"

    return get_chat_response(follow_up_prompt, context="", system_prompt=system_prompt)


def get_clarification_response(
    previous_response: str,
    clarification_question: str,
    item_name: str
) -> str:
    clarification_prompt = (
        f"I previously said: {previous_response}\n\n"
        f"The user is asking for clarification: {clarification_question}\n\n"
        f"Please explain the concept more simply and clearly, "
        f"breaking it down into easy-to-understand steps."
    )

    system_prompt = (
        SYSTEM_PROMPT_BASE +
        f"\n\nYou are clarifying information about {item_name}.\n"
        f"Use simpler language and provide concrete examples.\n"
        f"Do NOT repeat the bin colour, EPR program, or barangay guidelines."
    )

    return get_chat_response(clarification_prompt, context="", system_prompt=system_prompt)


def get_simplified_description(
    previous_response: str,
    item_name: str,
    context: str = ""
) -> str:
    simplified_prompt = (
        f"The user asked about {item_name}.\n\n"
        f"Provide ONLY a simple, brief description in exactly 1-2 sentences.\n"
        f"Include: What it is and how to dispose of it.\n"
        f"Do NOT include: decomposition time, environmental impact, or extra details.\n\n"
        f"Format: '{item_name} is a [type]. [Disposal method].'"
    )

    system_prompt = (
        "You are a concise assistant that provides ONLY essential information.\n"
        "Your response must be exactly 1-2 sentences. Nothing more.\n"
        "Keep it simple and direct."
    )

    if context:
        context_trimmed = context[:300]
        if '.' in context_trimmed:
            context_trimmed = context_trimmed.rsplit('.', 1)[0] + '.'
        system_prompt += f"\n\nItem Information:\n{context_trimmed}"

    return get_chat_response(simplified_prompt, context="", system_prompt=system_prompt)