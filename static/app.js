document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const sidebar = document.getElementById("app-sidebar");
  const openButton = document.querySelector("[data-sidebar-toggle]");
  const closeTarget = document.querySelector("[data-sidebar-close]");

  const closeSidebar = () => body.classList.remove("sidebar-open");
  if (openButton && sidebar) openButton.addEventListener("click", () => body.classList.toggle("sidebar-open"));
  if (closeTarget) closeTarget.addEventListener("click", closeSidebar);
  document.querySelectorAll(".sidebar a").forEach(link => link.addEventListener("click", closeSidebar));
  document.addEventListener("keydown", event => { if (event.key === "Escape") closeSidebar(); });

  const normalize = value => (value || "").toLowerCase().trim();
  const updateTable = tableId => {
    const table = document.getElementById(tableId);
    if (!table) return;
    const search = document.querySelector(`[data-table-search="${tableId}"]`);
    const filter = document.querySelector(`[data-table-filter="${tableId}"]`);
    const query = normalize(search?.value);
    const category = filter?.value || "";
    let visible = 0;
    table.querySelectorAll("tbody tr").forEach(row => {
      const matchesText = !query || normalize(row.textContent).includes(query);
      const matchesCategory = !category || row.dataset.category === category;
      const show = matchesText && matchesCategory;
      row.hidden = !show;
      if (show) visible += 1;
    });
    const empty = document.querySelector(`[data-empty-for="${tableId}"]`);
    if (empty) empty.classList.toggle("visible", visible === 0);
  };

  document.querySelectorAll("[data-table-search]").forEach(input => {
    const id = input.dataset.tableSearch;
    input.addEventListener("input", () => updateTable(id));
  });
  document.querySelectorAll("[data-table-filter]").forEach(select => {
    const id = select.dataset.tableFilter;
    select.addEventListener("change", () => updateTable(id));
  });


  document.querySelectorAll("[data-password-toggle]").forEach(button => {
    const wrapper = button.closest(".login-input-shell");
    const input = wrapper?.querySelector('input[type="password"], input[data-password-field]');
    if (!input) return;
    button.addEventListener("click", () => {
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      button.setAttribute("aria-pressed", String(!showing));
      button.setAttribute("aria-label", showing ? "Show password" : "Hide password");
      input.focus();
    });
  });


  const labShell = document.querySelector("[data-lab-id]");
  if (labShell) {
    const labId = labShell.dataset.labId;
    const checks = [...labShell.querySelectorAll("[data-lab-step-check]")];
    const progressText = labShell.querySelector("[data-lab-progress-text]");
    const progressBar = labShell.querySelector("[data-lab-progress-bar]");
    const storageKey = `academy-guided-lab:${labId}`;

    const readSaved = () => {
      try {
        return new Set(JSON.parse(localStorage.getItem(storageKey) || "[]").map(String));
      } catch (_) {
        return new Set();
      }
    };

    const save = completed => {
      try {
        localStorage.setItem(storageKey, JSON.stringify([...completed]));
      } catch (_) {
        // Progress still works for the current page when browser storage is unavailable.
      }
    };

    const completed = readSaved();

    const updateLabProgress = () => {
      checks.forEach(check => {
        const step = check.dataset.labStepCheck;
        check.checked = completed.has(step);
        check.closest(".guided-step")?.classList.toggle("completed", completed.has(step));
      });
      const count = completed.size;
      const percentage = checks.length ? Math.round((count / checks.length) * 100) : 0;
      if (progressText) progressText.textContent = `${count} of ${checks.length} steps`;
      if (progressBar) progressBar.style.width = `${percentage}%`;
    };

    checks.forEach(check => {
      check.addEventListener("change", () => {
        const step = check.dataset.labStepCheck;
        if (check.checked) completed.add(step);
        else completed.delete(step);
        save(completed);
        updateLabProgress();
      });
    });

    updateLabProgress();
  }

  document.querySelectorAll("[data-copy-command-group]").forEach(button => {
    button.addEventListener("click", async () => {
      const code = button.closest(".command-group")?.querySelector("code")?.textContent?.trim();
      if (!code) return;
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(code);
        button.textContent = "Copied";
      } catch (_) {
        button.textContent = "Select and copy";
      }
      window.setTimeout(() => { button.textContent = original; }, 1600);
    });
  });

});