/**
 * script.js — MathLens frontend logic
 *
 * Responsibilities:
 *  1. Handle file selection (click + drag-and-drop)
 *  2. Show image preview
 *  3. POST the image to /solve
 *  4. Display result or error
 *  5. Reset UI for another attempt
 */

(function () {
  "use strict";

  // ---------- DOM references ----------
  const dropZone      = document.getElementById("dropZone");
  const fileInput     = document.getElementById("fileInput");
  const previewWrap   = document.getElementById("previewWrap");
  const previewImg    = document.getElementById("previewImg");
  const changeBtn     = document.getElementById("changeBtn");
  const solveBtn      = document.getElementById("solveBtn");
  const uploadSection = document.getElementById("uploadSection");
  const resultCard    = document.getElementById("resultCard");
  const detectedEq    = document.getElementById("detectedEq");
  const solutionVal   = document.getElementById("solutionVal");
  const resetBtn      = document.getElementById("resetBtn");
  const errorCard     = document.getElementById("errorCard");
  const errorMsg      = document.getElementById("errorMsg");
  const errorResetBtn = document.getElementById("errorResetBtn");

  /** Currently selected file, or null. */
  let selectedFile = null;

  // ---------- File selection ----------

  /** Open the hidden file input when the drop zone is clicked. */
  dropZone.addEventListener("click", () => fileInput.click());

  /** Also trigger on Enter / Space for keyboard accessibility. */
  dropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });

  /** File chosen via the OS file picker. */
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFile(fileInput.files[0]);
    }
  });

  /** "Change image" button resets the picker. */
  changeBtn.addEventListener("click", () => {
    fileInput.value = "";       // allow same file to be re-selected
    fileInput.click();
  });

  // ---------- Drag-and-drop ----------

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  // ---------- File handling & preview ----------

  /**
   * Validate the file, show a preview, and enable the Solve button.
   * @param {File} file
   */
  function handleFile(file) {
    const allowedTypes = ["image/png", "image/jpeg", "image/gif", "image/bmp", "image/webp", "image/tiff"];

    if (!allowedTypes.includes(file.type)) {
      showError("Unsupported file type. Please upload a PNG, JPG, WEBP, or similar image.");
      return;
    }

    if (file.size > 16 * 1024 * 1024) {
      showError("File is too large. Maximum allowed size is 16 MB.");
      return;
    }

    selectedFile = file;

    // Generate an object URL for the preview
    const objectUrl = URL.createObjectURL(file);
    previewImg.src = objectUrl;
    previewImg.onload = () => URL.revokeObjectURL(objectUrl); // free memory after load

    // Swap drop zone for preview
    dropZone.hidden = true;
    previewWrap.hidden = false;
    solveBtn.disabled = false;

    // Hide previous results / errors
    resultCard.hidden = true;
    errorCard.hidden = true;
  }

  // ---------- Solve ----------

  solveBtn.addEventListener("click", handleSolve);

  async function handleSolve() {
    if (!selectedFile) return;

    // Set loading state
    solveBtn.classList.add("loading");
    solveBtn.disabled = true;
    solveBtn.querySelector(".btn-label").textContent = "Solving";
    resultCard.hidden = true;
    errorCard.hidden = true;

    try {
      const formData = new FormData();
      formData.append("image", selectedFile);

      const response = await fetch("/solve", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        showError(data.error || "Server returned an error. Please try again.");
        return;
      }

      showResult(data.detected_equation, data.result);

    } catch (err) {
      console.error("Request failed:", err);
      showError("Could not reach the server. Check your connection and try again.");
    } finally {
      // Reset button regardless of outcome
      solveBtn.classList.remove("loading");
      solveBtn.querySelector(".btn-label").textContent = "Solve Equation";
      // Keep disabled — user must change image or reset
    }
  }

  // ---------- Display result ----------

  /**
   * Show the result card with the detected equation and solution.
   * @param {string} equation - Raw detected equation text from OCR.
   * @param {string} result   - Solved result string.
   */
  function showResult(equation, result) {
    detectedEq.textContent = equation || "—";
    solutionVal.textContent = result  || "—";
    resultCard.hidden = false;
    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // ---------- Display error ----------

  /**
   * Show the error card with a message.
   * @param {string} message
   */
  function showError(message) {
    errorMsg.textContent = message;
    errorCard.hidden = false;
    errorCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // ---------- Reset ----------

  function resetUI() {
    selectedFile = null;
    fileInput.value = "";
    previewImg.src = "";
    dropZone.hidden = false;
    previewWrap.hidden = true;
    solveBtn.disabled = true;
    solveBtn.querySelector(".btn-label").textContent = "Solve Equation";
    resultCard.hidden = true;
    errorCard.hidden = true;
  }

  resetBtn.addEventListener("click", resetUI);
  errorResetBtn.addEventListener("click", resetUI);

})();

