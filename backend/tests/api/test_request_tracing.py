def test_request_tracing_generates_request_id_and_returns_it(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    generated_request_id = response.headers.get("X-Request-ID")
    assert generated_request_id
    assert len(generated_request_id) == 36


def test_request_id_is_included_in_application_errors(client):
    request_id = "missing-invoice-request"
    response = client.get(
        "/api/v1/invoices/not-found",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id


def test_processing_requests_are_rate_limited(client):
    for _ in range(3):
        response = client.post("/api/v1/invoices/process")
        assert response.status_code == 422

    response = client.post("/api/v1/invoices/process")

    assert response.status_code == 429
    assert response.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert response.headers["Retry-After"]
