"""Authentication & multi-tenancy resolution.

Supabase is the identity provider: the frontend signs users in and sends the
Supabase access token (a JWT) as `Authorization: Bearer <token>`. We verify it,
then just-in-time provision a matching row in our `users` table and resolve the
caller's organization membership.

Supabase supports two token-signing schemes and we handle both:
  * Asymmetric (ES256/RS256/EdDSA) — the current default. Verified against the
    project's public keys fetched from the JWKS endpoint.
  * Symmetric (HS256) — legacy projects. Verified with SUPABASE_JWT_SECRET.

The resulting `AuthContext` carries the user and active organization and is the
sole source of the organization_id used for all tenant-scoped data access.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import get_settings
from .db import connection
from .logging import get_logger

log = get_logger(__name__)


@lru_cache
def _jwks_client() -> "jwt.PyJWKClient":
    url = get_settings().supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    return jwt.PyJWKClient(url)


@dataclass
class AuthContext:
    user_id: str
    email: str
    organization_id: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role in ("owner", "admin")


class AuthError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _decode_token(token: str) -> dict:
    settings = get_settings()
    # leeway tolerates small clock skew between the token issuer (Supabase) and
    # this host — common under Docker Desktop, where the VM clock can drift and
    # otherwise trips "token not yet valid (iat/nbf)".
    opts = {"audience": "authenticated", "options": {"verify_aud": True}, "leeway": 60}
    try:
        alg = jwt.get_unverified_header(token).get("alg", "")
        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                raise AuthError("Auth not configured (missing SUPABASE_JWT_SECRET for HS256 tokens).")
            return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **opts)
        # Asymmetric (current Supabase default): verify against the project's
        # public keys from the JWKS endpoint.
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(token, signing_key.key, algorithms=["RS256", "ES256", "EdDSA"], **opts)
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired.")
    except jwt.InvalidTokenError as exc:
        raise AuthError(f"Invalid token: {exc}")
    except jwt.PyJWKClientError as exc:
        raise AuthError(f"Could not resolve signing key: {exc}")


def _provision_user_and_org(user_id: str, email: str, name: str | None) -> tuple[str, str]:
    """Ensure the user exists and belongs to an org. Returns (organization_id, role).

    On first sign-in a personal organization is created and the user is made its
    owner. (Inviting users into an existing org is a later feature; this gives a
    working tenant immediately.)
    """
    with connection() as conn:
        with conn.transaction():
            conn.execute(
                """
                INSERT INTO users (id, email, full_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email
                """,
                (user_id, email, name),
            )
            membership = conn.execute(
                """
                SELECT organization_id, role FROM memberships
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY created_at ASC LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if membership:
                return str(membership["organization_id"]), membership["role"]

            org_name = (email.split("@")[0] if email else "My") + "'s Organization"
            org = conn.execute(
                "INSERT INTO organizations (name) VALUES (%s) RETURNING id",
                (org_name,),
            ).fetchone()
            org_id = str(org["id"])
            conn.execute(
                """
                INSERT INTO memberships (organization_id, user_id, role)
                VALUES (%s, %s, 'owner')
                """,
                (org_id, user_id),
            )
            log.info("provisioned_new_org", user_id=user_id, organization_id=org_id)
            return org_id, "owner"


async def get_auth_context(
    authorization: str | None = Header(default=None),
) -> AuthContext:
    """FastAPI dependency: verify the bearer token and resolve tenant context."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("Missing bearer token.")
    token = authorization.split(" ", 1)[1].strip()
    claims = _decode_token(token)

    user_id = claims.get("sub")
    email = claims.get("email", "")
    name = (claims.get("user_metadata") or {}).get("full_name")
    if not user_id:
        raise AuthError("Token missing subject (sub).")

    org_id, role = _provision_user_and_org(user_id, email, name)
    return AuthContext(user_id=user_id, email=email, organization_id=org_id, role=role)


def require_admin(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    """Dependency variant that additionally requires owner/admin role."""
    if not ctx.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required.")
    return ctx
