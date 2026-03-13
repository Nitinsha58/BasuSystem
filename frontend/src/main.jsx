import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

const rootEl = document.getElementById("root");
const token = rootEl.dataset.token;
createRoot(rootEl).render(
	<StrictMode>
		<App token={token} />
	</StrictMode>,
);
