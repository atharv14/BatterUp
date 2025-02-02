import React from "react";
import { Routes, Route } from "react-router-dom";
import HomeScreen from "./pages/HomeScreen";
import LoginScreen from "./pages/LoginScreen";
import AdminPanel from "./pages/AdminPanel";
import ProtectedRoute from "./ProtectedRoute";
import PlayerTable from "./PlayerTable";
import Card from "./Card";
import CreateDeck from "./pages/CreateDeck";

const App: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginScreen />} />
      <Route path="/" element={<HomeScreen />} />

      {/* Protected Route for Logged-in Users */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <PlayerTable />
            <Card />
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
