import pytest
from fastapi.testclient import TestClient
from api import api
from database import Base, engine, Session as SessionLocal
client = TestClient(api)


# ---- Reset DB trước mỗi test ----
@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


# ---- Fixtures ----
@pytest.fixture
def setup_users():
    client.post("/users/", json={"email": "alice@example.com", "name": "Alice"})
    client.post("/users/", json={"email": "bob@example.com", "name": "Bob"})
    return ["alice@example.com", "bob@example.com"]


@pytest.fixture
def setup_message(setup_users):
    sender, recipient = setup_users
    response = client.post(
        "/messages/",
        json={
            "sender_id": sender,
            "recipients": [recipient],
            "subject": "Test subject",
            "content": "Hello Bob!",
        },
    )
    assert response.status_code == 200
    return response.json()  # trả về object message (có id)


# ---- User tests ----
def test_get_user_by_email(setup_users):
    response = client.get(f"/users/{setup_users[0]}")
    assert response.status_code == 200
    assert response.json()["email"] == setup_users[0]

def test_get_all_users():
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---- Message tests ----
def test_send_message(setup_message):
    assert "subject" in setup_message
    assert setup_message["subject"] == "Test subject"

def test_get_all_sent_message(setup_users):
    response = client.get(f"/messages/sent/{setup_users[0]}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_view_inbox(setup_users):
    response = client.get(f"/messages/inbox/{setup_users[1]}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_unread_message(setup_users):
    response = client.get(f"/messages/unread/{setup_users[1]}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_message_with_recipients(setup_message):
    message_id = setup_message["id"]
    response = client.get(f"/messages/{message_id}/recipients")
    assert response.status_code == 200
    data = response.json()
    assert "recipients" in data

def test_mark_as_read(setup_message, setup_users):
    message_id = setup_message["id"]
    recipient = setup_users[1]
    response = client.post(
        f"/messages/{message_id}/read",
        json={"recipient_id": recipient},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("read") is True

