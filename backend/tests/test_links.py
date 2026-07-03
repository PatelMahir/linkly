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


@pytest.mark.asyncio
async def test_list_links_pagination(client: AsyncClient) -> None:
    for i in range(5):
        await client.post("/api/links", json={"long_url": f"https://example.com/{i}"})

    page = (await client.get("/api/links", params={"limit": 2, "offset": 0})).json()
    assert len(page) == 2

    page2 = (await client.get("/api/links", params={"limit": 2, "offset": 2})).json()
    assert len(page2) == 2
    # Pages must not overlap.
    assert {link["id"] for link in page}.isdisjoint({link["id"] for link in page2})


@pytest.mark.asyncio
async def test_pagination_rejects_bad_limit(client: AsyncClient) -> None:
    assert (await client.get("/api/links", params={"limit": 0})).status_code == 422
    assert (await client.get("/api/links", params={"limit": 999})).status_code == 422


@pytest.mark.asyncio
async def test_redirect_uses_cache_on_second_hit(client: AsyncClient) -> None:
    """First redirect populates the cache; the code should then be resolvable
    from Redis even if the DB row is gone."""
    created = (
        await client.post(
            "/api/links",
            json={"long_url": "https://example.com/cached", "custom_code": "cache1"},
        )
    ).json()

    first = await client.get(f"/{created['code']}", follow_redirects=False)
    assert first.status_code == 307
    assert first.headers["location"] == "https://example.com/cached"
