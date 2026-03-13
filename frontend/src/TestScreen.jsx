import { useState, useEffect, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";

function fmtTime(secs) {
	const m = Math.floor(secs / 60);
	const s = secs % 60;
	return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function getCookie(name) {
	const v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
	return v ? v.pop() : "";
}

export default function TestScreen({
	token,
	paperData,
	attemptData,
	onSubmit,
}) {
	const { paper } = paperData;
	const questions = paper.questions;
	const [answers, setAnswers] = useState({}); // { qId: 'A'|'B'|'C'|'D' }
	const [timeLeft, setTimeLeft] = useState(attemptData.time_remaining);
	const [submitting, setSubmitting] = useState(false);
	const [error, setError] = useState("");
	const [confirmOpen, setConfirmOpen] = useState(false);
	const questionRefs = useRef([]);
	const autoSubmitted = useRef(false);

	// Countdown timer
	useEffect(() => {
		if (timeLeft <= 0) return;
		const id = setInterval(
			() => setTimeLeft((t) => Math.max(0, t - 1)),
			1000,
		);
		return () => clearInterval(id);
	}, []);

	// Auto-submit when timer hits 0
	const doSubmit = useCallback(
		(currentAnswers) => {
			if (autoSubmitted.current) return;
			autoSubmitted.current = true;
			setSubmitting(true);
			const payload = questions.map((q) => ({
				question_id: q.id,
				selected: currentAnswers[q.id] ?? null,
			}));
			fetch(`/api/sat/submit/${token}/`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					"X-CSRFToken": getCookie("csrftoken"),
				},
				body: JSON.stringify({ answers: payload }),
			})
				.then((r) => r.json())
				.then((data) => {
					if (data.error) {
						setError(data.error);
						setSubmitting(false);
						autoSubmitted.current = false;
					} else {
						onSubmit(data);
					}
				})
				.catch(() => {
					setError("Submission failed. Please retry.");
					setSubmitting(false);
					autoSubmitted.current = false;
				});
		},
		[token, questions, onSubmit],
	);

	useEffect(() => {
		if (timeLeft === 0 && !autoSubmitted.current) {
			doSubmit(answers);
		}
	}, [timeLeft]);

	function handleSelect(qId, option) {
		setAnswers((prev) => ({ ...prev, [qId]: option }));
	}

	function scrollToQ(idx) {
		questionRefs.current[idx]?.scrollIntoView({
			behavior: "smooth",
			block: "start",
		});
	}

	const answeredCount = Object.keys(answers).length;
	const urgent = timeLeft <= 300; // last 5 mins

	return (
		<div
			style={{
				display: "flex",
				flexDirection: "column",
				minHeight: "100svh",
			}}>
			{/* Sticky top bar */}
			<div
				style={{
					position: "sticky",
					top: 0,
					zIndex: 100,
					background: urgent ? "#fef2f2" : "var(--navy)",
					borderBottom:
						"1px solid " + (urgent ? "#fca5a5" : "transparent"),
					padding: "10px 20px",
					display: "flex",
					alignItems: "center",
					justifyContent: "space-between",
					gap: "16px",
				}}>
				<div
					style={{
						color: urgent ? "var(--red)" : "rgba(255,255,255,.8)",
						fontSize: "13px",
						fontWeight: 500,
					}}>
					{paper.title}
				</div>
				<div
					style={{
						fontFamily: "'IBM Plex Mono', monospace",
						fontSize: "22px",
						fontWeight: 700,
						color: urgent ? "var(--red)" : "#fff",
						letterSpacing: "2px",
					}}>
					{fmtTime(timeLeft)}
				</div>
				<div
					style={{
						color: urgent ? "var(--muted)" : "rgba(255,255,255,.7)",
						fontSize: "13px",
					}}>
					{answeredCount}/{questions.length} answered
				</div>
			</div>

			{/* Questions */}
			<div
				style={{
					flex: 1,
					padding: "24px 16px 140px",
					maxWidth: "720px",
					margin: "0 auto",
					width: "100%",
				}}>
				{error && (
					<div
						style={{
							background: "#fef2f2",
							border: "1px solid #fca5a5",
							color: "var(--red)",
							borderRadius: "8px",
							padding: "12px 16px",
							fontSize: "14px",
							marginBottom: "16px",
						}}>
						{error}
					</div>
				)}
				{questions.map((q, idx) => {
					const selected = answers[q.id];
					const answered = !!selected;
					return (
						<div
							key={q.id}
							ref={(el) => (questionRefs.current[idx] = el)}
							style={{
								background: "var(--card)",
								border:
									"1px solid " +
									(answered
										? "var(--green)"
										: "var(--border)"),
								borderRadius: "12px",
								padding: "20px 22px",
								marginBottom: "16px",
								scrollMarginTop: "70px",
							}}>
							{/* Q header */}
							<div
								style={{
									display: "flex",
									alignItems: "flex-start",
									gap: "12px",
									marginBottom: "14px",
								}}>
								<span
									style={{
										background: answered
											? "var(--green)"
											: "var(--navy)",
										color: "#fff",
										borderRadius: "6px",
										width: "28px",
										height: "28px",
										display: "flex",
										alignItems: "center",
										justifyContent: "center",
										fontSize: "13px",
										fontWeight: 700,
										flexShrink: 0,
									}}>
									{idx + 1}
								</span>
								<div style={{ flex: 1 }}>
									<div
										style={{
											display: "flex",
											gap: "6px",
											marginBottom: "8px",
											flexWrap: "wrap",
										}}>
										<span
											style={{
												fontSize: "11px",
												fontWeight: 600,
												padding: "2px 8px",
												borderRadius: "4px",
												background:
													"rgba(13,27,62,.08)",
												color: "var(--navy)",
											}}>
											{q.subject_tag}
										</span>
										<span
											style={{
												fontSize: "11px",
												fontWeight: 600,
												padding: "2px 8px",
												borderRadius: "4px",
												background:
													q.difficulty === "L1"
														? "#dcfce7"
														: q.difficulty === "L2"
															? "#fef9c3"
															: "#fee2e2",
												color:
													q.difficulty === "L1"
														? "var(--green)"
														: q.difficulty === "L2"
															? "#a16207"
															: "var(--red)",
											}}>
											{q.difficulty}
										</span>
									</div>
									<div
										style={{
											fontSize: "15px",
											lineHeight: "1.6",
											color: "var(--text)",
										}}>
										<ReactMarkdown>{q.text}</ReactMarkdown>
									</div>
								</div>
							</div>

							{/* Options */}
							<div
								style={{
									display: "flex",
									flexDirection: "column",
									gap: "8px",
								}}>
								{["A", "B", "C", "D", "E"].map((opt) => {
									const text =
										q["option_" + opt.toLowerCase()];
									if (!text) return null;
									const isSelected = selected === opt;
									return (
										<button
											key={opt}
											onClick={() =>
												handleSelect(q.id, opt)
											}
											style={{
												textAlign: "left",
												padding: "10px 14px",
												borderRadius: "8px",
												border:
													"1.5px solid " +
													(isSelected
														? "var(--navy)"
														: "var(--border)"),
												background: isSelected
													? "rgba(13,27,62,.07)"
													: "#fff",
												color: "var(--text)",
												fontSize: "14px",
												fontWeight: isSelected
													? 600
													: 400,
												display: "flex",
												gap: "10px",
												alignItems: "flex-start",
												lineHeight: "1.5",
												transition: "all .15s",
											}}>
											<span
												style={{
													minWidth: "22px",
													height: "22px",
													borderRadius: "50%",
													background: isSelected
														? "var(--navy)"
														: "transparent",
													border:
														"1.5px solid " +
														(isSelected
															? "var(--navy)"
															: "var(--border)"),
													color: isSelected
														? "#fff"
														: "var(--muted)",
													display: "flex",
													alignItems: "center",
													justifyContent: "center",
													fontSize: "12px",
													fontWeight: 700,
													flexShrink: 0,
													marginTop: "1px",
												}}>
												{opt}
											</span>
											{text}
										</button>
									);
								})}
							</div>
						</div>
					);
				})}
			</div>

			{/* Sticky bottom: dot nav + submit */}
			<div
				style={{
					position: "fixed",
					bottom: 0,
					left: 0,
					right: 0,
					zIndex: 100,
					background: "rgba(255,255,255,.97)",
					borderTop: "1px solid var(--border)",
					padding: "12px 16px",
					backdropFilter: "blur(8px)",
				}}>
				{/* Dot navigation */}
				<div
					style={{
						display: "flex",
						flexWrap: "wrap",
						gap: "6px",
						justifyContent: "center",
						marginBottom: "12px",
						maxWidth: "720px",
						margin: "0 auto 12px",
					}}>
					{questions.map((q, idx) => {
						const answered = !!answers[q.id];
						return (
							<button
								key={q.id}
								onClick={() => scrollToQ(idx)}
								title={`Q${idx + 1}`}
								style={{
									width: "28px",
									height: "28px",
									borderRadius: "50%",
									border: "none",
									background: answered
										? "var(--green)"
										: "var(--border)",
									color: answered ? "#fff" : "var(--muted)",
									fontSize: "11px",
									fontWeight: 700,
									padding: 0,
									cursor: "pointer",
									transition: "all .1s",
								}}>
								{idx + 1}
							</button>
						);
					})}
				</div>

				{/* Submit row */}
				<div
					style={{
						display: "flex",
						justifyContent: "center",
						gap: "12px",
						maxWidth: "720px",
						margin: "0 auto",
					}}>
					<div
						style={{
							fontSize: "13px",
							color: "var(--muted)",
							display: "flex",
							alignItems: "center",
							gap: "8px",
						}}>
						<span
							style={{
								width: "10px",
								height: "10px",
								borderRadius: "50%",
								background: "var(--green)",
								display: "inline-block",
							}}
						/>
						{answeredCount} answered
						<span
							style={{
								width: "10px",
								height: "10px",
								borderRadius: "50%",
								background: "var(--border)",
								display: "inline-block",
								marginLeft: "8px",
							}}
						/>
						{questions.length - answeredCount} unanswered
					</div>
					<button
						className="btn-primary"
						onClick={() => setConfirmOpen(true)}
						disabled={submitting}
						style={{ padding: "10px 28px" }}>
						{submitting ? "Submitting…" : "Submit Test"}
					</button>
				</div>
			</div>

			{/* Confirm modal */}
			{confirmOpen && (
				<div
					style={{
						position: "fixed",
						inset: 0,
						background: "rgba(0,0,0,.45)",
						display: "flex",
						alignItems: "center",
						justifyContent: "center",
						zIndex: 200,
						padding: "16px",
					}}>
					<div
						style={{
							background: "#fff",
							borderRadius: "16px",
							padding: "32px 28px",
							maxWidth: "380px",
							width: "100%",
							textAlign: "center",
						}}>
						<div style={{ fontSize: "36px", marginBottom: "16px" }}>
							📝
						</div>
						<h2
							style={{
								fontSize: "18px",
								fontWeight: 600,
								marginBottom: "8px",
							}}>
							Submit test?
						</h2>
						<p
							style={{
								fontSize: "14px",
								color: "var(--muted)",
								marginBottom: "8px",
							}}>
							You have answered <strong>{answeredCount}</strong>{" "}
							of <strong>{questions.length}</strong> questions.
						</p>
						{answeredCount < questions.length && (
							<p
								style={{
									fontSize: "13px",
									color: "var(--red)",
									marginBottom: "20px",
								}}>
								{questions.length - answeredCount} unanswered
								question(s) will score 0.
							</p>
						)}
						<div
							style={{
								display: "flex",
								gap: "10px",
								justifyContent: "center",
								marginTop: "20px",
							}}>
							<button
								className="btn-outline"
								onClick={() => setConfirmOpen(false)}>
								Go back
							</button>
							<button
								className="btn-primary"
								onClick={() => {
									setConfirmOpen(false);
									doSubmit(answers);
								}}>
								Yes, submit
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
