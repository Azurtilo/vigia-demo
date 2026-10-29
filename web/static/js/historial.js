/* Historial sin entradas repetidas (spec 018, D-080). Un formulario marcado con
   data-replace-history se envía con fetch y su entrada del historial se reemplaza
   por el destino. Sin JavaScript o sin fetch, el envío de siempre. */
(() => {
  if (!window.fetch || !window.FormData) return;

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (event.defaultPrevented || !(form instanceof HTMLFormElement) || !form.hasAttribute("data-replace-history")) return;
    if (form.method.toLowerCase() !== "post") return;
    event.preventDefault();
    if (form.dataset.sending) return;  // a second click while the first is on its way

    const submitter = event.submitter;
    const data = new FormData(form);
    if (submitter?.name) data.append(submitter.name, submitter.value);
    form.dataset.sending = "1";
    submitter?.setAttribute("disabled", "");

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: data,
        credentials: "same-origin",
        headers: { "X-Vigia-Navigation": "replace" },
      });
      if ((response.headers.get("Content-Type") || "").includes("application/json")) {
        const { location: target } = await response.json();
        if (target) { window.location.replace(target); return; }
      }
      // Form errors and other pages: show them where the form was.
      const html = await response.text();
      history.replaceState(null, "", response.url);
      document.open();
      document.write(html);
      document.close();
    } catch {
      delete form.dataset.sending;
      submitter?.removeAttribute("disabled");
      window.createToast?.("error", null, "Error", "No se pudo enviar. Revisa tu conexión e inténtalo otra vez.");
    }
  });
})();
