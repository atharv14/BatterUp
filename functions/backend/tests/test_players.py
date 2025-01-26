from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_player():
    # Test with string ID
    response = client.get("/api/v1/players/650391")
    assert response.status_code == 200
    assert isinstance(response.json()["player_id"], str)

def test_get_players_list():
    response = client.get("/api/v1/players/")
    assert response.status_code == 200

    data = response.json()
    assert "players" in data
    assert "total" in data

    # Verify all player_ids are strings
    for player in data["players"]:
        assert isinstance(player["player_id"], str)

def test_get_player_headshot_url():
    response = client.get("/api/v1/players/650391/headshot/url")
    assert response.status_code == 200
    assert "url" in response.json()
    assert "mlb.com" in response.json()["url"]
