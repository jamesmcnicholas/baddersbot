from fastapi.testclient import TestClient

from baddersbot.app import create_app


def get_client() -> TestClient:
    return TestClient(create_app())


def test_admin_dashboard_renders() -> None:
    client = get_client()
    response = client.get("/admin/dashboard")

    assert response.status_code == 200
    assert "Administrator Dashboard" in response.text
    assert "Pending Payments" in response.text
    assert "Upcoming Week Sessions" in response.text


def test_allocation_management_renders() -> None:
    client = get_client()
    response = client.get("/admin/allocation")

    assert response.status_code == 200
    assert "Session Allocation Control" in response.text
    assert "Manual Change Log" in response.text


def test_allocation_messages_renders() -> None:
    client = get_client()
    response = client.get("/admin/allocation/messages")

    assert response.status_code == 200
    assert "WhatsApp Message Builder" in response.text
    assert "Tue 6pm - Court 1" in response.text


def test_manage_users_renders() -> None:
    client = get_client()
    response = client.get("/admin/users")

    assert response.status_code == 200
    assert "Player Directory" in response.text
    assert "Showing" in response.text
