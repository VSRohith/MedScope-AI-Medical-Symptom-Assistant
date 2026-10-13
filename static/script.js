document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("symptom-form");
  const button = document.getElementById("analyze-btn");

  if (form && button) {
    form.addEventListener("submit", () => {
      if (!form.checkValidity()) {
        return;
      }

      button.disabled = true;
      button.innerHTML = "<span>Analyzing symptoms... please wait</span>";
    });
  }

  const report = document.getElementById("report");

  if (report) {
    setTimeout(() => {
      report.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 150);
  }
});
