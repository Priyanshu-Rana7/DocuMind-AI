def test_health_check_via_conftest_client(client):
    request_id = "test-request-123"
    response = client.get("/api/v1/health", headers={"X-Request-ID": request_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert data["migration"] in {"not_initialized", "unknown"} or data["migration"]
    assert isinstance(data["llm_configured"], bool)
    assert data["ocr_configured"] is True
    assert "OPENROUTER_API_KEY" not in str(data)
