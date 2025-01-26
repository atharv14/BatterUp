import React from "react";

// Define the player type
interface Player {
  id: number;
  name: string;
  role: string;
  strength: number;
  speed: number;
  accuracy: number;
  intelligence: number;
  elusiveness: number;
  durability: number;
}

const PlayerTable: React.FC = () => {
  const players: Player[] = [
    {
      id: 1,
      name: "John Doe",
      role: "Warrior",
      strength: 80,
      speed: 70,
      accuracy: 75,
      intelligence: 60,
      elusiveness: 50,
      durability: 85,
    },
    {
      id: 2,
      name: "Jane Smith",
      role: "Mage",
      strength: 50,
      speed: 60,
      accuracy: 85,
      intelligence: 95,
      elusiveness: 65,
      durability: 55,
    },
    // Add more player data as needed
  ];

  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow-md">
      <table className="min-w-full text-left border-collapse">
        <thead>
          <tr className="bg-gray-200 text-gray-700">
            <th className="p-3">ID</th>
            <th className="p-3">Name</th>
            <th className="p-3">Role</th>
            <th className="p-3">Strength</th>
            <th className="p-3">Speed</th>
            <th className="p-3">Accuracy</th>
            <th className="p-3">Intelligence</th>
            <th className="p-3">Elusiveness</th>
            <th className="p-3">Durability</th>
          </tr>
        </thead>
        <tbody>
          {players.map((player) => (
            <tr key={player.id} className="border-b hover:bg-gray-100">
              <td className="p-3">{player.id}</td>
              <td className="p-3">{player.name}</td>
              <td className="p-3">{player.role}</td>
              <td className="p-3">{player.strength}</td>
              <td className="p-3">{player.speed}</td>
              <td className="p-3">{player.accuracy}</td>
              <td className="p-3">{player.intelligence}</td>
              <td className="p-3">{player.elusiveness}</td>
              <td className="p-3">{player.durability}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PlayerTable;
