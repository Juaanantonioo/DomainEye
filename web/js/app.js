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

// Year in footer
const yearEl = document.getElementById("year");
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}

// Mobile nav toggle
const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");

if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });

  // Close nav when clicking a link on mobile
  navLinks.addEventListener("click", (e) => {
    if (e.target.tagName === "A") {
      navLinks.classList.remove("open");
    }
  });
}

// Domain form handling
const domainForm = document.getElementById("domainForm");
const domainInput = document.getElementById("domainInput");
const statusSpan = document.querySelector("[data-status]");

function normalizeDomain(input) {
  return input.trim();
}

function isLikelyDomain(str) {
  // Super simple heuristic, you can replace with a stricter regex if you want
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

    statusSpan.textContent = `Querying ${domain}…`;
    statusSpan.style.color = "#0f172a";

    try {
      // 🔥 Call FastAPI backend
      const result = await sendDomainQuery(domain);
      statusSpan.textContent = `${result.status.toUpperCase()}: ${result.detail}`;
      statusSpan.style.color = "#0f172a";
    } catch (err) {
      console.error(err);
      statusSpan.textContent = "An error occurred while querying the backend.";
      statusSpan.style.color = "#b91c1c";
    }
  });

  // Explicit submit on Enter, though form already handles it by default
  domainInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      domainForm.dispatchEvent(new Event("submit"));
    }
  });
}
