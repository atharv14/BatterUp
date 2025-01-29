import React from "react";
import { Routes, Route } from "react-router-dom";
import HomeScreen from "./HomeScreen";
import LoginScreen from "./LoginScreen";
import AdminPanel from "./AdminPanel";
import ProtectedRoute from "./ProtectedRoute";
import PlayerTable from "./PlayerTable";

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
