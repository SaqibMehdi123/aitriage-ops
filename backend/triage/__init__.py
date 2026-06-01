"""AI Inbox Triage + Reply Router — backend package.

Contains the FastAPI API, the Celery worker, the pluggable LLM wrapper, and the
shared data/auth layer. Conventions and architecture are described in the
project TRD; this package implements Modules 0–1 (Foundation + Auth/tenancy).
"""

__version__ = "0.1.0"
