import { useState, useEffect } from "react";

const s = {
	page: {
		minHeight: "100svh",
		display: "flex",
		alignItems: "center",
		justifyContent: "center",
		padding: "24px 16px",
		background: "var(--bg)",
	},
	card: {
		background: "var(--card)",
		borderRadius: "16px",
		border: "1px solid var(--border)",
		padding: "40px 36px",
		maxWidth: "520px",
		width: "100%",
		boxShadow: "0 4px 24px rgba(13,27,62,.08)",
	},
	header: {
		background: "var(--navy)",
		borderRadius: "12px",
		padding: "20px 24px",
		marginBottom: "28px",
		color: "#fff",
	},
	badge: {
		display: "inline-block",
		background: "var(--gold)",
		color: "#fff",
		fontSize: "11px",
		fontWeight: 600,
		letterSpacing: ".8px",
		textTransform: "uppercase",
		padding: "3px 10px",
		borderRadius: "20px",
		marginBottom: "10px",
	},
	title: {
		fontSize: "22px",
		fontWeight: 600,
		marginBottom: "4px",
	},
	sub: {
		fontSize: "13px",
		opacity: 0.75,
	},
	infoGrid: {
		display: "grid",
		gridTemplateColumns: "1fr 1fr",
		gap: "10px",
		marginBottom: "24px",
	},
	infoCell: {
		background: "var(--bg)",
		borderRadius: "8px",
		padding: "12px 14px",
		border: "1px solid var(--border)",
	},
	infoLabel: {
		fontSize: "11px",
		fontWeight: 600,
		color: "var(--muted)",
		textTransform: "uppercase",
		letterSpacing: ".6px",
		marginBottom: "4px",
	},
	infoVal: {
		fontSize: "16px",
		fontWeight: 600,
		color: "var(--text)",
	},
	studentRow: {
		display: "flex",
		alignItems: "center",
		gap: "12px",
		background: "rgba(13,27,62,.04)",
		border: "1px solid rgba(13,27,62,.12)",
		borderRadius: "10px",
		padding: "12px 16px",
		marginBottom: "24px",
	},
	avatar: {
		width: "40px",
		height: "40px",
		borderRadius: "50%",
		background: "var(--navy)",
		color: "#fff",
		display: "flex",
		alignItems: "center",
		justifyContent: "center",
		fontWeight: 700,
		fontSize: "16px",
		flexShrink: 0,
	},
	rules: {
		marginBottom: "28px",
	},
	rulesTitle: {
		fontSize: "13px",
		fontWeight: 600,
		color: "var(--muted)",
		textTransform: "uppercase",
		letterSpacing: ".6px",
		marginBottom: "10px",
	},
	rule: {
		display: "flex",
		gap: "10px",
		alignItems: "flex-start",
		padding: "7px 0",
		borderBottom: "1px solid var(--border)",
		fontSize: "14px",
		color: "var(--text)",
		lineHeight: "20px",
	},
	dot: {
		width: "6px",
		height: "6px",
		borderRadius: "50%",
		background: "var(--gold)",
		marginTop: "7px",
		flexShrink: 0,
	},
	error: {
		background: "#fef2f2",
		border: "1px solid #fca5a5",
		color: "var(--red)",
		borderRadius: "8px",
		padding: "12px 16px",
		fontSize: "14px",
		marginBottom: "16px",
	},
};

export default function InfoScreen({ token, onPaperLoaded, onStart }) {
	const [paper, setPaper] = useState(null);
	const [studentName, setStudentName] = useState("");
	const [loading, setLoading] = useState(true);
	const [starting, setStarting] = useState(false);
	const [error, setError] = useState("");

	useEffect(() => {
		fetch(`/api/sat/paper/${token}/`)
			.then((r) => r.json())
			.then((data) => {
				if (data.error) {
					if (data.submitted) {
						setError("This test has already been submitted.");
					} else {
						setError(data.error);
					}
				} else {
					// API now returns flat metadata (no paper.questions nested object)
					setPaper(data);
					setStudentName(data.student_name);
					onPaperLoaded(data);
				}
				setLoading(false);
			})
			.catch(() => {
				setError(
					"Could not connect to server. Please check your connection.",
				);
				setLoading(false);
			});
	}, [token]);

	function handleStart() {
		setStarting(true);
		setError("");
		fetch(`/api/sat/start/${token}/`, {
			method: "POST",
			headers: { "X-CSRFToken": getCookie("csrftoken") },
		})
			.then((r) => r.json())
			.then((data) => {
				if (data.error) {
					setError(data.error);
					setStarting(false);
				} else {
					onStart(data);
				}
			})
			.catch(() => {
				setError("Failed to start test. Please try again.");
				setStarting(false);
			});
	}

	if (loading) {
		return (
			<div style={s.page}>
				<div style={{ textAlign: "center", color: "var(--muted)" }}>
					<div style={{ fontSize: "32px", marginBottom: "12px" }}>
						⏳
					</div>
					Loading test…
				</div>
			</div>
		);
	}

	if (!paper && error) {
		return (
			<div style={s.page}>
				<div style={{ ...s.card, textAlign: "center" }}>
					<div style={{ fontSize: "40px", marginBottom: "16px" }}>
						🚫
					</div>
					<p
						style={{
							color: "var(--red)",
							fontSize: "16px",
							fontWeight: 500,
						}}>
						{error}
					</p>
				</div>
			</div>
		);
	}

	const initials = studentName
		.split(" ")
		.map((w) => w[0])
		.slice(0, 2)
		.join("")
		.toUpperCase();
	const qCount = paper.total_questions ?? 0;
	const totalMins = paper.time_limit;

	return (
		<div style={s.page}>
			<div style={s.card}>
				{/* Header */}
				<div style={s.header}>
					<div style={s.badge}>Scholarship Aptitude Test</div>
					<div style={s.title}>{paper.title}</div>
					<div style={s.sub}>Class {paper.class_label}</div>
				</div>

				{/* Student identity (read-only — proctor verifies) */}
				<div style={s.studentRow}>
					<div style={s.avatar}>{initials}</div>
					<div>
						<div style={{ fontSize: "15px", fontWeight: 600 }}>
							{studentName}
						</div>
						<div
							style={{ fontSize: "12px", color: "var(--muted)" }}>
							Identity verified by proctor
						</div>
					</div>
				</div>

				{/* Test info */}
				<div style={s.infoGrid}>
					<div style={s.infoCell}>
						<div style={s.infoLabel}>Questions</div>
						<div style={s.infoVal}>{qCount}</div>
					</div>
					<div style={s.infoCell}>
						<div style={s.infoLabel}>Time limit</div>
						<div style={s.infoVal}>{totalMins} min</div>
					</div>
					<div style={s.infoCell}>
						<div style={s.infoLabel}>Correct answer</div>
						<div style={s.infoVal}>+{paper.marks_per_correct}</div>
					</div>
					<div style={s.infoCell}>
						<div style={s.infoLabel}>Wrong / Skip</div>
						<div style={s.infoVal}>0</div>
					</div>
				</div>

				{/* Rules */}
				<div style={s.rules}>
					<div style={s.rulesTitle}>Instructions</div>
					{[
						"The test will open in fullscreen — do not exit fullscreen during the test.",
						"Do not switch tabs or leave this window — the second violation will auto-submit.",
						"Each question has exactly one correct option.",
						"You can navigate freely and change any answer before submitting.",
						'The timer starts the moment you click "Start Test" and cannot be paused.',
						"Your answers are saved automatically as you navigate. Submit before time runs out.",
					].map((rule, i) => (
						<div key={i} style={s.rule}>
							<div style={s.dot} />
							{rule}
						</div>
					))}
				</div>

				{error && <div style={s.error}>{error}</div>}

				<button
					className="btn-primary"
					style={{ width: "100%", padding: "14px", fontSize: "16px" }}
					onClick={handleStart}
					disabled={starting}>
					{starting ? "Starting…" : "I'm ready — Start Test →"}
				</button>
			</div>
		</div>
	);
}

function getCookie(name) {
	const v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
	return v ? v.pop() : "";
}
