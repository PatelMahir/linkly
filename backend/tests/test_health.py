"""Tests for the liveness and readiness probes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_is_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ready_checks_dependencies(client: AsyncClient) -> None:
    resp = await client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"database": "ok", "redis": "ok"}


@pytest.mark.asyncio
async def test_response_has_observability_headers(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert "X-Request-ID" in resp.headers
    assert "X-Process-Time-Ms" in resp.headers
