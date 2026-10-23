(() => {
  "use strict";
  const tray = document.getElementById("care-reminders");
  if (!tray) return;
  const list = tray.querySelector("[data-care-alert-list]");
  const announcer = tray.querySelector("[data-care-announcer]");
  const csrf = tray.querySelector("[name=csrfmiddlewaretoken]")?.value;
  let syncing = false;
  let serverTime = null;
  let syncAt = performance.now();
  const localSeen = new Set();
  const timerNodes = [...document.querySelectorAll("[data-care-timer]")];
  if (timerNodes.length) serverTime = Date.parse(timerNodes[0].dataset.server);
  function tick() {
    if (!Number.isFinite(serverTime)) return;
    const now = serverTime + performance.now() - syncAt;
    for (const node of timerNodes) {
      const due = Date.parse(node.dataset.due);
      if (!Number.isFinite(due)) continue;
      const seconds = Math.ceil((due - now) / 1000);
      node.classList.toggle("is-due", seconds <= 0);
      const minutes = Math.ceil(Math.abs(seconds) / 60);
      node.textContent = seconds <= 0 ? `Cambio pendiente · ${minutes} min de atraso` : `Próximo cambio en ${Math.floor(seconds / 3600)} h ${Math.floor((seconds % 3600) / 60)} min`;
    }
  }
  function show(item) {
    const article = document.createElement("article");
    article.className = "care-alert";
    article.dataset.key = item.key;
    const name = document.createElement("strong");
    name.textContent = item.patient_name;
    const label = document.createElement("p");
    label.textContent = item.label;
    const link = document.createElement("a");
    link.className = "text-link";
    link.href = `${tray.dataset.patientBase}${item.patient_id}/`;
    link.textContent = "Abrir ficha y registrar cuidado";
    const close = document.createElement("button");
    close.type = "button";
    close.textContent = "Cerrar aviso (no registra cuidado)";
    close.addEventListener("click", () => article.remove());
    article.append(name, label, link, close);
    list.append(article);
    announcer.textContent = `${item.patient_name}: ${item.label}`;
  }
  async function sync() {
    if (syncing || document.hidden || !navigator.onLine) return;
    syncing = true;
    try {
      const response = await fetch(tray.dataset.poll, {credentials: "same-origin", cache: "no-store"});
      if (!response.ok || response.redirected) return;
      const data = await response.json();
      serverTime = Date.parse(data.now);
      syncAt = performance.now();
      for (const node of timerNodes) {
        const timer = data.timers.find(t => String(t.patient) === node.dataset.careTimer);
        node.dataset.due = timer?.due || "";
        if (!timer?.due) {
          node.textContent = timer?.paused ? "Recordatorios pausados" : "Recordatorios no activos · actualiza la ficha";
          node.classList.remove("is-due");
        }
      }
      const keys = new Set(data.reminders.map(i => i.key));
      for (const alert of list.children) if (!keys.has(alert.dataset.key)) alert.remove();
      for (const item of data.reminders) {
        if (item.seen || localSeen.has(item.key)) continue;
        const result = await fetch(tray.dataset.claim, {method: "POST", credentials: "same-origin", cache: "no-store",
          headers: {"X-CSRFToken": csrf, "Content-Type": "application/x-www-form-urlencoded"}, body: new URLSearchParams({token: item.token})});
        if (!result.ok) continue;
        const claim = await result.json();
        localSeen.add(item.key);
        if (claim.claimed) show(item);
      }
      tick();
    } catch (_) {
      // A suspended/offline tab retries on return. No local clinical data is stored.
    } finally { syncing = false; }
  }
  setInterval(tick, 1000);
  setInterval(sync, 30000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) sync(); });
  window.addEventListener("online", sync);
  window.addEventListener("focus", sync);
  tick();
  sync();
})();
