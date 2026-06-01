"""Routing engine (Module 6).

Evaluates ordered, per-organisation rules against a classified email to choose an
assignee and/or CRM action, then fires a Slack notification if configured. Every
email ends up owned (assigned) or explicitly left in the unassigned queue.
"""
from .engine import evaluate_conditions, first_matching_rule
from .service import route_email

__all__ = ["evaluate_conditions", "first_matching_rule", "route_email"]
