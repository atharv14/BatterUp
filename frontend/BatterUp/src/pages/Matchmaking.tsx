import React, { useEffect, useState } from "react";
import axios, { AxiosError } from "axios";
import { useAuth } from "../AuthContext";
import "./Matchmaking.css"; // Import the CSS file

const Matchmaking: React.FC = () => {
  const [gameId, setGameId] = useState<string>("");
  const [joinGameId, setJoinGameId] = useState<string>("");
  const [deck, setDeck] = useState<any>(null);
  const [firebaseUid, setFirebaseUid] = useState<string>("");
  const { token } = useAuth();

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await axios.get(
          "http://localhost:8000/api/v1/auth/me",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        console.log("Fetched user data:", response.data);
        setDeck(response.data.deck);
        setFirebaseUid(response.data.firebase_uid);
      } catch (error) {
        console.error("Error fetching user data:", error);
      }
    };

    fetchUserData();
  }, [token]);

  const createGame = async () => {
    if (!deck || !firebaseUid) {
      console.error("Deck or Firebase UID is not set");
      return;
    }

    try {
      const requestData = { user_id: firebaseUid, deck };
      console.log(
        "Request data to /games/create:",
        JSON.stringify(requestData, null, 2)
      );
      const response = await axios.post(
        "http://localhost:8000/api/v1/games/create",
        requestData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      console.log("Response from /games/create:", response.data);
      setGameId(response.data.game_id);
    } catch (error) {
      const axiosError = error as AxiosError;
      console.error("Error creating game:", axiosError);
      if (axiosError.response) {
        console.error("Response data:", axiosError.response.data);
      }
    }
  };

  const joinGame = async () => {
    if (!deck || !firebaseUid) {
      console.error("Deck or Firebase UID is not set");
      return;
    }

    try {
      const requestData = { user_id: firebaseUid, deck };
      console.log(
        "Request data to /games/join:",
        JSON.stringify(requestData, null, 2)
      );
      await axios.post(
        `http://localhost:8000/api/v1/games/${joinGameId}/join`,
        requestData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      alert("Successfully joined the game!");
    } catch (error) {
      const axiosError = error as AxiosError;
      console.error("Error joining game:", axiosError);
      if (axiosError.response) {
        console.error("Response data:", axiosError.response.data);
      }
    }
  };

  return (
    <div className="container">
      <button className="button" onClick={createGame}>
        Create Game
      </button>
      {gameId && <p className="game-id">Game ID: {gameId}</p>}
      <input
        className="input"
        type="text"
        value={joinGameId}
        onChange={(e) => setJoinGameId(e.target.value)}
        placeholder="Enter Game ID"
      />
      <button className="button" onClick={joinGame}>
        Join Game
      </button>
    </div>
  );
};

export default Matchmaking;
