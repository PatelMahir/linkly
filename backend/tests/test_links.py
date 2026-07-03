"""API tests covering the create → redirect → analytics happy path."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_link_returns_short_url(client: AsyncClient) -> None:
    resp = await client.post("/api/links", json={"long_url": "https://example.com/page"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["long_url"] == "https://example.com/page"
    assert body["code"]
    assert body["short_url"].endswith(body["code"])


@pytest.mark.asyncio
async def test_custom_code_conflict(client: AsyncClient) -> None:
    payload = {"long_url": "https://example.com", "custom_code": "mycode"}
    first = await client.post("/api/links", json=payload)
    assert first.status_code == 201

    dupe = await client.post("/api/links", json=payload)
    assert dupe.status_code == 409


@pytest.mark.asyncio
async def test_redirect_and_analytics(client: AsyncClient) -> None:
    created = (
        await client.post(
            "/api/links",
            json={"long_url": "https://example.com/dest", "custom_code": "go1"},
        )
    ).json()

    # Redirect (don't follow) should 307 to the destination.
    redirect = await client.get(f"/{created['code']}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/dest"

    # The click should now show up in analytics.
    stats = (await client.get(f"/api/analytics/{created['code']}")).json()
    assert stats["total_clicks"] == 1


@pytest.mark.asyncio
async def test_invalid_url_rejected(client: AsyncClient) -> None:
    resp = await client.post("/api/links", json={"long_url": "not-a-url"})
    assert resp.status_code == 422  # Pydantic validation error
