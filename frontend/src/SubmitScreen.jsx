import { useEffect } from "react";

export default function SubmitScreen({ resultData }) {
	const { total_marks, max_marks, percentage, auto_release, report_token } =
		resultData || {};

	// If auto_release is true, redirect to report after a short delay
	useEffect(() => {
		if (auto_release && report_token) {
			const timer = setTimeout(() => {
				window.location.href = `/sat/report/${report_token}/`;
			}, 3000);
			return () => clearTimeout(timer);
		}
	}, [auto_release, report_token]);

	const tier =
		percentage >= 90
			? { label: "Gold Scholar", color: "#c9921a", icon: "🥇" }
			: percentage >= 75
				? { label: "Silver Scholar", color: "#9ca3af", icon: "🥈" }
				: percentage >= 60
					? { label: "Bronze Scholar", color: "#cd7f32", icon: "🥉" }
					: {
							label: "Participant",
							color: "var(--navy)",
							icon: "🎓",
						};

	return (
		<div
			style={{
				minHeight: "100svh",
				display: "flex",
				alignItems: "center",
				justifyContent: "center",
				padding: "24px 16px",
				background: "var(--bg)",
			}}>
			<div
				style={{
					background: "var(--card)",
					borderRadius: "16px",
					border: "1px solid var(--border)",
					padding: "48px 36px",
					maxWidth: "440px",
					width: "100%",
					textAlign: "center",
					boxShadow: "0 4px 24px rgba(13,27,62,.08)",
				}}>
				<div style={{ fontSize: "56px", marginBottom: "16px" }}>✅</div>
				<h1
					style={{
						fontSize: "24px",
						fontWeight: 700,
						color: "var(--navy)",
						marginBottom: "8px",
					}}>
					Test Submitted!
				</h1>
				<p
					style={{
						fontSize: "15px",
						color: "var(--muted)",
						marginBottom: "28px",
					}}>
					Your answers have been recorded and scored.
				</p>

				{resultData && (
					<>
						{/* Score hero */}
						<div
							style={{
								background: "var(--navy)",
								borderRadius: "12px",
								padding: "24px",
								marginBottom: "20px",
								color: "#fff",
							}}>
							<div
								style={{
									fontSize: "13px",
									opacity: 0.7,
									marginBottom: "6px",
									letterSpacing: ".6px",
									textTransform: "uppercase",
								}}>
								Your Score
							</div>
							<div
								style={{
									fontSize: "48px",
									fontWeight: 700,
									fontFamily: "'IBM Plex Mono', monospace",
									letterSpacing: "-1px",
								}}>
								{total_marks}
								<span
									style={{ fontSize: "20px", opacity: 0.6 }}>
									/{max_marks}
								</span>
							</div>
							<div
								style={{
									fontSize: "20px",
									fontWeight: 600,
									color: "var(--gold)",
									marginTop: "4px",
								}}>
								{percentage?.toFixed(1)}%
							</div>
						</div>

						{/* Tier badge */}
						<div
							style={{
								display: "inline-flex",
								alignItems: "center",
								gap: "8px",
								background: tier.color + "18",
								border: "1.5px solid " + tier.color + "55",
								color: tier.color,
								borderRadius: "30px",
								padding: "8px 20px",
								fontWeight: 700,
								fontSize: "15px",
								marginBottom: "28px",
							}}>
							<span>{tier.icon}</span>
							{tier.label}
						</div>
					</>
				)}

				{auto_release && report_token ? (
					<p style={{ fontSize: "14px", color: "var(--muted)" }}>
						Redirecting to your report in a moment…
					</p>
				) : (
					<div
						style={{
							background: "rgba(13,27,62,.04)",
							borderRadius: "8px",
							border: "1px dashed var(--border)",
							padding: "16px",
							fontSize: "14px",
							color: "var(--muted)",
						}}>
						Your detailed report will be shared by the centre once
						ready.
					</div>
				)}
			</div>
		</div>
	);
}
