import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";
import "./styles/index.css";

if ("scrollRestoration" in history) {
  history.scrollRestoration = "manual";
}

// Single React mount point for the Vite frontend app.
createRoot(document.getElementById("root")!).render(<App />);