(() => {
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.getAttribute("aria-controls") || "");
      if (!input) return;
      const hidden = input.getAttribute("type") === "password";
      input.setAttribute("type", hidden ? "text" : "password");
      button.setAttribute("aria-pressed", hidden ? "true" : "false");
      button.textContent = hidden ? "Скрыть" : "Показать";
    });
  });

  document.querySelectorAll("form[data-pending]").forEach((form) => {
    form.addEventListener("submit", () => {
      const submit = form.querySelector("[type=submit]");
      if (!submit || submit.disabled) return;
      submit.disabled = true;
      submit.dataset.originalLabel = submit.textContent || "";
      submit.textContent = submit.dataset.pendingLabel || "Входим…";
    });
  });

  if (prefersReduced) {
    document.documentElement.classList.add("reduce-motion");
  }
})();
