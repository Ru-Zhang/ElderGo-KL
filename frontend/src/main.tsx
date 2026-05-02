import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";
import "./styles/index.css";

// Single React mount point for the Vite frontend app.
createRoot(document.getElementById("root")!).render(<App />);