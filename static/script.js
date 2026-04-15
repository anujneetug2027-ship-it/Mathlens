(function () {
  "use strict";

  // --- DOM ---
  const dropZone      = document.getElementById("dropZone");
  const fileInput     = document.getElementById("fileInput");
  const previewWrap   = document.getElementById("previewWrap");
  const previewImg    = document.getElementById("previewImg");
  const changeBtn     = document.getElementById("changeBtn");
  const solveBtnImage = document.getElementById("solveBtnImage");
  const solveBtnText  = document.getElementById("solveBtnText");
  const equationInput = document.getElementById("equationInput");
  const clearBtn      = document.getElementById("clearBtn");
  const imageCard     = document.getElementById("imageCard");
  const textCard      = document.getElementById("textCard");
  const resultCard    = document.getElementById("resultCard");
  const detectedEq    = document.getElementById("detectedEq");
  const stepsContainer= document.getElementById("stepsContainer");
  const resetBtn      = document.getElementById("resetBtn");
  const copyBtn       = document.getElementById("copyBtn");
  const errorCard     = document.getElementById("errorCard");
  const errorMsg      = document.getElementById("errorMsg");
  const errorResetBtn = document.getElementById("errorResetBtn");

  let selectedFile = null;
  let currentMode  = "image";
  let lastResult   = "";

  // --- Mode switch ---
  window.switchMode = function (mode) {
    currentMode = mode;
    document.getElementById("modeImage").classList.toggle("active", mode === "image");
    document.getElementById("modeText").classList.toggle("active", mode === "text");
    imageCard.hidden = mode !== "image";
    textCard.hidden  = mode !== "text";
    resultCard.hidden = true;
    errorCard.hidden  = true;
  };

  // --- Symbol keyboard ---
  document.querySelectorAll(".sym-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const insert = btn.dataset.insert;
      const ta = equationInput;
      const start = ta.selectionStart;
      const end   = ta.selectionEnd;
      ta.value = ta.value.slice(0, start) + insert + ta.value.slice(end);
      const pos = start + insert.length;
      ta.setSelectionRange(pos, pos);
      ta.focus();
      toggleSolveBtnText();
    });
  });

  // --- Example chips ---
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      equationInput.value = chip.dataset.eq;
      equationInput.focus();
      toggleSolveBtnText();
    });
  });

  // --- Text input ---
  equationInput.addEventListener("input", toggleSolveBtnText);
  function toggleSolveBtnText() {
    solveBtnText.disabled = equationInput.value.trim().length === 0;
  }

  clearBtn.addEventListener("click", () => {
    equationInput.value = "";
    solveBtnText.disabled = true;
    equationInput.focus();
  });

  // --- File input ---
  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); } });
  fileInput.addEventListener("change", () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });
  changeBtn.addEventListener("click", () => { fileInput.value = ""; fileInput.click(); });

  dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("drop", e => {
    e.preventDefault(); dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });

  function handleFile(file) {
    const allowed = ["image/png","image/jpeg","image/gif","image/bmp","image/webp","image/tiff"];
    if (!allowed.includes(file.type)) { showError("Unsupported file type. Use PNG, JPG, or WEBP."); return; }
    if (file.size > 16 * 1024 * 1024) { showError("File too large (max 16 MB)."); return; }
    selectedFile = file;
    const url = URL.createObjectURL(file);
    previewImg.src = url;
    previewImg.onload = () => URL.revokeObjectURL(url);
    dropZone.hidden = true;
    previewWrap.hidden = false;
    solveBtnImage.disabled = false;
    resultCard.hidden = true;
    errorCard.hidden = true;
  }

  // --- Solve: Image ---
  solveBtnImage.addEventListener("click", async () => {
    if (!selectedFile) return;
    setLoading(solveBtnImage, true);
    resultCard.hidden = true;
    errorCard.hidden = true;

    try {
      const fd = new FormData();
      fd.append("image", selectedFile);
      const res  = await fetch("/solve", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok || data.error) { showError(data.error || "Server error."); return; }
      showResult(data.detected_equation, data.steps);
    } catch (e) {
      showError("Could not reach server. Check your connection.");
    } finally {
      setLoading(solveBtnImage, false);
    }
  });

  // --- Solve: Text ---
  solveBtnText.addEventListener("click", async () => {
    const eq = equationInput.value.trim();
    if (!eq) return;
    setLoading(solveBtnText, true);
    resultCard.hidden = true;
    errorCard.hidden = true;

    try {
      const res  = await fetch("/solve_text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ equation: eq }),
      });
      const data = await res.json();
      if (!res.ok || data.error) { showError(data.error || "Server error."); return; }
      showResult(data.detected_equation, data.steps);
    } catch (e) {
      showError("Could not reach server. Check your connection.");
    } finally {
      setLoading(solveBtnText, false);
    }
  });

  // --- Show result ---
  function showResult(equation, steps) {
    detectedEq.textContent = equation || "—";
    stepsContainer.innerHTML = "";

    if (!steps || steps.length === 0) {
      stepsContainer.innerHTML = '<p style="color:var(--muted)">No steps returned.</p>';
    } else {
      steps.forEach((step, i) => {
        if (step.type === "final") {
          const div = document.createElement("div");
          div.className = "final-answer";
          div.innerHTML = `<p class="final-label">Final Answer</p><p class="final-value">${escHtml(step.expr)}</p>`;
          stepsContainer.appendChild(div);
        } else {
          const div = document.createElement("div");
          div.className = "step";
          div.style.animationDelay = `${i * 0.06}s`;
          div.innerHTML = `
            <div class="step-num">${i + 1}</div>
            <div class="step-body">
              <p class="step-title">${escHtml(step.title)}</p>
              <p class="step-expr">${escHtml(step.expr)}</p>
            </div>`;
          stepsContainer.appendChild(div);
        }
      });
    }

    lastResult = equation + "\n" + (steps || []).map(s => s.title + ": " + s.expr).join("\n");
    resultCard.hidden = false;
    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // --- Copy ---
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(lastResult).then(() => {
      copyBtn.textContent = "Copied!";
      setTimeout(() => copyBtn.textContent = "Copy", 1500);
    });
  });

  // --- Error ---
  function showError(msg) {
    errorMsg.textContent = msg;
    errorCard.hidden = false;
    errorCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // --- Reset ---
  function resetUI() {
    selectedFile = null;
    fileInput.value = "";
    previewImg.src = "";
    dropZone.hidden = false;
    previewWrap.hidden = true;
    solveBtnImage.disabled = true;
    equationInput.value = "";
    solveBtnText.disabled = true;
    resultCard.hidden = true;
    errorCard.hidden = true;
  }
  resetBtn.addEventListener("click", resetUI);
  errorResetBtn.addEventListener("click", resetUI);

  // --- Loading state ---
  function setLoading(btn, on) {
    btn.classList.toggle("loading", on);
    btn.disabled = on;
    btn.querySelector(".btn-label").textContent = on ? "Solving" : "Solve Equation";
  }

})();
