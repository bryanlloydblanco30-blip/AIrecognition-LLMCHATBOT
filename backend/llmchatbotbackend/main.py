from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import io
import os
import sys
from difflib import SequenceMatcher

# Append current directory to path to locate local utils folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.vector_store import load_index, save_index, create_index, search_index
from utils.llm import get_chat_response, get_follow_up_response, get_clarification_response, get_simplified_description
from utils.data_lookup import (
    load_dataset,
    find_best_match,
    find_best_matches,
    build_item_response,
    no_match_response
)
from utils.conversation_manager import (
    Message,
    ConversationContext,
    NON_ITEM_MESSAGES,
    detect_question_type,
    extract_item_from_history,
    build_context_aware_prompt,
    should_use_previous_context,
    is_vague_topic,
    is_generic_knowledge_question,
)

app = FastAPI(title="EcoBot Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

index, documents = load_index()
dataset_df = load_dataset()

conversation_contexts = {}
MAX_SESSIONS = 1000

# Canned greeting reply — never pulled from the dataset
GREETING_REPLY = (
    "Hello! I'm here to help you with proper waste disposal and recycling guidance. "
    "What item would you like to know about?"
)

# Returned when the user asks a social question like "how are you"
SOCIAL_REPLY = (
    "I'm just a waste management assistant, so I don't have feelings — "
    "but I'm ready to help! What item would you like to know about?"
)

# Returned when the user sends a vague topic framing ("let's focus on recycling")
VAGUE_TOPIC_REPLY = (
    "Sure! To give you the most useful guidance, could you tell me "
    "which specific item you'd like to recycle or dispose of?"
)

# Returned for generic knowledge questions ("what are the types of trash")
GENERIC_KNOWLEDGE_REPLY = (
    "In the Philippines, waste is generally categorised as biodegradable "
    "(food scraps, yard waste), recyclable (plastic, paper, metal, glass), "
    "residual (non-recyclable dry waste), and special/hazardous waste "
    "(batteries, chemicals, e-waste). "
    "Which specific item would you like help disposing of?"
)

# Phrases that signal the user is explicitly correcting the tracked item.
# e.g. "we are talking about plastic bottles", "i meant old shirt"
CORRECTION_PHRASES = [
    "we are talking about",
    "i meant",
    "i mean",
    "no,",
    "actually",
    "i said",
    "not that",
    "i was asking about",
    "go back to",
    "back to",
]


def _strip_msg(msg: str) -> str:
    """Lowercase, strip whitespace and common punctuation."""
    return msg.lower().strip().strip("!?.,:;")


def _items_are_related(item_a: str, item_b: str) -> bool:
    """
    Return True if two item names are similar enough to be the same item.
    Prevents completely unrelated dataset matches from hijacking the context.
    """
    a = item_a.lower()
    b = item_b.lower()
    ratio = SequenceMatcher(None, a, b).ratio()
    shared_words = set(a.split()) & set(b.split())
    return ratio > 0.4 or len(shared_words) > 0


def _detect_correction(msg_lower: str) -> Optional[str]:
    """
    If the message contains a correction phrase, extract and return the
    corrected item name. Returns None if no correction detected.
    """
    for phrase in CORRECTION_PHRASES:
        if phrase in msg_lower:
            after = msg_lower.split(phrase, 1)[-1].strip().strip(".,!?").strip()
            if after:
                return after
    return None


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []
    session_id: Optional[str] = "default"


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "dataset_rows": len(dataset_df),
        "indexed_documents": len(documents)
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global index, documents

    content = await file.read()
    filename = file.filename

    new_docs = []
    if filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
        new_docs = df.astype(str).apply(lambda x: ' | '.join(x), axis=1).tolist()
    elif filename.endswith('.txt'):
        new_docs = content.decode('utf-8').split('\n')
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    new_docs = [d.strip() for d in new_docs if d.strip()]
    documents.extend(new_docs)
    index = create_index(documents)
    save_index(index, documents)

    return {"message": f"Successfully indexed {len(new_docs)} entries from {filename}"}


@app.post("/chat")
async def chat(request: ChatRequest):
    global index, documents, dataset_df

    session_id = request.session_id or "default"

    # Cap sessions to prevent memory leak
    if session_id not in conversation_contexts:
        if len(conversation_contexts) >= MAX_SESSIONS:
            oldest_key = next(iter(conversation_contexts))
            del conversation_contexts[oldest_key]
        conversation_contexts[session_id] = ConversationContext()

    context = conversation_contexts[session_id]
    msg_lower = request.message.lower()
    msg_stripped = _strip_msg(request.message)

    # ----------------------------------------------------------------
    # GUARD 1: Greetings, fillers, acknowledgements, "okay okay" etc.
    # ----------------------------------------------------------------
    if msg_stripped in NON_ITEM_MESSAGES:
        context.add_exchange(request.message, GREETING_REPLY)
        return {
            "response": GREETING_REPLY,
            "match_confidence": "none",
            "item": None,
            "question_type": "greeting"
        }

    # ----------------------------------------------------------------
    # GUARD 2: Social questions ("how are you") — bot is not a chatbot.
    # ----------------------------------------------------------------
    SOCIAL_QUESTIONS = {
        "how are you", "how are you?", "how r u", "how r you",
        "are you okay", "are you good", "hows it going", "how's it going",
        "how do you do", "you good", "you okay",
    }
    if msg_stripped in SOCIAL_QUESTIONS:
        context.add_exchange(request.message, SOCIAL_REPLY)
        return {
            "response": SOCIAL_REPLY,
            "match_confidence": "none",
            "item": None,
            "question_type": "social"
        }

    # ----------------------------------------------------------------
    # GUARD 3: Vague topic framing ("let's focus on recycling").
    # Ask for a specific item instead of dumping a generic essay.
    # ----------------------------------------------------------------
    if is_vague_topic(request.message):
        context.add_exchange(request.message, VAGUE_TOPIC_REPLY)
        return {
            "response": VAGUE_TOPIC_REPLY,
            "match_confidence": "none",
            "item": None,
            "question_type": "vague_topic"
        }

    # ----------------------------------------------------------------
    # GUARD 4: Generic knowledge questions ("what are the types of trash").
    # Give a brief canned answer and redirect to item lookup.
    # ----------------------------------------------------------------
    if is_generic_knowledge_question(request.message):
        context.add_exchange(request.message, GENERIC_KNOWLEDGE_REPLY)
        return {
            "response": GENERIC_KNOWLEDGE_REPLY,
            "match_confidence": "none",
            "item": None,
            "question_type": "generic_knowledge"
        }

    # ----------------------------------------------------------------
    # FIX 2: Detect explicit user corrections BEFORE question-type
    # detection so we can force-update the tracked item immediately.
    # e.g. "we are talking about plastic bottles" / "i meant old shirt"
    # ----------------------------------------------------------------
    corrected_item = _detect_correction(msg_lower)
    if corrected_item:
        context.update_current_item(corrected_item)
        search_query = corrected_item
        question_type = "new_query"
        is_follow_up = False
        context.pinned_item_row = None
    else:
        question_type, is_follow_up = detect_question_type(
            request.message,
            request.history,
            context
        )
        search_query = request.message  # default; refined below

    # Handle context clearing — reset before any logic runs
    if question_type == "context_clear":
        context.reset()
        question_type = "new_query"

    # Simplified request detection
    simplified_keywords = [
        "just want", "only want", "simple description",
        "short description", "brief description"
    ]
    is_simplified_request = any(keyword in msg_lower for keyword in simplified_keywords)

    # Refine search_query (skip if already set by correction handler above)
    if not corrected_item:
        is_follow_up_type = question_type in ("follow_up", "clarification")
        if is_follow_up_type and context.current_item:
            search_query = context.current_item
        elif is_simplified_request and context.current_item:
            search_query = context.current_item
        else:
            search_query = request.message

    is_follow_up_type = question_type in ("follow_up", "clarification")

    # Find match in dataset
    match_result = find_best_match(dataset_df, search_query, return_confidence=True)

    if match_result[0] is not None:
        best_row, confidence, score = match_result
        matched_item_name = best_row.get("Item Name", "Unknown item")

        # ----------------------------------------------------------------
        # FIX 3: Don't update current_item on a weak new_query match.
        # A weak fuzzy hit on a vague phrase poisons the session state.
        # ----------------------------------------------------------------
        if question_type == "new_query" and confidence == "weak":
            pass  # fall through to vector search

        else:
            item_switched = (
                context.current_item is not None and
                matched_item_name.lower() != context.current_item.lower()
            )

            # ----------------------------------------------------------------
            # FIX 4: On follow-ups, reject a switched item if:
            #   (a) confidence is not strong, OR
            #   (b) the new item is completely unrelated to the current one.
            # This stops "creative repurposing" → "Concrete Rubble" etc.
            # ----------------------------------------------------------------
            if is_follow_up_type and item_switched:
                unrelated = not _items_are_related(context.current_item, matched_item_name)
                if confidence != "strong" or unrelated:
                    # Stay on the tracked item
                    item_name = context.current_item
                    correct_match = find_best_match(
                        dataset_df, context.current_item, return_confidence=True
                    )
                    context_str = (
                        build_item_response(correct_match[0], verbose=False)
                        if correct_match[0] is not None else ""
                    )
                else:
                    # Strong match to a related item — switch is intentional
                    item_name = matched_item_name
                    context.update_current_item(item_name)
                    context_str = build_item_response(best_row, verbose=False)
            else:
                # New query, topic switch, correction, or same item — update normally.
                item_name = matched_item_name
                context.update_current_item(item_name)

                is_verbose = (
                    question_type in ("new_query", "topic_switch")
                    and not corrected_item  # ← suppress boilerplate on corrections
                )
                context_str = build_item_response(best_row, verbose=is_verbose)

            # Build response based on question type
            if question_type == "follow_up" and context.last_response:
                ai_response = get_follow_up_response(
                    request.message,
                    context.last_response,
                    item_name,
                    context_str
                )
            elif question_type == "clarification" and context.last_response:
                if is_simplified_request:
                    ai_response = get_simplified_description(
                        context.last_response,
                        item_name,
                        context_str
                    )
                else:
                    ai_response = get_clarification_response(
                        context.last_response,
                        request.message,
                        item_name
                    )
            else:
                # new_query, topic_switch, correction, or follow_up with no prior response
                conversation_context_str = context.get_context_summary()
                prompt = build_context_aware_prompt(
                    request.message,
                    question_type,
                    context.last_response,
                    context_str,
                    context
                )
                try:
                    ai_response = get_chat_response(
                        prompt,
                        context=context_str,
                        conversation_context=conversation_context_str
                    )
                except Exception:
                    ai_response = context_str

            context.add_exchange(request.message, ai_response)

            return {
                "response": ai_response,
                "match_confidence": confidence,
                "item": item_name,
                "question_type": question_type
            }

    # -----------------------------------------------------------------------
    # FOLLOW-UP WITH NO DATASET MATCH AT ALL
    # Answer from last_response directly — never fall to vector search for
    # follow-ups (vector search returns unrelated items).
    # -----------------------------------------------------------------------
    if is_follow_up_type and context.current_item:
        try:
            conversation_context_str = context.get_context_summary()
            if context.last_response:
                ai_response = get_follow_up_response(
                    request.message,
                    context.last_response,
                    context.current_item,
                    context=""
                )
            else:
                ai_response = get_chat_response(
                    request.message,
                    context="",
                    conversation_context=conversation_context_str
                )
            context.add_exchange(request.message, ai_response)
            return {
                "response": ai_response,
                "match_confidence": "context_only",
                "item": context.current_item,
                "question_type": question_type
            }
        except Exception:
            pass

    # Vector search fallback — only for new queries with no dataset match
    context_str = search_index(index, documents, search_query, k=3)
    if context_str:
        try:
            conversation_context_str = context.get_context_summary()
            ai_response = get_chat_response(
                request.message,
                context=context_str,
                conversation_context=conversation_context_str
            )
            context.add_exchange(request.message, ai_response)
            return {
                "response": ai_response,
                "match_confidence": "weak",
                "item": None,
                "question_type": question_type
            }
        except Exception:
            pass

    # Total fallback
    fallback_response = no_match_response()
    context.add_exchange(request.message, fallback_response)

    return {
        "response": fallback_response,
        "match_confidence": "no_match",
        "item": None,
        "question_type": question_type
    }


@app.post("/reset_session")
async def reset_session(session_id: str = "default"):
    if session_id in conversation_contexts:
        del conversation_contexts[session_id]
    return {"message": f"Session '{session_id}' cleared"}


@app.get("/session_context")
async def get_session_context(session_id: str = "default"):
    if session_id in conversation_contexts:
        ctx = conversation_contexts[session_id]
        return {
            "current_item": ctx.current_item,
            "items_discussed": ctx.items_discussed,
            "question_count": ctx.question_count,
            "context_summary": ctx.get_context_summary()
        }
    return {"message": "Session not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
