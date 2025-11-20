from datetime import datetime

def build_domain_report_html(domain : str, tables_html: str, score: float, recommend_div : str) -> str:
    """
    Build the full DominAI report HTML.

    Parameters
    ----------
    tables_html : str
        Raw HTML string containing the two tables
        (one for existing domains and one for non-existent domains).
        Example: "<table>...</table><table>...</table>"

    score : float
        Global risk score in [0.0, 1.0]. It will be shown in the text
        and used by the JS diagram.

    Returns
    -------
    str
        Complete HTML document as a string.
    """

    template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>DominAI – Domain Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <style>
    :root {
      --bg: #f4f5fb;
      --text-main: #111827;
      --text-muted: #6b7280;
      --accent: #00c899;
      --border: #e5e7eb;
      --card-bg: #ffffff;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text-main);
      padding: 2rem 1rem;
    }

    .report {
      max-width: 1100px;
      margin: 0 auto;
      background: var(--card-bg);
      border-radius: 18px;
      padding: 2rem 2.2rem 2.5rem;
      box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
    }

    header h1 {
      font-size: 1.8rem;
      margin-bottom: 0.4rem;
    }

    header p {
      color: var(--text-muted);
      font-size: 0.95rem;
      margin-bottom: 1.8rem;
    }

    h2 {
      font-size: 1.2rem;
      margin-bottom: 0.8rem;
    }

    h3 {
      font-size: 1rem;
      margin-top: 1.2rem;
      margin-bottom: 0.4rem;
    }

    .score-section {
      display: flex;
      flex-wrap: wrap;
      gap: 2rem;
      align-items: center;
      margin-bottom: 2.5rem;
    }

    .score-text {
      flex: 1 1 260px;
      min-width: 0;
    }

    .score-text p {
      font-size: 0.95rem;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 0.8rem;
    }

    .score-text strong {
      color: var(--accent);
    }

    .score-chart-container {
      flex: 0 0 auto;
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .score-chart-container canvas {
      display: block;
    }

    .colorbar {
      font-size: 0.75rem;
      color: var(--text-muted);
      text-align: center;
    }

    .colorbar-gradient {
      width: 18px;
      height: 160px;
      border-radius: 8px;
      margin: 0 auto 0.25rem auto;
      background: linear-gradient(to top, red, yellow, #7fd321, #00a000);
      border: 1px solid rgba(0,0,0,0.2);
    }

    .colorbar-scale {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 160px;
    }

    .colorbar-scale span {
      line-height: 1;
    }

    .tables-section {
      margin-top: 1rem;
    }

    .tables-section h2 {
      margin-bottom: 1rem;
    }

    .tables-wrapper {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .tables-wrapper table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid var(--border);
      background-color: #ffffff;
    }

    .tables-wrapper thead {
      background: linear-gradient(135deg, #a8ff78, #78ffd6);
    }

    .tables-wrapper th,
    .tables-wrapper td {
      padding: 0.55rem 0.75rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }

    .tables-wrapper th {
      font-weight: 600;
      font-size: 0.85rem;
    }

    .tables-wrapper tbody tr:nth-child(even) {
      background-color: #f9fafb;
    }

    .tables-wrapper tbody tr:last-child td {
      border-bottom: none;
    }

    @media (max-width: 768px) {
      .report {
        padding: 1.5rem 1.3rem 2rem;
      }
      header h1 {
        font-size: 1.5rem;
      }
      .score-section {
        align-items: flex-start;
      }
    }
  </style>
</head>
<body>
  <main class="report">
    <header>
      <h1>Report for __DOMAIN__</h1>
      <p class="meta">Generated at __TIME__</p>
      <p>Automatically generated analysis of your domain space and potential brand-abuse risk.</p>
    </header>

    <section class="score-section">
      <div class="score-text">
        <h2>Overall Risk Score: <strong id="score-value">__SCORE_TEXT__</strong></h2>

        <h3>Recommendations</h3>
        __RECOMMEND_DIV__

        <h3>Score Explanation</h3>
        <p id="score-explanation">
          The score ranges from <strong>0.0</strong> (low concern) to <strong>1.0</strong> (high concern).
          It reflects the proportion and nature of risky or confusingly similar domains that already exist
          compared to the combinations evaluated. The coloured ring on the right shows how individual
          domain groups contribute to the final score.
        </p>
      </div>

      <div class="score-chart-container">
        <canvas id="score-diagram" width="260" height="260" aria-label="risk score diagram"></canvas>

        <div class="colorbar">
          <div class="colorbar-gradient"></div>
          <div class="colorbar-scale">
            <span>1.0</span>
            <span>0.8</span>
            <span>0.6</span>
            <span>0.4</span>
            <span>0.2</span>
            <span>0.0</span>
          </div>
        </div>
      </div>
    </section>

    <section class="tables-section">
      <h2>Domain Lists</h2>
      <div class="tables-wrapper">
        __TABLES__
      </div>
    </section>
  </main>

  <script>
    const DOMINAI_SCORE = __SCORE_JS__;
    const segmentValues = Array(12).fill(DOMINAI_SCORE);

    function valueToColor(v) {
      const clamped = Math.min(1, Math.max(0, v));
      const hue = 120 * clamped;
      return "hsl(" + hue + ", 80%, 50%)";
    }

    function drawScoreDiagram(canvasId, score, segmentValues) {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      const width = canvas.width;
      const height = canvas.height;
      const cx = width / 2;
      const cy = height / 2;

      ctx.clearRect(0, 0, width, height);

      const nSeg = segmentValues.length;
      const outerR = Math.min(width, height) * 0.48;
      const innerR = outerR * 0.72;
      const innerCircleR = innerR * 0.82;

      const fullAngle = 2 * Math.PI;
      const segAngle = fullAngle / nSeg;

      ctx.save();
      ctx.translate(cx, cy);

      for (let i = 0; i < nSeg; i++) {
        const value = segmentValues[i];
        const start = -Math.PI / 2 + i * segAngle;
        const end = start + segAngle;

        ctx.beginPath();
        ctx.arc(0, 0, outerR, start, end, false);
        ctx.arc(0, 0, innerR, end, start, true);
        ctx.closePath();
        ctx.fillStyle = valueToColor(value);
        ctx.fill();

        ctx.strokeStyle = "rgba(0,0,0,0.15)";
        ctx.lineWidth = 1;
        ctx.stroke();

        const midAngle = (start + end) / 2;
        const textR = (innerR + outerR) / 2;
        const labelX = Math.cos(midAngle) * textR;
        const labelY = Math.sin(midAngle) * textR;

        ctx.fillStyle = "#111827";
        ctx.font = "10px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(i + 1), labelX, labelY);
      }

      ctx.beginPath();
      ctx.arc(0, 0, innerCircleR, 0, fullAngle);
      ctx.closePath();
      ctx.fillStyle = valueToColor(score);
      ctx.fill();

      ctx.fillStyle = "#111827";
      ctx.font = "bold 42px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(score.toFixed(2), 0, 4);

      ctx.restore();
    }

    document.addEventListener("DOMContentLoaded", function () {
      var scoreValueEl = document.getElementById("score-value");
      if (scoreValueEl) {
        scoreValueEl.textContent = DOMINAI_SCORE.toFixed(2);
      }
      drawScoreDiagram("score-diagram", DOMINAI_SCORE, segmentValues);
    });
  </script>
</body>
</html>
"""

    # Format score for text and JS
    score_str = f"{score:.2f}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = template.replace("__SCORE_TEXT__", score_str)
    html = html.replace("__DOMAIN__", domain)
    html = html.replace("__TIME__", now)
    html = html.replace("__SCORE_JS__", score_str)
    html = html.replace("__RECOMMEND_DIV__", recommend_div)
    html = html.replace("__TABLES__", tables_html)

    return html
