import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";
import "./styles/index.css";
import { debugLog } from "./utils/debugLog";

// #region agent log
window.addEventListener("error", (event) => {
  debugLog("main.tsx:global-error", "window error", {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    stack: event.error instanceof Error ? event.error.stack : undefined
  }, "A");
});
window.addEventListener("unhandledrejection", (event) => {
  debugLog("main.tsx:unhandled-rejection", "unhandled promise rejection", {
    reason: event.reason instanceof Error ? event.reason.message : String(event.reason),
    stack: event.reason instanceof Error ? event.reason.stack : undefined
  }, "E");
});
// #endregion

if ("scrollRestoration" in history) {
  history.scrollRestoration = "manual";
}

// Single React mount point for the Vite frontend app.
createRoot(document.getElementById("root")!).render(<App />);