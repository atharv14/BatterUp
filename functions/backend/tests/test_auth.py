import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Mock Firebase token
TEST_TOKEN = "your_test_token"

def test_register_user():
    response = client.post(
        "/api/v1/users/register",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "firebase_uid": "test_uid",
            "email": "test@example.com",
            "username": "testuser"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_create_deck():
    response = client.post(
        "/api/v1/users/deck",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "PITCHER": ["650391", "650392", "650393", "650394", "650395"],
            "CATCHER": ["650396"],
            "INFIELDER": ["650397", "650398", "650399", "650400"],
            "OUTFIELDER": ["650401", "650402", "650403"],
            "HITTER": ["650404", "650405", "650406", "650407"]
        }
    )
    assert response.status_code == 200
    assert len(response.json()["cards"]["PITCHER"]) == 5