"""Schema the model must conform to. Validated before use (never trust raw text)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# The fixed category set (PRD). Keep in sync with the eval set and UI.
CATEGORIES = ("Support", "Sales", "Billing", "Spam", "Other")
Category = Literal["Support", "Sales", "Billing", "Spam", "Other"]
Urgency = Literal["low", "normal", "high"]


class ClassificationResult(BaseModel):
    category: Category
    confidence: float = Field(..., ge=0.0, le=1.0)
    urgency: Urgency = "normal"
    rationale: str = Field(default="", max_length=500)

    @field_validator("confidence")
    @classmethod
    def _clamp(cls, v: float) -> float:
        return max(0.0, min(1.0, v))
