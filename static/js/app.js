document.addEventListener("click", async (event) => {
  const copyButton = event.target.closest("[data-copy]");
  if (!copyButton) return;

  try {
    await navigator.clipboard.writeText(copyButton.dataset.copy || "");
    const originalText = copyButton.textContent;
    copyButton.textContent = "Copied";
    setTimeout(() => {
      copyButton.textContent = originalText;
    }, 1200);
  } catch (error) {
    alert("Gagal menyalin teks.");
  }
});

document.addEventListener("submit", (event) => {
  const form = event.target;
  const message = form.dataset.confirm;
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});
