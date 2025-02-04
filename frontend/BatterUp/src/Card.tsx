import React from "react";
import cardBackground from "./assets/backgroundcard.png";

interface Player {
  player_id: number;
  basic_info: {
    name: string;
    team: string;
    primary_position: string;
    headshot_url: string;
  };
  role_info: {
    primary_role: string;
  };
  batting_abilities: {
    contact: number;
    power: number;
    discipline: number;
    speed: number;
  };
  pitching_abilities: {
    control: number;
    velocity: number;
    stamina: number;
    effectiveness: number;
  };
  fielding_abilities: {
    defense: number;
    range: number;
    reliability: number;
  };
}

interface CardProps {
  player: Player;
}

const statAbbreviations: { [key: string]: string } = {
  contact: "CON",
  power: "POW",
  discipline: "DIS",
  speed: "SPD",
  control: "CTL",
  velocity: "VEL",
  stamina: "STA",
  effectiveness: "EFF",
  defense: "DEF",
  range: "RNG",
  reliability: "REL",
};

const Card: React.FC<CardProps> = ({ player }) => {
  const getRelevantStats = () => {
    const role = player.role_info.primary_role.toLowerCase();
    let primaryStats: { [key: string]: number } = {};
    let secondaryStats: { [key: string]: number } = {};

    if (role === "pitcher") {
      primaryStats = player.pitching_abilities;
      secondaryStats = {
        ...player.batting_abilities,
        ...player.fielding_abilities,
      };
    } else {
      primaryStats = player.batting_abilities;
      secondaryStats = {
        ...player.pitching_abilities,
        ...player.fielding_abilities,
      };
    }

    const sortedSecondaryStats = Object.entries(secondaryStats)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 2);

    return { primaryStats, sortedSecondaryStats };
  };

  const { primaryStats, sortedSecondaryStats } = getRelevantStats();

  return (
    <div
      className="relative w-80 h-120 rounded-2xl shadow-lg p-6 flex flex-col items-center text-center"
      style={{
        backgroundImage: `url(${cardBackground})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}>
      <img
        src={player.basic_info.headshot_url}
        alt={player.basic_info.name}
        className="w-32 h-32 rounded-full border-2 border-black mt-1" // Adjusted margin-top
      />
      <h2 className="text-2xl font-bold text-black mt-2">
        {player.basic_info.name}
      </h2>
      <p className="text-lg text-gray-800 mt-1">{player.basic_info.team}</p>
      <div className="grid grid-cols-2 gap-2 text-black text-lg font-bold mt-2">
        {Object.entries(primaryStats).map(([key, value]) => (
          <p key={key}>
            {value} {statAbbreviations[key] || key.toUpperCase()}
          </p>
        ))}
        {sortedSecondaryStats.map(([key, value]) => (
          <p key={key}>
            {value} {statAbbreviations[key] || key.toUpperCase()}
          </p>
        ))}
      </div>
    </div>
  );
};

export default Card;
