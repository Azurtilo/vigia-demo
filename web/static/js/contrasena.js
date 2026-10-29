/* Indicadores de contraseña en vivo (spec 018). La contraseña no sale del navegador
   ni se guarda; el servidor sigue siendo quien la valida. */
(() => {
  const STATUS = { pending: "pendiente", pass: "cumple", fail: "no cumple" };
  const CHECKABLE = ["length", "numeric", "match"];

  function setState(item, state) {
    item.dataset.state = state;
    item.querySelector(".password-rule-status").textContent = STATUS[state];
  }

  document.querySelectorAll("[data-password-checklist]").forEach((box) => {
    const password = document.getElementById(box.dataset.password);
    if (!password) return;
    const confirm = box.dataset.confirm ? document.getElementById(box.dataset.confirm) : null;
    const typed = (box.dataset.personalIds || "").split(",").filter(Boolean).map((id) => document.getElementById(id)).filter(Boolean);
    let known = [];
    try { known = JSON.parse(document.getElementById(box.dataset.personalValues)?.textContent || "[]"); } catch { known = []; }
    const summary = box.querySelector("[data-password-summary]");
    const items = [...box.querySelectorAll("li[data-rule]")];

    // Right below the password field; without JavaScript it stays after the form fields.
    (password.closest('[id^="div_id_"]') || password.parentElement).after(box);
    password.setAttribute("aria-describedby", [password.getAttribute("aria-describedby"), box.id].filter(Boolean).join(" "));

    // Username and the part of the e-mail before the @ (D-078).
    const personal = () => [...known, ...typed.map((input) => input.value)]
      .map((value) => value.split("@")[0].trim().toLowerCase())
      .filter((value) => value.length >= 3);

    function evaluate(item, value) {
      const rule = item.dataset.rule;
      if (rule === "match") {
        if (!confirm || !confirm.value) return "pending";
        return confirm.value === value ? "pass" : "fail";
      }
      if (!value) return "pending";
      if (rule === "length") return value.length >= Number(item.dataset.min) ? "pass" : "fail";
      if (rule === "numeric") return /^\d+$/.test(value) ? "fail" : "pass";
      if (rule === "similar") return personal().some((part) => value.toLowerCase().includes(part)) ? "fail" : "pending";
      return "pending";  // only the server can check it (D-079)
    }

    let timer;
    function update() {
      items.forEach((item) => setState(item, evaluate(item, password.value)));
      const checkable = items.filter((item) => CHECKABLE.includes(item.dataset.rule));
      const passed = checkable.filter((item) => item.dataset.state === "pass").length;
      clearTimeout(timer);
      timer = setTimeout(() => { summary.textContent = `Requisitos cumplidos: ${passed} de ${checkable.length}.`; }, 700);
    }

    [password, confirm, ...typed].filter(Boolean).forEach((input) => input.addEventListener("input", update));
  });
})();
