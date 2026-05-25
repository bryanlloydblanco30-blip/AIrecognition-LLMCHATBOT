"""
Conversation Management for Multi-turn Context Handling
"""
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


FOLLOW_UP_KEYWORDS = [
    "more", "explain", "detail", "information", "why", "tell me",
    "description", "describe", "yes", "yeah", "sure", "ok", "okay",
    "tip", "tips", "suggest", "impact", "effect", "environment", "affect",
    "again", "remind", "repeat", "simplify", "simple", "easy",
    "just", "only", "simply", "basic", "short", "long", "decompose",
    "recycle", "dispose", "hazardous", "bin", "instructions", "how",
    "when", "where", "which", "what"
]

# Words that clearly signal the user wants a DIFFERENT item entirely
TOPIC_SWITCH_PHRASES = [
    "what about", "how about", "tell me about", "what is",
    "instead", "different item", "another item"
]

CONTEXT_CLEAR_WORDS = [
    "clear", "reset", "start over", "different item", "something else", "new topic"
]

# Greetings must NEVER be treated as follow-ups — always start fresh.
# Exported as a set so main.py can import and use it for the dataset-lookup guard.
GREETING_PHRASES = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "greetings", "sup", "what's up", "hi there", "hello there",
    "hiya", "yo", "hi!", "hello!", "hey!"
}

# NON_ITEM_MESSAGES: messages that must never trigger a dataset lookup.
# Includes greetings, acknowledgements, fillers, AND vague social messages
# like "how are you" and multi-word acknowledgements like "okay okay".
NON_ITEM_MESSAGES = {
    # Acknowledgements / reactions
    "thanks", "thank you", "thank", "ok", "okay", "cool", "nice", "great",
    "awesome", "wow", "lol", "haha", "bye", "goodbye", "later", "noted",
    "got it", "i see", "alright", "alright!", "sounds good",
    "okay okay", "ok ok", "okay!", "got it!", "i see", "i got it",
    "that's great", "that's cool", "that's nice", "nice one", "good to know",
    "makes sense", "understood", "sure", "sure thing", "of course",
    # Filler / hesitation sounds
    "uhmm", "uhm", "um", "uh", "hmm", "hm", "err", "uhh",
    "ahh", "ah", "oh", "ohh", "ooh", "oof", "huh", "umm",
    "emmm", "emm", "em", "mhm", "aha", "ahhh",
    # Social / small-talk — bot is not a general chatbot
    "how are you", "how are you?", "how r u", "how r you",
    "are you okay", "are you good", "what's up", "whats up",
    "how's it going", "hows it going", "how do you do",
    "you good", "you okay",
} | GREETING_PHRASES  # union — greetings are also non-item messages

# Vague topic phrases that should redirect to "ask for a specific item"
# rather than triggering a generic essay from the LLM.
VAGUE_TOPIC_PHRASES = {
    "let's focus on recycling", "lets focus on recycling",
    "let's talk about recycling", "lets talk about recycling",
    "let's talk about waste", "lets talk about waste",
    "let's talk about disposal", "lets talk about disposal",
    "recycling", "disposal", "waste management", "composting",
    "let's discuss", "lets discuss",
}

# Generic knowledge questions — answer briefly then redirect to item lookup.
# These should NOT do a dataset lookup (there's no item to match).
GENERIC_KNOWLEDGE_PHRASES = [
    "what is disposing", "what is recycling", "what is composting",
    "what is waste", "what is landfill", "what is incineration",
    "what are the types of trash", "what are the types of waste",
    "types of trash", "types of waste", "types of garbage",
    "what is proper disposal", "what is waste management",
    "define recycling", "define disposal", "define waste",
]


class ConversationContext:
    """Manages conversation state and context"""

    def __init__(self):
        self.current_item: Optional[str] = None
        self.conversation_history: List[Dict] = []
        self.items_discussed: List[str] = []
        self.last_response: Optional[str] = None
        self.question_count = 0
        self.pinned_item_row = None  # set after correction to anchor the resolved row

    def reset(self):
        """Fully wipe all state — call this instead of __init__()"""
        self.current_item = None
        self.conversation_history = []
        self.items_discussed = []
        self.last_response = None
        self.question_count = 0
        self.pinned_item_row = None

    def update_current_item(self, item: str):
        if item and item not in self.items_discussed:
            self.items_discussed.append(item)
        self.current_item = item

    def add_exchange(self, user_msg: str, bot_msg: str):
        self.conversation_history.append({
            "user": user_msg,
            "bot": bot_msg,
            "item": self.current_item
        })
        self.last_response = bot_msg
        self.question_count += 1

    def get_context_summary(self) -> str:
        parts = []
        if self.current_item:
            parts.append(f"Current item: {self.current_item}")
        if self.question_count > 0:
            parts.append(f"Questions asked: {self.question_count}")
        if self.items_discussed:
            parts.append(f"Items discussed: {', '.join(self.items_discussed)}")
        return " | ".join(parts)


def is_vague_topic(msg: str) -> bool:
    """Return True if the message is a vague topic framing with no specific item."""
    s = _strip_msg_static(msg)
    return s in VAGUE_TOPIC_PHRASES


def is_generic_knowledge_question(msg: str) -> bool:
    """Return True if the message is a generic 'what is X' with no specific item."""
    s = msg.lower().strip()
    return any(s == phrase or s.startswith(phrase) for phrase in GENERIC_KNOWLEDGE_PHRASES)


def _strip_msg_static(msg: str) -> str:
    return msg.lower().strip().strip("!?.,:;")


def _strip_msg(msg: str) -> str:
    """Lowercase, strip whitespace and common punctuation."""
    return msg.lower().strip().strip("!?.,:;")


def detect_question_type(
    current_message: str,
    history: List[Message],
    context: ConversationContext
) -> Tuple[str, bool]:
    msg_lower = current_message.lower().strip()
    words = msg_lower.split()
    msg_stripped = _strip_msg(current_message)

    # --- Greeting / non-item check FIRST ---
    # These are NEVER follow-ups, even if we have a current_item.
    if msg_stripped in NON_ITEM_MESSAGES:
        return "new_query", False

    # No item tracked yet — definitely a new query
    if not context.current_item:
        return "new_query", False

    # Explicit reset request
    if any(phrase in msg_lower for phrase in CONTEXT_CLEAR_WORDS):
        return "context_clear", False

    # Simplified description request — treat as clarification on current item
    simplified_keywords = [
        "just want", "only want", "simple description",
        "short description", "brief description"
    ]
    if any(kw in msg_lower for kw in simplified_keywords):
        return "clarification", True

    # Topic switch — user is explicitly asking about something else
    if any(phrase in msg_lower for phrase in TOPIC_SWITCH_PHRASES):
        refers_to_current = any(w in words for w in ["it", "this", "that", "its"])
        if not refers_to_current:
            return "topic_switch", False

    # Follow-up keyword present → follow_up
    if any(kw in msg_lower for kw in FOLLOW_UP_KEYWORDS):
        return "follow_up", True

    # Short message (≤ 3 words, not a greeting) with active context → follow_up
    if len(words) <= 3:
        # Extra safety: single common words that aren't about waste → new_query
        non_waste_singles = {
            "thanks", "thank", "ok", "okay", "cool", "nice", "great",
            "awesome", "wow", "lol", "haha", "bye", "goodbye", "later"
        }
        if msg_stripped in non_waste_singles:
            return "new_query", False
        return "follow_up", True

    # Long message with no follow-up signals → new query
    return "new_query", False


def extract_item_from_history(history: List[Message], steps_back: int = 1) -> Optional[str]:
    """Kept for compatibility. Prefer context.current_item."""
    if not history:
        return None
    user_messages = [msg for msg in reversed(history) if msg.role == "user"]
    for user_msg in user_messages:
        msg_lower = user_msg.content.lower()
        if any(kw in msg_lower for kw in ["more", "yes", "no", "explain", "tip"]):
            continue
        if len(msg_lower.split()) <= 2:
            continue
        return user_msg.content
    if user_messages:
        return user_messages[0].content
    return None


def build_context_aware_prompt(
    current_message: str,
    question_type: str,
    previous_response: Optional[str],
    item_context: Optional[str],
    conversation_context: ConversationContext
) -> str:
    prompt_parts = []

    if question_type == "follow_up":
        if previous_response and conversation_context.current_item:
            prompt_parts.append(
                f"The user is asking a follow-up about {conversation_context.current_item}."
            )
            prompt_parts.append(f"Previous response was:\n{previous_response}")
            prompt_parts.append(f"Now they're asking: {current_message}")
            prompt_parts.append("Provide a focused follow-up answer. Do not repeat previous info.")
    elif question_type == "clarification":
        if previous_response:
            prompt_parts.append("The user wants clarification on a previous point.")
            prompt_parts.append(f"Previous response: {previous_response}")
            prompt_parts.append(f"Clarification request: {current_message}")
            prompt_parts.append("Explain more clearly and simply.")
    elif question_type == "topic_switch":
        prompt_parts.append(
            f"The user is switching topics. Previous item: {conversation_context.current_item}."
        )
        prompt_parts.append(f"New question: {current_message}")
        prompt_parts.append("Treat this as a fresh query.")
    else:
        prompt_parts.append(f"User question: {current_message}")

    if item_context:
        prompt_parts.append(f"\nDataset context:\n{item_context}")

    return "\n\n".join(prompt_parts)


def should_use_previous_context(
    question_type: str,
    current_item: Optional[str]
) -> bool:
    """Return True if the search should use the tracked item name instead of the raw message."""
    if question_type in ["follow_up", "clarification"]:
        return current_item is not None
    return False