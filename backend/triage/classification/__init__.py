"""Email intent classification (Module 3).

Structured-output classification through the LLM wrapper: every email gets a
{category, confidence, urgency}. Below the confidence threshold the email is
routed to a human-review lane unclassified rather than guessed.
"""
from .schemas import CATEGORIES, ClassificationResult
from .service import classify_email, classify_text

__all__ = ["CATEGORIES", "ClassificationResult", "classify_email", "classify_text"]
