import { useState, useEffect } from "react";
import { useAuth } from "../AuthContext"; // Import useAuth to get user info
import { useNavigate } from "react-router-dom"; // Redirect user on login click
import "../index.css";

function App() {
  const [image, setImage] = useState("src/assets/MLB.png");
  const { user, logout } = useAuth(); // Get logged-in user and logout function
  const [dropdownOpen, setDropdownOpen] = useState(false); // Manage dropdown state
  const navigate = useNavigate(); // Use for navigation

  console.log("Current User:", user);

  const handleCardCollectionClick = () => {
    navigate("/create-deck");
  };

  const Click = () => {
    setImage(
      image === "src/assets/MLB.png"
        ? "src/assets/event.png"
        : "src/assets/MLB.png"
    );
  };

  const slideshow = ["src/assets/baseball.jpg", "src/assets/dude.jpg"];
  const [imgIndex, setImgIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setImgIndex((prevIndex) => (prevIndex + 1) % slideshow.length);
    }, 20000);
    return () => clearInterval(interval);
  }, [slideshow.length]);

  return (
    <>
      <div
        style={{
          backgroundImage: `url(${slideshow[imgIndex]})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          height: "100vh",
          width: "100%",
        }}
        className="flex justify-center items-center">
        {/* User Profile Section - Now in the Top Left */}
        <div className="absolute top-0 left-0 m-6">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex flex-row items-center bg-custom-red rounded-lg p-4 shadow-lg shadow-slate-800 cursor-pointer">
            <img src="src/assets/pfp.png" className="w-12" />
            <h3 className="ml-3 text-lg font-bold text-white">
              {user ? user.displayName || user.email : "Guest"}
            </h3>
          </button>

          {/* Dropdown Menu - Show Login or Logout */}
          {dropdownOpen && (
            <div className="absolute top-full left-0 mt-2 bg-white shadow-lg rounded-lg p-2">
              {user ? (
                // If logged in, show Logout
                <button
                  onClick={logout}
                  className="block px-4 py-2 text-black hover:bg-gray-200 w-full text-left">
                  Logout
                </button>
              ) : (
                // If not logged in, show Login
                <button
                  onClick={() => navigate("/login")}
                  className="block px-4 py-2 text-black hover:bg-gray-200 w-full text-left">
                  Login
                </button>
              )}
            </div>
          )}
        </div>

        {/* Top Right Icons */}
        <div className="flex items-center absolute top-0 right-0 bg-custom-red rounded-lg p-4 m-8 shadow-lg shadow-slate-800">
          <button className="relative">
            <img src="src/assets/mailfill.png" className="w-12 mr-2" />
          </button>
          <button className="relative">
            <img src="src/assets/gearfill.png" className="w-12" />
          </button>
        </div>

        {/* Card Collection & Missions */}
        <div className="flex flex-col items-center align-middle absolute top-1/3 left-0 ml-8">
          <div className="bg-custom-blue border-solid border-white border-4 p-7 mb-4 rounded-lg shadow-lg shadow-slate-800">
            <button onClick={handleCardCollectionClick}>
              <h1 className="text-3xl text-red-700 font-bold">
                Card Collection
              </h1>
            </button>
          </div>

          <div className="bg-custom-blue border-solid border-white p-4 border-4 w-full rounded-lg shadow-lg shadow-slate-800">
            <button className="flex items-center">
              <img
                src="src/assets/baseballbat.png"
                className="w-12 ml-6 mr-6"
              />
              <h1 className="text-3xl text-custom-red font-bold">Missions</h1>
            </button>
          </div>
        </div>

        {/* Slideshow */}
        <div className="absolute top-2/3 left-8">
          <div className="flex flex-col items-center">
            <div>
              <button onClick={Click}>
                <img src={image} className="w-80" />
              </button>
            </div>
            <div className="flex flex-row justify-center mt-4">
              <div className="bg-slate-200 w-4 h-4 rounded-full shadow-lg shadow-slate-800 mr-2"></div>
              <div className="bg-slate-200 w-4 h-4 rounded-full shadow-lg shadow-slate-800"></div>
            </div>
          </div>
        </div>

        {/* Bottom Right Baseball Icon */}
        <div className="absolute bottom-0 right-0 mr-10">
          <button>
            <img src="src/assets/baseball.png" className="mb-16 w-56" />
          </button>
        </div>
      </div>
    </>
  );
}

export default App;
