import os
import re
from difflib import SequenceMatcher
from typing import List, Tuple, Optional
import pandas as pd

DATASET_PATHS = [
    os.path.join("..", "data", "trash_dataset_cleaned.csv"),
    os.path.join("..", "data", "trash_dataset.csv"),
    os.path.join("data", "trash_dataset_cleaned.csv"),
    os.path.join("data", "trash_dataset.csv"),
]

# FIX: Raised thresholds — old values (0.25 / 0.35 / 0.50) were too low,
# causing garbage like "Concrete Rubble" to match "creative repurposing".
MATCH_THRESHOLD = 0.40
STRONG_MATCH_THRESHOLD = 0.65
MEDIUM_MATCH_THRESHOLD = 0.50

# FIX (Bug #1): Single generic material words must never match a specific item.
# "plastic" alone should NOT match "Bilao (plastic)" — return no_match and let
# the fallback ask the user to be more specific.
GENERIC_MATERIAL_WORDS = {
    "plastic", "metal", "paper", "glass", "wood", "rubber",
    "fabric", "textile", "organic", "electronic", "chemical"
}

ITEM_ALIASES = {
    # English synonyms
    "pet bottle": "plastic bottle",
    "pet": "plastic bottle",
    "polypet": "plastic bottle",
    "plastic bag": "plastic bag",
    "t shirt": "old shirt",
    "tshirt": "old shirt",
    "t-shirt": "old shirt",
    "polo shirt": "old shirt",
    "polo": "old shirt",
    "blouse": "old shirt",
    "jeans": "old pants",
    "denim": "old pants",
    "tetra pak": "juice box",
    "tetrapak": "juice box",
    "styro": "styrofoam",
    "styrofoam box": "styrofoam",
    "foam box": "styrofoam",
    "tin can": "aluminum can",
    "soda can": "aluminum can",
    "beer can": "aluminum can",
    "phone": "mobile phone",
    "cellphone": "mobile phone",
    "cell phone": "mobile phone",
    "laptop": "computer",
    "notebook computer": "computer",
    "light bulb": "lightbulb",
    "cfl": "lightbulb",
    "led bulb": "lightbulb",
    "dead battery": "battery",
    "used battery": "battery",
    "aa battery": "battery",
    "aaa battery": "battery",
    "cooking oil": "used cooking oil",
    "old oil": "used cooking oil",
    "waste oil": "used cooking oil",
    "nappy": "diaper",
    "diapers": "diaper",
    "pampers": "diaper",
    "mask": "face mask",
    "surgical mask": "face mask",
    "n95": "face mask",
    "kn95": "face mask",
    "rubble": "concrete rubble",
    "construction debris": "concrete rubble",
    # Filipino terms
    "bote": "plastic bottle",
    "basura": "general waste",
    "karton": "cardboard",
    "dyaryo": "newspaper",
    "papel": "paper",
    "lata": "aluminum can",
    "baso": "glass",
    "salamin": "glass",
    "gulong": "tire",
    "lumang damit": "old shirt",
    "damit": "old shirt",
    "plastik": "plastic bag",
    "kawayan": "bamboo",
}


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    text = str(value).lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def get_match_confidence(score: float) -> str:
    normalized = score / 100
    if normalized >= STRONG_MATCH_THRESHOLD:
        return "strong"
    elif normalized >= MEDIUM_MATCH_THRESHOLD:
        return "medium"
    elif normalized >= MATCH_THRESHOLD:
        return "weak"
    return "no_match"


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def load_dataset() -> pd.DataFrame:
    actual_path = None
    for path in DATASET_PATHS:
        if os.path.exists(path):
            actual_path = path
            break
    if actual_path is None:
        raise FileNotFoundError(f"No dataset found at {DATASET_PATHS}")
    df = pd.read_csv(actual_path)
    return df.fillna("")


def score_row(row: pd.Series, query: str) -> float:
    query_norm = normalize_text(query)
    query_words = set(query_norm.split())  # used throughout

    item_name = normalize_text(row.get("Item Name", ""))
    main_category = normalize_text(row.get("Main Category", ""))
    subcategory = normalize_text(row.get("Subcategory", ""))
    ai_labels = normalize_text(row.get("AI Detection Labels", ""))

    score = 0.0  # ✅ initialized FIRST before any arithmetic

    # --- Exact full-phrase containment ---
    if query_norm and query_norm in item_name:
        score += 80.0
    if query_norm and query_norm in ai_labels:
        score += 30.0
    if query_norm and query_norm in main_category:
        score += 40.0
    if query_norm and query_norm in subcategory:
        score += 30.0

    # --- Token sets (defined BEFORE they are used) ---
    item_name_tokens = set(item_name.split())       # ✅ defined here
    ai_labels_tokens = set(ai_labels.split())
    main_category_tokens = set(main_category.split())
    subcategory_tokens = set(subcategory.split())

    exact_item_matches = len(query_words & item_name_tokens)
    exact_label_matches = len(query_words & ai_labels_tokens)
    exact_category_matches = len(query_words & main_category_tokens)
    exact_subcategory_matches = len(query_words & subcategory_tokens)

    score += exact_item_matches * 25
    score += exact_label_matches * 6
    score += exact_category_matches * 7
    score += exact_subcategory_matches * 6

    # --- Similarity scores ---
    score += similarity(query_norm, item_name) * 70
    score += similarity(query_norm, ai_labels) * 15
    score += similarity(query_norm, main_category) * 20
    score += similarity(query_norm, subcategory) * 15

    # Bonus when item-name or label token matched
    if exact_item_matches > 0 or exact_label_matches > 0:
        score += 20.0

    # Exact full match bonus
    if query_norm == item_name:
        score += 50.0

    # Length penalty — penalise item names longer than the query
    extra_words = len(item_name_tokens) - len(query_words)
    if extra_words > 0:
        score -= extra_words * 10.0

    # FIX (Bug #3): Extra-token penalty — penalise each word in the item name
    # that does NOT appear in the query at all.
    # Stops "Plastic Bottle Cap" from beating "Plastic Bottle" on query
    # "plastic bottles" because "cap" is a completely foreign token.
    # ✅ item_name_tokens and query_words are both defined above — safe to use.
    item_extra_tokens = item_name_tokens - query_words
    if item_extra_tokens:
        score -= len(item_extra_tokens) * 8.0

    return score


def resolve_alias(query: str) -> str:
    """Return canonical item name if query matches a known alias, else original."""
    return ITEM_ALIASES.get(query.lower().strip(), query)


def find_best_match(df: pd.DataFrame, query: str, return_confidence: bool = False):
    query_normalized = normalize_text(query)

    # FIX (Bug #1): Block single generic material words from matching any item.
    # "plastic" alone should NOT score against "Bilao (plastic)" etc.
    if query_normalized in GENERIC_MATERIAL_WORDS:
        if return_confidence:
            return None, "no_match", 0.0
        return None

    if not query or not query.strip():
        if return_confidence:
            return None, "no_match", 0.0
        return None

    # Resolve aliases before scoring so "pet bottle" → "plastic bottle"
    query = resolve_alias(query)

    scores = []
    for _, row in df.iterrows():
        scores.append((score_row(row, query), row))

    scores.sort(key=lambda item: item[0], reverse=True)

    if not scores:
        if return_confidence:
            return None, "no_match", 0.0
        return None

    best_score, best_row = scores[0]
    confidence = get_match_confidence(best_score)

    if best_score < MATCH_THRESHOLD * 100:
        if return_confidence:
            return None, "no_match", best_score
        return None

    if return_confidence:
        return best_row, confidence, best_score

    return best_row


def find_best_matches(df: pd.DataFrame, query: str, top_k: int = 3) -> List[Tuple]:
    """Find multiple matching rows from dataset."""
    if not query or not query.strip():
        return []

    # Resolve aliases here too
    query = resolve_alias(query)

    scores = []
    for _, row in df.iterrows():
        scores.append((score_row(row, query), row))

    scores.sort(key=lambda item: item[0], reverse=True)

    results = []
    for score, row in scores[:top_k]:
        if score >= MATCH_THRESHOLD * 100:
            confidence = get_match_confidence(score)
            results.append((row, confidence, score))

    return results


def build_item_response(row: pd.Series, verbose: bool = True) -> str:
    """
    Build a structured response string from a dataset row.

    Args:
        row: Dataset row
        verbose: If True (default), include bin, decomposition, priority, and
                 Philippine context. Set to False for follow-up responses to
                 avoid repeating boilerplate on every turn.
    """
    item_name = row.get("Item Name", "Unknown item")
    main_category = row.get("Main Category", "Unknown category")
    recyclable = str(row.get("Recyclable", "No")).strip()
    hazardous = str(row.get("Hazardous", "No")).strip()
    suggested_bin = row.get("Suggested Bin Color", "appropriate bin").strip()
    decomposition = row.get("Decomposition Time", "Unknown").strip()
    priority = row.get("Priority for Correct Disposal", "").strip()
    phil_context = row.get("Philippine Context", "").strip()

    # First line: item name + category + recyclability
    first_line = (
        f"{item_name} — {main_category}, "
        f"{'recyclable' if recyclable.lower().startswith('y') else 'not recyclable'}."
    )
    # Only show bin colour on the first (verbose) response
    if suggested_bin and verbose:
        first_line += f" Use the {suggested_bin.lower()} bin."

    # Safety warnings are ALWAYS shown regardless of verbose flag
    if hazardous.lower().startswith("y") or priority.lower() == "critical":
        warning_lines = []
        if hazardous.lower().startswith("y"):
            warning_lines.append("⚠️ This is hazardous. Do NOT place it in the general bin.")
        if priority.lower() == "critical":
            warning_lines.append("‼️ Priority: Critical disposal required.")
        first_line = f"{' '.join(warning_lines)} {first_line}".strip()

    summary_lines = [first_line]

    if verbose:
        # Disposal / recycling instruction
        instruction = ""
        if recyclable.lower().startswith("y") and row.get("Recycling Instructions 1", "").strip():
            instruction = row.get("Recycling Instructions 1", "").strip()
        elif row.get("Disposal Instructions 1", "").strip():
            instruction = row.get("Disposal Instructions 1", "").strip()
        else:
            instruction = "Follow local disposal rules and your barangay guidelines."
        summary_lines.append(instruction)

        if decomposition:
            summary_lines.append(f"Decomposition time: {decomposition}.")
        if priority:
            summary_lines.append(f"Disposal priority: {priority}.")
        if phil_context:
            summary_lines.append(f"Philippine context: {phil_context}")

        # Follow-up prompts — only on first response
        followups = []
        if str(row.get("Recycling Tip 2", "")).strip():
            followups.append("Want more recycling tips?")
        if str(row.get("Disposal Tip 2", "")).strip():
            followups.append("Want more disposal tips?")
        if str(row.get("Notes / Environmental Impact", "")).strip():
            followups.append("Should I explain the environmental impact?")

        if followups:
            summary_lines.append(
                "".join([f"{i+1}. {opt} " for i, opt in enumerate(followups)]).strip()
            )

    return "\n".join([line for line in summary_lines if line])


def no_match_response() -> str:
    return (
        "I couldn't identify that item exactly. "
        "Can you tell me if it's plastic, metal, paper, organic, or something else?"
    )