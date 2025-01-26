import { useState, useEffect } from "react";
import "./index.css";

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
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  );
}

export default App;
