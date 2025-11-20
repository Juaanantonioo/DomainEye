// ---- Call FastAPI backend ----
async function sendDomainQuery(domain) {
  const response = await fetch("/api/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ domain }),
  });

  if (!response.ok) {
    throw new Error("Request failed");
  }

  const data = await response.json();
  console.log("Backend response:", data);
  return data;
}

// ---- UI wiring ----

const yearEl = document.getElementById("year");
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}

const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");

if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });

  navLinks.addEventListener("click", (e) => {
    if (e.target.tagName === "A") {
      navLinks.classList.remove("open");
    }
  });
}

const domainForm = document.getElementById("domainForm");
const domainInput = document.getElementById("domainInput");
const statusSpan = document.querySelector("[data-status]");

function normalizeDomain(input) {
  return input.trim();
}

function isLikelyDomain(str) {
  return /\./.test(str) && !/\s/.test(str);
}

if (domainForm && domainInput && statusSpan) {
  domainForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const raw = domainInput.value;
    const domain = normalizeDomain(raw);

    if (!domain || !isLikelyDomain(domain)) {
      statusSpan.textContent = "Please enter a valid domain.";
      statusSpan.style.color = "#b91c1c";
      domainInput.focus();
      domainInput.select();
      return;
    }

    statusSpan.textContent = `Generating report for ${domain}…`;
    statusSpan.style.color = "#0f172a";

    try {
      const result = await sendDomainQuery(domain);

      if (result.status === "ok" && result.report_url) {
        // 🔥 Redirect to the generated report page
        window.location.href = result.report_url;

        console.log("Redirecting to report:", result.report_url);
      } else {
        statusSpan.textContent = result.detail || "Unexpected response from server.";
        statusSpan.style.color = "#b91c1c";
      }
    } catch (err) {
      console.error(err);
      statusSpan.textContent = "An error occurred while querying the backend.";
      statusSpan.style.color = "#b91c1c";
    }
  });

  domainInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      domainForm.dispatchEvent(new Event("submit"));
    }
  });
}
