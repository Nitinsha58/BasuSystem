import { useState } from "react";
import InfoScreen from "./InfoScreen";
import TestScreen from "./TestScreen";
import SubmitScreen from "./SubmitScreen";

// SCREENS: info → test → submit
export default function App({ token }) {
	const [screen, setScreen] = useState("info");
	const [paperData, setPaperData] = useState(null); // { paper, student_name }
	const [attemptData, setAttemptData] = useState(null); // { attempt_id, time_remaining }
	const [resultData, setResultData] = useState(null); // { report_token, auto_release, ... }

	if (screen === "info") {
		return (
			<InfoScreen
				token={token}
				onPaperLoaded={(data) => setPaperData(data)}
				onStart={(data) => {
					setAttemptData(data);
					setScreen("test");
				}}
			/>
		);
	}
	if (screen === "test") {
		return (
			<TestScreen
				token={token}
				paperData={paperData}
				attemptData={attemptData}
				onSubmit={(data) => {
					setResultData(data);
					setScreen("submit");
				}}
			/>
		);
	}
	return <SubmitScreen token={token} resultData={resultData} />;
}
