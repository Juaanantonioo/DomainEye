from datetime import datetime

def build_domain_report_html(domain: str, tables_html: str, score: float, recommend_div: str) -> str:
    """
    Build the full DominAI report HTML with the same color system as the main index page.

    Parameters
    ----------
    domain : str
        Main domain analysed.

    tables_html : str
        Raw HTML string containing the two tables
        (one for existing domains and one for non-existent domains).

    score : float
        Global risk score in [0.0, 100.0]. It will be shown in the text
        and used by the JS diagram.

    recommend_div : str
        Raw HTML for the recommendations block (can be one or several <p>).

    Returns
    -------
    str
        Complete HTML document as a string.
    """

    template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>DominAI – Report for __DOMAIN__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <style>
    :root {
      --bg-gradient-start: #a8ff78; /* lime-ish */
      --bg-gradient-end: #78ffd6;   /* light blue/teal */
      --accent: #00c899;
      --accent-soft: rgba(0, 200, 153, 0.15);
      --text-main: #0b1721;
      --text-muted: #5f6c7b;
      --card-bg: rgba(255, 255, 255, 0.9);
      --border-subtle: rgba(0, 0, 0, 0.06);
      --shadow-soft: 0 18px 45px rgba(15, 23, 42, 0.18);
      --radius-lg: 18px;
      --radius-pill: 999px;
      --transition-fast: 150ms ease-out;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text",
        "Segoe UI", sans-serif;
      min-height: 100vh;
      background: linear-gradient(135deg, var(--bg-gradient-start), var(--bg-gradient-end));
      color: var(--text-main);
      display: flex;
      flex-direction: column;
    }

    main {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem 1.5rem 3rem;
    }

    .report-card {
      max-width: 900px;
      width: 100%;
      background: var(--card-bg);
      border-radius: 24px;
      padding: 2.5rem 2.3rem 2.3rem;
      box-shadow: var(--shadow-soft);
      border: 1px solid rgba(255, 255, 255, 0.7);
      backdrop-filter: blur(14px);
      position: relative;
      overflow: hidden;
    }

    .report-card::before {
      content: "";
      position: absolute;
      inset: -40%;
      background:
        radial-gradient(circle at 0% 0%, rgba(255, 255, 255, 0.55), transparent 55%),
        radial-gradient(circle at 100% 100%, rgba(0, 200, 153, 0.2), transparent 60%);
      mix-blend-mode: soft-light;
      opacity: 0.9;
      pointer-events: none;
    }

    .report-inner {
      position: relative;
      z-index: 1;
    }

    header.report-header h1 {
      font-size: clamp(1.7rem, 3vw, 2.1rem);
      margin-bottom: 0.25rem;
      color: var(--text-main);
    }

    header.report-header p.meta {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-bottom: 0.5rem;
    }

    header.report-header p.subtitle {
      color: var(--text-muted);
      font-size: 0.9rem;
      margin-bottom: 1.6rem;
    }

    h2 {
      font-size: 1.2rem;
      margin-bottom: 0.7rem;
      color: var(--text-main);
    }

    h3 {
      font-size: 1rem;
      margin-top: 1.1rem;
      margin-bottom: 0.4rem;
      color: var(--text-main);
    }

    .score-section {
      display: flex;
      flex-wrap: wrap;
      gap: 2rem;
      align-items: center;
      margin-bottom: 2.1rem;
    }

    .score-text {
      flex: 1 1 260px;
      min-width: 0;
    }

    .score-text p {
      font-size: 0.92rem;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 0.7rem;
    }

    .score-text strong {
      color: var(--accent);
    }

    .score-chart-container {
      flex: 0 0 auto;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .score-chart-container canvas {
      display: block;
    }

    .tables-section {
      margin-top: 0.7rem;
    }

    .tables-section h2 {
      margin-bottom: 0.9rem;
    }

    .tables-wrapper {
      display: flex;
      flex-direction: column;
      gap: 1.2rem;
    }

    .tables-wrapper table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid var(--border-subtle);
      background-color: rgba(255, 255, 255, 0.98);
      box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
    }

    .tables-wrapper thead {
      background: linear-gradient(135deg, var(--bg-gradient-start), var(--bg-gradient-end));
    }

    .tables-wrapper th,
    .tables-wrapper td {
      padding: 0.55rem 0.75rem;
      text-align: left;
      border-bottom: 1px solid var(--border-subtle);
    }

    .tables-wrapper th {
      font-weight: 600;
      font-size: 0.82rem;
      color: var(--text-main);
    }

    .tables-wrapper tbody tr:nth-child(even) {
      background-color: #f9fafb;
    }

    .tables-wrapper tbody tr:last-child td {
      border-bottom: none;
    }

    @media (max-width: 768px) {
      main {
        padding-inline: 1rem;
      }
      .report-card {
        padding: 2rem 1.5rem 2rem;
        border-radius: 20px;
      }
      .score-section {
        align-items: flex-start;
      }
    }

    @media (max-width: 480px) {
      header.report-header h1 {
        font-size: 1.6rem;
      }
    }
  </style>
</head>
<body>
  <main>
    <section class="report-card">
      <div class="report-inner">
        <header class="report-header">
          <h1>Report for __DOMAIN__</h1>
          <p class="meta">Generated at __TIME__</p>
          <p class="subtitle">
            Automatically generated analysis of your domain space and potential brand-abuse risk.
          </p>
        </header>

        <section class="score-section">
          <div class="score-text">
            <h2>Overall Risk Score: <strong id="score-value">__SCORE_TEXT__ / 100</strong></h2>

            <h3>Recommendations</h3>
            __RECOMMEND_DIV__

            <h3>Score Explanation</h3>
            <p id="score-explanation">
              The score ranges from <strong>0</strong> (low concern, green) to <strong>100</strong> (high concern, red).
              The coloured circle on the right acts like a traffic light: green for low risk, amber for moderate risk,
              and red for high risk. The value summarises how many risky or confusingly similar domains exist
              compared to the combinations evaluated.
            </p>
          </div>

          <div class="score-chart-container">
            <canvas id="score-diagram" width="260" height="260" aria-label="risk score circle"></canvas>
          </div>
        </section>

        <section class="tables-section">
          <h2>Domain Lists</h2>
          <div class="tables-wrapper">
            __TABLES__
          </div>
        </section>
      </div>
    </section>
  </main>

  <script>
    // Score in [0, 100]
    const DOMINAI_SCORE = __SCORE_JS__;

    // Map score to traffic-light color:
    // 0 -> green, 50 -> amber, 100 -> red
    function scoreToColor(score) {
      const norm = Math.min(100, Math.max(0, score)) / 100; // 0..1
      const hue = 120 * (1 - norm); // 120 (green) -> 0 (red)
      return "hsl(" + hue + ", 80%, 50%)";
    }

    function drawScoreCircle(canvasId, score) {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      const width = canvas.width;
      const height = canvas.height;
      const cx = width / 2;
      const cy = height / 2;

      ctx.clearRect(0, 0, width, height);

      const radius = Math.min(width, height) * 0.4;

      // Filled circle with traffic-light color
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
      ctx.closePath();
      ctx.fillStyle = scoreToColor(score);
      ctx.fill();

      // Subtle border
      ctx.strokeStyle = "rgba(0,0,0,0.25)";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Score text
      ctx.fillStyle = "#111827";
      ctx.font = "bold 42px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(score.toFixed(0), cx, cy);
    }

    document.addEventListener("DOMContentLoaded", function () {
      const scoreValueEl = document.getElementById("score-value");
      if (scoreValueEl) {
        scoreValueEl.textContent = DOMINAI_SCORE.toFixed(0) + " / 100";
      }
      drawScoreCircle("score-diagram", DOMINAI_SCORE);
    });
  </script>
</body>
</html>
"""

    # Format score for text and JS (integer 0–100)
    score_str = f"{score:.0f}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = template.replace("__SCORE_TEXT__", score_str)
    html = html.replace("__DOMAIN__", domain)
    html = html.replace("__TIME__", now)
    html = html.replace("__SCORE_JS__", score_str)
    html = html.replace("__RECOMMEND_DIV__", recommend_div)
    html = html.replace("__TABLES__", tables_html)

    return html
