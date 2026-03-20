import re

def analyze_quality(response_text: str) -> list[str]:
    """
    Analyzes an LLM response and applies quality heuristics.
    Returns a list of flags.
    """
    flags = []
    
    # Heuristic 1: too_short (< 20 words)
    words = response_text.split()
    if len(words) < 20:
        flags.append("too_short")
        
    # Heuristic 2: refusal
    refusal_phrases = [
        "i cannot", 
        "i'm sorry, i can't", 
        "i am unable", 
        "as an ai",
        "i do not have access",
        "i apologize, but i cannot"
    ]
    lower_text = response_text.lower()
    if any(phrase in lower_text for phrase in refusal_phrases):
        flags.append("refusal")
        
    # Heuristic 3: repetition (same sentence 3+ times)
    # Split by common sentence delimiters
    sentences = re.split(r'[.!?]+', response_text)
    # Clean up and remove empty
    sentences = [s.strip().lower() for s in sentences if len(s.strip()) > 5]
    
    sentence_counts = {}
    for s in sentences:
        sentence_counts[s] = sentence_counts.get(s, 0) + 1
        if sentence_counts[s] >= 3:
            flags.append("repetition")
            break  # Only need to flag it once
            
    # Heuristic 4: low_confidence
    hedging_phrases = [
        "it seems that",
        "it might be",
        "i could be wrong",
        "it is possible that",
        "there is a chance"
    ]
    if any(phrase in lower_text for phrase in hedging_phrases):
        flags.append("low_confidence")
            
    return flags
