import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../AuthContext";
import Card from "../Card";

const CreateDeck: React.FC = () => {
  const [players, setPlayers] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [filterColumn, setFilterColumn] = useState<string>("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState<number>(0);
  const [selectedPlayers, setSelectedPlayers] = useState<any[]>([]);
  const [previewPlayer, setPreviewPlayer] = useState<any | null>(null);
  const playersPerPage = 15;
  const { user, token } = useAuth();

  console.log("Current User:", user);
  console.log("Token:", token);

  const roleLimits = {
    catcher: 1,
    pitcher: 5,
    infielder: 4,
    hitter: 4,
    outfielder: 3,
  };

  const getToken = () => {
    // Replace this with your actual token retrieval logic
    return localStorage.getItem("token");
  };

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const token = getToken();
        const response = await axios.get(
          "http://localhost:8000/api/v1/players",
          {
            params: {
              role: null,
              team: null,
              position: null,
              limit: 1454,
              offset: 0,
            },
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.data && Array.isArray(response.data.players)) {
          setPlayers(response.data.players);
        } else {
          console.error("Unexpected response format:", response.data);
        }
      } catch (error) {
        console.error("Error fetching players:", error);
      }
    };

    fetchPlayers();
  }, []);

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleFilterChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setFilterColumn(event.target.value);
  };

  const handleSortOrderChange = () => {
    setSortOrder((prevOrder) => (prevOrder === "asc" ? "desc" : "asc"));
  };

  const handleNextPage = () => {
    setCurrentPage((prevPage) => prevPage + 1);
  };

  const handlePreviousPage = () => {
    setCurrentPage((prevPage) => Math.max(prevPage - 1, 0));
  };

  const handlePreviewPlayer = (player: any) => {
    setPreviewPlayer(player); // Function to set preview player
  };

  const handleSelectPlayer = (player: any) => {
    if (selectedPlayers.some((p) => p.player_id === player.player_id)) {
      alert("This player is already selected.");
      return;
    }

    const role = player.role_info.primary_role.toLowerCase();
    const roleCount = selectedPlayers.filter(
      (p) => p.role_info.primary_role.toLowerCase() === role
    ).length;

    if (
      (role === "catcher" && roleCount >= roleLimits.catcher) ||
      (role === "pitcher" && roleCount >= roleLimits.pitcher) ||
      ((role === "infielder" || role === "hitter") &&
        roleCount >= roleLimits.infielder) ||
      (role === "outfielder" && roleCount >= roleLimits.outfielder)
    ) {
      alert(`You have already selected the maximum number of ${role}s.`);
      return;
    }

    setSelectedPlayers((prevSelected) => [...prevSelected, player]);
  };

  const handleRemovePlayer = (playerId: string) => {
    setSelectedPlayers((prevSelected) =>
      prevSelected.filter((p) => p.player_id !== playerId)
    );
  };

  const handleSubmit = async () => {
    const requestBody = {
      catchers: selectedPlayers
        .filter((p) => p.role_info.primary_role.toLowerCase() === "catcher")
        .map((p) => p.player_id),
      pitchers: selectedPlayers
        .filter((p) => p.role_info.primary_role.toLowerCase() === "pitcher")
        .map((p) => p.player_id),
      infielders: selectedPlayers
        .filter((p) => p.role_info.primary_role.toLowerCase() === "infielder")
        .map((p) => p.player_id),
      outfielders: selectedPlayers
        .filter((p) => p.role_info.primary_role.toLowerCase() === "outfielder")
        .map((p) => p.player_id),
      hitters: selectedPlayers
        .filter((p) => p.role_info.primary_role.toLowerCase() === "hitter")
        .map((p) => p.player_id),
    };

    if (!token) {
      console.error("No token found");
      alert("No token found. Please log in.");
      return;
    }

    console.log("Submitting deck with token:", token); // Debugging: Log the token

    try {
      const response = await axios.post(
        "http://localhost:8000/api/v1/users/deck",
        requestBody,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      alert("Deck submitted successfully!");
    } catch (error) {
      console.error("Error submitting deck:", error);
      alert("Failed to submit deck.");
    }
  };

  const filteredPlayers = players.filter((player: any) => {
    const value =
      player.basic_info[filterColumn] ||
      player.batting_abilities[filterColumn] ||
      player.pitching_abilities[filterColumn] ||
      player.fielding_abilities[filterColumn];
    return value?.toString().toLowerCase().includes(searchTerm.toLowerCase());
  });

  const sortedPlayers = filteredPlayers.sort((a: any, b: any) => {
    const aValue =
      a.basic_info[filterColumn] ||
      a.batting_abilities[filterColumn] ||
      a.pitching_abilities[filterColumn] ||
      a.fielding_abilities[filterColumn];
    const bValue =
      b.basic_info[filterColumn] ||
      b.batting_abilities[filterColumn] ||
      b.pitching_abilities[filterColumn] ||
      b.fielding_abilities[filterColumn];

    if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
    if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  const paginatedPlayers = sortedPlayers.slice(
    currentPage * playersPerPage,
    (currentPage + 1) * playersPerPage
  );

  const roleCounts = {
    catcher: selectedPlayers.filter(
      (p) => p.role_info.primary_role.toLowerCase() === "catcher"
    ).length,
    pitcher: selectedPlayers.filter(
      (p) => p.role_info.primary_role.toLowerCase() === "pitcher"
    ).length,
    infielder: selectedPlayers.filter(
      (p) =>
        p.role_info.primary_role.toLowerCase() === "infielder" ||
        p.role_info.primary_role.toLowerCase() === "hitter"
    ).length,
    outfielder: selectedPlayers.filter(
      (p) => p.role_info.primary_role.toLowerCase() === "outfielder"
    ).length,
  };

  return (
    <div style={{ display: "flex", padding: "20px" }}>
      <div style={{ flex: 1, marginRight: "20px" }}>
        <h1>Create Deck</h1>
        <div style={{ marginBottom: "20px" }}>
          <input
            type="text"
            placeholder="Search"
            value={searchTerm}
            onChange={handleSearch}
            style={{ padding: "10px", marginRight: "10px" }}
          />
          <select
            value={filterColumn}
            onChange={handleFilterChange}
            style={{ padding: "10px", marginRight: "10px" }}>
            <option value="name">Name</option>
            <option value="primary_position">Position</option>
            <option value="team">Team</option>
            <option value="contact">Contact</option>
            <option value="power">Power</option>
            <option value="discipline">Discipline</option>
            <option value="speed">Speed</option>
            <option value="control">Control</option>
            <option value="velocity">Velocity</option>
            <option value="stamina">Stamina</option>
            <option value="effectiveness">Effectiveness</option>
            <option value="defense">Defense</option>
            <option value="range">Range</option>
            <option value="reliability">Reliability</option>
          </select>
          <button onClick={handleSortOrderChange} style={{ padding: "10px" }}>
            Sort {sortOrder === "asc" ? "Descending" : "Ascending"}
          </button>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ ...headerStyle, width: "50px" }}>ID</th>
              <th style={{ ...headerStyle, width: "150px" }}>Name</th>
              <th style={{ ...headerStyle, width: "100px" }}>Role</th>
              <th style={{ ...headerStyle, width: "100px" }}>Team</th>
              <th style={{ ...headerStyle, width: "100px" }}>Position</th>
              <th style={{ ...headerStyle, width: "80px" }}>Contact</th>
              <th style={{ ...headerStyle, width: "80px" }}>Power</th>
              <th style={{ ...headerStyle, width: "80px" }}>Discipline</th>
              <th style={{ ...headerStyle, width: "80px" }}>Speed</th>
              <th style={{ ...headerStyle, width: "80px" }}>Control</th>
              <th style={{ ...headerStyle, width: "80px" }}>Velocity</th>
              <th style={{ ...headerStyle, width: "80px" }}>Stamina</th>
              <th style={{ ...headerStyle, width: "80px" }}>Effectiveness</th>
              <th style={{ ...headerStyle, width: "80px" }}>Defense</th>
              <th style={{ ...headerStyle, width: "80px" }}>Range</th>
              <th style={{ ...headerStyle, width: "80px" }}>Reliability</th>
              <th style={{ ...headerStyle, width: "80px" }}>Select</th>
            </tr>
          </thead>
          <tbody>
            {paginatedPlayers.map((player: any) => (
              <tr
                key={player.player_id}
                style={rowStyle}
                onClick={() => handlePreviewPlayer(player)}
                className="cursor-pointer">
                <td style={cellStyle}>{player.player_id}</td>
                <td style={cellStyle}>{player.basic_info.name}</td>
                <td style={cellStyle}>{player.role_info.primary_role}</td>
                <td style={cellStyle}>{player.basic_info.team}</td>
                <td style={cellStyle}>{player.basic_info.primary_position}</td>
                <td style={cellStyle}>{player.batting_abilities.contact}</td>
                <td style={cellStyle}>{player.batting_abilities.power}</td>
                <td style={cellStyle}>{player.batting_abilities.discipline}</td>
                <td style={cellStyle}>{player.batting_abilities.speed}</td>
                <td style={cellStyle}>{player.pitching_abilities.control}</td>
                <td style={cellStyle}>{player.pitching_abilities.velocity}</td>
                <td style={cellStyle}>{player.pitching_abilities.stamina}</td>
                <td style={cellStyle}>
                  {player.pitching_abilities.effectiveness}
                </td>
                <td style={cellStyle}>{player.fielding_abilities.defense}</td>
                <td style={cellStyle}>{player.fielding_abilities.range}</td>
                <td style={cellStyle}>
                  {player.fielding_abilities.reliability}
                </td>
                <td style={cellStyle}>
                  <button onClick={() => handleSelectPlayer(player)}>
                    Select
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: "20px" }}>
          <button
            onClick={handlePreviousPage}
            disabled={currentPage === 0}
            style={{ padding: "10px", marginRight: "10px" }}>
            Previous
          </button>
          <button
            onClick={handleNextPage}
            disabled={
              (currentPage + 1) * playersPerPage >= sortedPlayers.length
            }
            style={{ padding: "10px" }}>
            Next
          </button>
        </div>
      </div>
      <div style={{ flex: 1 }}>
        <h2>Selected Players</h2>
        <div>
          <h3>
            Catcher ({roleCounts.catcher}/{roleLimits.catcher})
          </h3>
          <ul>
            {selectedPlayers
              .filter(
                (player) =>
                  player.role_info.primary_role.toLowerCase() === "catcher"
              )
              .map((player) => (
                <li
                  key={player.player_id}
                  style={{ display: "flex", alignItems: "center" }}>
                  <span>{player.basic_info.name}</span>
                  <button
                    onClick={() => handleRemovePlayer(player.player_id)}
                    style={{
                      marginLeft: "10px",
                      padding: "5px 10px",
                      border: "1px solid #ddd",
                      backgroundColor: "#f9f9f9",
                      cursor: "pointer",
                    }}>
                    Remove
                  </button>
                </li>
              ))}
          </ul>
        </div>
        <div>
          <h3>
            Pitchers ({roleCounts.pitcher}/{roleLimits.pitcher})
          </h3>
          <ul>
            {selectedPlayers
              .filter(
                (player) =>
                  player.role_info.primary_role.toLowerCase() === "pitcher"
              )
              .map((player) => (
                <li
                  key={player.player_id}
                  style={{ display: "flex", alignItems: "center" }}>
                  <span>{player.basic_info.name}</span>
                  <button
                    onClick={() => handleRemovePlayer(player.player_id)}
                    style={{
                      marginLeft: "10px",
                      padding: "5px 10px",
                      border: "1px solid #ddd",
                      backgroundColor: "#f9f9f9",
                      cursor: "pointer",
                    }}>
                    Remove
                  </button>
                </li>
              ))}
          </ul>
        </div>
        <div>
          <h3>
            Infielders/Hitters ({roleCounts.infielder}/{roleLimits.infielder})
          </h3>
          <ul>
            {selectedPlayers
              .filter(
                (player) =>
                  player.role_info.primary_role.toLowerCase() === "infielder" ||
                  player.role_info.primary_role.toLowerCase() === "hitter"
              )
              .map((player) => (
                <li
                  key={player.player_id}
                  style={{ display: "flex", alignItems: "center" }}>
                  <span>{player.basic_info.name}</span>
                  <button
                    onClick={() => handleRemovePlayer(player.player_id)}
                    style={{
                      marginLeft: "10px",
                      padding: "5px 10px",
                      border: "1px solid #ddd",
                      backgroundColor: "#f9f9f9",
                      cursor: "pointer",
                    }}>
                    Remove
                  </button>
                </li>
              ))}
          </ul>
        </div>
        <div>
          <h3>
            Outfielders ({roleCounts.outfielder}/{roleLimits.outfielder})
          </h3>
          <ul>
            {selectedPlayers
              .filter(
                (player) =>
                  player.role_info.primary_role.toLowerCase() === "outfielder"
              )
              .map((player) => (
                <li
                  key={player.player_id}
                  style={{ display: "flex", alignItems: "center" }}>
                  <span>{player.basic_info.name}</span>
                  <button
                    onClick={() => handleRemovePlayer(player.player_id)}
                    style={{
                      marginLeft: "10px",
                      padding: "5px 10px",
                      border: "1px solid #ddd",
                      backgroundColor: "#f9f9f9",
                      cursor: "pointer",
                    }}>
                    Remove
                  </button>
                </li>
              ))}
          </ul>
        </div>
        <button
          onClick={handleSubmit}
          style={{
            marginTop: "20px",
            padding: "10px",
            backgroundColor: "#4CAF50",
            color: "white",
            border: "none",
            cursor: "pointer",
          }}>
          Submit Deck
        </button>
      </div>
      {previewPlayer && (
        <div className="fixed bottom-0 right-0 m-4">
          <Card player={previewPlayer} /> {/* Render Card component */}
        </div>
      )}
    </div>
  );
};

const headerStyle = {
  backgroundColor: "#f2f2f2",
  padding: "5px",
  border: "1px solid #ddd",
  textAlign: "left" as const,
};

const rowStyle = {
  backgroundColor: "#fff",
  borderBottom: "1px solid #ddd",
};

const cellStyle = {
  padding: "5px",
  border: "1px solid #ddd",
};

export default CreateDeck;
