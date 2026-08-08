"""HTTP cron trigger for platforms without a long-lived process (e.g. Vercel)."""

from __future__ import annotations

import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Query, Request

from src.config import get_settings
from src.services.scheduler_service import run_tick

logger = logging.getLogger(__name__)
router = APIRouter(tags=["cron"])


def _authorized(
    *,
    secret: str,
    x_cron_secret: str | None,
    authorization: str | None,
    query_secret: str | None,
) -> bool:
    if not secret:
        return False
    candidates = [x_cron_secret, query_secret]
    if authorization:
        auth = authorization.strip()
        if auth.lower().startswith("bearer "):
            candidates.append(auth[7:].strip())
        else:
            candidates.append(auth)
    return any(c is not None and hmac.compare_digest(c, secret) for c in candidates)


@router.api_route("/cron/tick", methods=["GET", "POST"])
async def cron_tick(
    request: Request,
    secret: str | None = Query(None, description="Cron secret (alternative to headers)"),
    x_cron_secret: str | None = Header(None, alias="X-Cron-Secret"),
    authorization: str | None = Header(None),
):
    """Run one scheduler tick. Protect with CRON_SECRET.

    cron-job.org examples:
    - Header: ``X-Cron-Secret: <CRON_SECRET>``
    - Or URL: ``https://your.host/cron/tick?secret=<CRON_SECRET>``
    """
    settings = get_settings()
    if not settings.cron_secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET is not configured")
    if not _authorized(
        secret=settings.cron_secret,
        x_cron_secret=x_cron_secret,
        authorization=authorization,
        query_secret=secret,
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info("Cron tick triggered from %s", request.client.host if request.client else "?")
    result = await run_tick()
    return result
