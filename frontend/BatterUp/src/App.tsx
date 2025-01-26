import { useState, useEffect } from "react";
import "./index.css";
import LoginScreen from "./LoginScreen";
import { BrowserRouter as Router, Route } from "react-router-dom";

function App() {
  const [image, setImage] = useState("src/assets/MLB.png");
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
    <div className="App">
      <LoginScreen />
    </div>
  );
}

export default App;
