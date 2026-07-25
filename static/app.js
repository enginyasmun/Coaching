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

});