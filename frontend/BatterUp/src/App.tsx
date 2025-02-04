import React from "react";
import { Routes, Route } from "react-router-dom";
import HomeScreen from "./pages/HomeScreen";
import LoginScreen from "./pages/LoginScreen";
import AdminPanel from "./pages/AdminPanel";
import ProtectedRoute from "./ProtectedRoute";
import CreateDeck from "./pages/CreateDeck";
import Matchmaking from "./pages/Matchmaking";
import GameComponent from "./pages/GameComponent";

const App: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginScreen />} />
      <Route path="/" element={<HomeScreen />} />

      {/* Protected Route for Logged-in Users */}
      <Route
        path="/matchmaking"
        element={
          <ProtectedRoute>
            <Matchmaking />
          </ProtectedRoute>
        }
      />
      <Route
        path="/create-deck"
        element={
          <ProtectedRoute>
            <CreateDeck />
          </ProtectedRoute>
        }
      />

      <Route
        path="/game/:gameId"
        element={
          <ProtectedRoute>
            <GameComponent />
          </ProtectedRoute>
        }
      />
      {/* Other routes */}
      <Route
        path="/games/:gameId/pitch"
        element={
          <ProtectedRoute>
            <GameComponent />
          </ProtectedRoute>
        }
      />
      <Route
        path="/games/:gameId/bat"
        element={
          <ProtectedRoute>
            <GameComponent />
          </ProtectedRoute>
        }
      />

      {/* Admin-Only Route */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute role="admin">
            <AdminPanel />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

export default App;
