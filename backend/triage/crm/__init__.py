"""Pluggable CRM logging for the 'Send & log to CRM' action.

Providers (config.crm_provider):
  * none     — no-op (default).
  * webhook  — POST the interaction as JSON to any URL (works with HubSpot
               workflows, Zapier, Make, or webhook.site for testing).
  * hubspot  — native: upsert the contact by email and attach a note.

All failures are swallowed and logged — a CRM outage must never block sending
the customer's reply (the reply delivery already happened).
"""
from .service import log_interaction

__all__ = ["log_interaction"]
