import React from "react";
import PlayerTable from "../PlayerTable";

const AdminPanel: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Admin Panel</h1>
        <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
          User
        </button>
      </div>

      {/* Player Table */}
      <PlayerTable />
    </div>
  );
};

export default AdminPanel;
