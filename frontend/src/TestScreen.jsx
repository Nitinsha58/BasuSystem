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
	const totalQuestions = attemptData.total_questions;

	// Wall-clock deadline — immune to DevTools interval pausing
	const examEndRef = useRef(Date.now() + attemptData.time_remaining * 1000);

	const [currentIndex, setCurrentIndex] = useState(0);
	const [questionCache, setQuestionCache] = useState({}); // { index: {question, already_selected} }
	const [answers, setAnswers] = useState({}); // { index: 'A'|'B'|... }
	const [timeLeft, setTimeLeft] = useState(attemptData.time_remaining);
	const [submitting, setSubmitting] = useState(false);
	const [error, setError] = useState("");
	const [expiredError, setExpiredError] = useState(false);
	const [confirmOpen, setConfirmOpen] = useState(false);

	// Overlay states
	const [fsWarning, setFsWarning] = useState(false); // fullscreen warning overlay
	const [tabWarning, setTabWarning] = useState(false); // tab-switch warning banner

	const autoSubmitted = useRef(false);
	const tabSwitchCount = useRef(0);
	const fullscreenExitCount = useRef(0);
	const pendingSaveIndex = useRef(null); // index being saved async

	// Stable refs — lets event listeners registered once always read latest state
	const answersRef = useRef(answers);
	const doSubmitRef = useRef(null);
	const logEventRef = useRef(null);

	// ─── Load a question ────────────────────────────────────────────────────────
	const loadQuestion = useCallback(
		(index) => {
			if (questionCache[index]) return; // already cached
			fetch(`/api/sat/question/${token}/${index}/`)
				.then((r) => r.json())
				.then((data) => {
					if (data.error) return; // silently ignore; will show on render
					setQuestionCache((prev) => ({ ...prev, [index]: data }));
					// Seed answer from server-stored response (in case of refresh)
					if (data.already_selected) {
						setAnswers((prev) => ({
							...prev,
							[index]: data.already_selected,
						}));
					}
				})
				.catch(() => {});
		},
		[token, questionCache],
	);

	// Load first question on mount, and pre-fetch next
	useEffect(() => {
		loadQuestion(0);
	}, []);

	useEffect(() => {
		loadQuestion(currentIndex);
		// Pre-fetch adjacent questions
		if (currentIndex + 1 < totalQuestions) loadQuestion(currentIndex + 1);
	}, [currentIndex]);

	// ─── Wall-clock timer ───────────────────────────────────────────────────────
	useEffect(() => {
		const id = setInterval(() => {
			const remaining = Math.max(
				0,
				Math.round((examEndRef.current - Date.now()) / 1000),
			);
			setTimeLeft(remaining);
		}, 500);
		return () => clearInterval(id);
	}, []);

	// ─── Auto-submit ─────────────────────────────────────────────────────────────
	const doSubmit = useCallback(
		(currentAnswers, isAuto = false) => {
			if (autoSubmitted.current) return;
			autoSubmitted.current = true;
			setSubmitting(true);
			setConfirmOpen(false);

			const payload = Array.from({ length: totalQuestions }, (_, i) => ({
				question_id: questionCache[i]?.question?.id ?? null,
				selected: currentAnswers[i] ?? null,
			})).filter((item) => item.question_id !== null);

			fetch(`/api/sat/submit/${token}/`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					"X-CSRFToken": getCookie("csrftoken"),
				},
				body: JSON.stringify({
					answers: payload,
					auto_submitted: isAuto,
				}),
			})
				.then((r) => {
					if (r.status === 403) {
						setExpiredError(true);
						setSubmitting(false);
						autoSubmitted.current = false;
						return null;
					}
					return r.json();
				})
				.then((data) => {
					if (!data) return;
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
		[token, totalQuestions, questionCache, onSubmit],
	);

	useEffect(() => {
		if (timeLeft === 0 && !autoSubmitted.current) {
			doSubmit(answers, true);
		}
	}, [timeLeft]);

	// ─── Progressive save ────────────────────────────────────────────────────────
	const saveAnswer = useCallback(
		(index, selected) => {
			fetch(`/api/sat/answer/${token}/`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					"X-CSRFToken": getCookie("csrftoken"),
				},
				body: JSON.stringify({
					question_index: index,
					selected: selected ?? "",
				}),
			}).catch(() => {}); // best-effort; silent fail
		},
		[token],
	);

	// ─── Log events (tab switch / fullscreen) ────────────────────────────────────
	const logEvent = useCallback(
		(event) => {
			fetch(`/api/sat/log-event/${token}/`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					"X-CSRFToken": getCookie("csrftoken"),
				},
				body: JSON.stringify({ event }),
			})
				.then((r) => r.json())
				.then((data) => {
					tabSwitchCount.current =
						data.tab_switch_count ?? tabSwitchCount.current;
					fullscreenExitCount.current =
						data.fullscreen_exit_count ??
						fullscreenExitCount.current;
				})
				.catch(() => {});
		},
		[token],
	);

	// Keep stable refs in sync — event listeners always read the latest values
	// without needing to re-register (which would re-trigger cleanup & exitFullscreen)
	useEffect(() => {
		answersRef.current = answers;
	}, [answers]);
	useEffect(() => {
		doSubmitRef.current = doSubmit;
	}, [doSubmit]);
	useEffect(() => {
		logEventRef.current = logEvent;
	}, [logEvent]);

	// ─── Tab-switch detection (registered ONCE via stable refs) ──────────────────
	useEffect(() => {
		const handleVisibility = () => {
			if (!document.hidden) {
				// Tab is visible again — dismiss warning if only one offence so far
				setTabWarning((prev) => prev && tabSwitchCount.current < 2);
				return;
			}
			tabSwitchCount.current += 1;
			logEventRef.current?.("tab_switch");
			if (tabSwitchCount.current >= 2) {
				doSubmitRef.current?.(answersRef.current, true);
			} else {
				setTabWarning(true);
			}
		};
		document.addEventListener("visibilitychange", handleVisibility);
		return () =>
			document.removeEventListener("visibilitychange", handleVisibility);
	}, []); // empty — uses refs, never re-registers mid-test

	// ─── Fullscreen enforcement (registered ONCE via stable refs) ────────────────
	useEffect(() => {
		document.documentElement.requestFullscreen?.().catch(() => {});

		const handleFsChange = () => {
			if (document.fullscreenElement) {
				setFsWarning(false); // re-entered
				return;
			}
			// Exited fullscreen
			fullscreenExitCount.current += 1;
			logEventRef.current?.("fullscreen_exit");
			if (fullscreenExitCount.current >= 2) {
				doSubmitRef.current?.(answersRef.current, true);
			} else {
				setFsWarning(true);
			}
		};
		document.addEventListener("fullscreenchange", handleFsChange);
		return () => {
			document.removeEventListener("fullscreenchange", handleFsChange);
			// exitFullscreen only on true unmount (test done), never mid-test
			if (document.fullscreenElement) document.exitFullscreen?.();
		};
	}, []); // empty — never re-registers, so cleanup never fires mid-test

	function reenterFullscreen() {
		document.documentElement.requestFullscreen?.().catch(() => {});
		setFsWarning(false);
	}

	// ─── Copy-paste / DevTools deterrence ────────────────────────────────────────
	useEffect(() => {
		const blockKey = (e) => {
			// Block F12, Ctrl+Shift+I, Ctrl+U, Ctrl+S
			if (
				e.key === "F12" ||
				(e.ctrlKey && e.shiftKey && e.key === "I") ||
				(e.ctrlKey && e.key === "u") ||
				(e.ctrlKey && e.key === "s")
			) {
				e.preventDefault();
			}
		};
		document.addEventListener("keydown", blockKey);
		return () => document.removeEventListener("keydown", blockKey);
	}, []);

	// ─── Navigation ──────────────────────────────────────────────────────────────
	function navigateTo(index) {
		// Save current answer before leaving
		if (answers[currentIndex] !== undefined) {
			saveAnswer(currentIndex, answers[currentIndex]);
		}
		setCurrentIndex(index);
	}

	function handleSelect(index, option) {
		setAnswers((prev) => ({ ...prev, [index]: option }));
	}

	// ─── Render helpers ──────────────────────────────────────────────────────────
	const answeredCount = Object.keys(answers).length;
	const urgent = timeLeft <= 300;
	const current = questionCache[currentIndex];

	if (expiredError) {
		return (
			<div
				style={{
					minHeight: "100svh",
					display: "flex",
					alignItems: "center",
					justifyContent: "center",
					flexDirection: "column",
					gap: "16px",
					padding: "24px",
					textAlign: "center",
				}}>
				<div style={{ fontSize: "48px" }}>⏰</div>
				<h2
					style={{
						fontSize: "22px",
						fontWeight: 700,
						color: "var(--red)",
					}}>
					Test Session Expired
				</h2>
				<p style={{ color: "var(--muted)", maxWidth: "360px" }}>
					Your submission arrived after the allowed window. Please
					contact your test coordinator.
				</p>
			</div>
		);
	}

	return (
		<div
			style={{
				display: "flex",
				flexDirection: "column",
				minHeight: "100svh",
			}}
			onContextMenu={(e) => e.preventDefault()}
			onCopy={(e) => e.preventDefault()}
			onPaste={(e) => e.preventDefault()}
			onCut={(e) => e.preventDefault()}>
			{/* Tab-switch warning banner */}
			{tabWarning && (
				<div
					style={{
						position: "fixed",
						top: 0,
						left: 0,
						right: 0,
						zIndex: 300,
						background: "#fef3c7",
						borderBottom: "2px solid #f59e0b",
						padding: "10px 20px",
						textAlign: "center",
						fontSize: "14px",
						fontWeight: 600,
						color: "#92400e",
					}}>
					⚠️ Tab switching detected. Switching again will auto-submit
					your test.
				</div>
			)}

			{/* Fullscreen warning overlay */}
			{fsWarning && (
				<div
					style={{
						position: "fixed",
						inset: 0,
						background: "rgba(0,0,0,.75)",
						zIndex: 400,
						display: "flex",
						alignItems: "center",
						justifyContent: "center",
					}}>
					<div
						style={{
							background: "#fff",
							borderRadius: "16px",
							padding: "36px 32px",
							maxWidth: "400px",
							textAlign: "center",
						}}>
						<div style={{ fontSize: "48px", marginBottom: "16px" }}>
							🖥️
						</div>
						<h2
							style={{
								fontSize: "20px",
								fontWeight: 700,
								marginBottom: "8px",
								color: "var(--red)",
							}}>
							Fullscreen Required
						</h2>
						<p
							style={{
								fontSize: "14px",
								color: "var(--muted)",
								marginBottom: "24px",
							}}>
							You exited fullscreen mode. This is your first
							warning — exiting again will automatically submit
							your test.
						</p>
						<button
							className="btn-primary"
							onClick={reenterFullscreen}>
							Re-enter Fullscreen →
						</button>
					</div>
				</div>
			)}

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
					{paperData.title}
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
					{answeredCount}/{totalQuestions} answered
				</div>
			</div>

			{/* Question area */}
			<div
				style={{
					flex: 1,
					padding: "24px 16px 160px",
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

				{!current ? (
					<div
						style={{
							textAlign: "center",
							padding: "60px 0",
							color: "var(--muted)",
						}}>
						Loading question…
					</div>
				) : (
					<QuestionCard
						index={currentIndex}
						total={totalQuestions}
						data={current}
						selected={answers[currentIndex] ?? null}
						onSelect={(opt) => handleSelect(currentIndex, opt)}
					/>
				)}
			</div>

			{/* Sticky bottom: question map + navigation + submit */}
			<div
				style={{
					position: "fixed",
					bottom: 0,
					left: 0,
					right: 0,
					zIndex: 100,
					background: "rgba(255,255,255,.97)",
					borderTop: "1px solid var(--border)",
					padding: "10px 16px 12px",
					backdropFilter: "blur(8px)",
				}}>
				{/* Question map */}
				<div
					style={{
						display: "flex",
						flexWrap: "wrap",
						gap: "5px",
						justifyContent: "center",
						marginBottom: "10px",
						maxWidth: "720px",
						margin: "0 auto 10px",
					}}>
					{Array.from({ length: totalQuestions }, (_, i) => {
						const answered = answers[i] !== undefined;
						const isCurrent = i === currentIndex;
						return (
							<button
								key={i}
								onClick={() => navigateTo(i)}
								title={`Q${i + 1}`}
								style={{
									width: "28px",
									height: "28px",
									borderRadius: "50%",
									border: isCurrent
										? "2px solid var(--navy)"
										: "none",
									background: isCurrent
										? "var(--navy)"
										: answered
											? "var(--green)"
											: "var(--border)",
									color:
										isCurrent || answered
											? "#fff"
											: "var(--muted)",
									fontSize: "11px",
									fontWeight: 700,
									padding: 0,
									cursor: "pointer",
									transition: "all .1s",
								}}>
								{i + 1}
							</button>
						);
					})}
				</div>

				{/* Nav + submit row */}
				<div
					style={{
						display: "flex",
						justifyContent: "space-between",
						alignItems: "center",
						maxWidth: "720px",
						margin: "0 auto",
						gap: "8px",
					}}>
					<button
						className="btn-outline"
						disabled={currentIndex === 0}
						onClick={() => navigateTo(currentIndex - 1)}
						style={{ padding: "8px 18px" }}>
						← Prev
					</button>

					<div
						style={{
							fontSize: "13px",
							color: "var(--muted)",
							textAlign: "center",
						}}>
						{currentIndex + 1} / {totalQuestions}
					</div>

					{currentIndex < totalQuestions - 1 ? (
						<button
							className="btn-outline"
							onClick={() => navigateTo(currentIndex + 1)}
							style={{ padding: "8px 18px" }}>
							Next →
						</button>
					) : (
						<button
							className="btn-primary"
							onClick={() => setConfirmOpen(true)}
							disabled={submitting}
							style={{ padding: "8px 18px" }}>
							{submitting ? "Submitting…" : "Submit Test"}
						</button>
					)}
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
							of <strong>{totalQuestions}</strong> questions.
						</p>
						{answeredCount < totalQuestions && (
							<p
								style={{
									fontSize: "13px",
									color: "var(--red)",
									marginBottom: "20px",
								}}>
								{totalQuestions - answeredCount} unanswered
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
								onClick={() => doSubmit(answers, false)}>
								Yes, submit
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}

// ─── QuestionCard sub-component ──────────────────────────────────────────────
function QuestionCard({ index, total, data, selected, onSelect }) {
	const { question } = data;
	const answered = !!selected;

	return (
		<div
			style={{
				background: "var(--card)",
				border:
					"1px solid " +
					(answered ? "var(--green)" : "var(--border)"),
				borderRadius: "12px",
				padding: "20px 22px",
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
						background: answered ? "var(--green)" : "var(--navy)",
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
					{index + 1}
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
								background: "rgba(13,27,62,.08)",
								color: "var(--navy)",
							}}>
							{question.subject_tag}
						</span>
						<span
							style={{
								fontSize: "11px",
								fontWeight: 600,
								padding: "2px 8px",
								borderRadius: "4px",
								background:
									question.difficulty === "L1"
										? "#dcfce7"
										: question.difficulty === "L2"
											? "#fef9c3"
											: "#fee2e2",
								color:
									question.difficulty === "L1"
										? "var(--green)"
										: question.difficulty === "L2"
											? "#a16207"
											: "var(--red)",
							}}>
							{question.difficulty}
						</span>
					</div>
					<div
						style={{
							fontSize: "15px",
							lineHeight: "1.6",
							color: "var(--text)",
						}}>
						<ReactMarkdown>{question.text}</ReactMarkdown>
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
					const text = question["option_" + opt.toLowerCase()];
					if (!text) return null;
					const isSelected = selected === opt;
					return (
						<button
							key={opt}
							onClick={() => onSelect(opt)}
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
								fontWeight: isSelected ? 600 : 400,
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
									color: isSelected ? "#fff" : "var(--muted)",
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
}
