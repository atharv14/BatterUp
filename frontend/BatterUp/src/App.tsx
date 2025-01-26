import { Routes, Route } from "react-router-dom";
import HomeScreen from "./HomeScreen"; // Your main/home component
import LoginScreen from "./LoginScreen"; // or wherever your login component is

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeScreen />} />
      <Route path="/login" element={<LoginScreen />} />
    </Routes>
  );
}

export default App;
