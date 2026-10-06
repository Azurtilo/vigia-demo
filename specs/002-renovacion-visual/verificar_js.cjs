/* Verificación aislada de contratos JS; no controla un navegador ni requiere npm. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const source = (name) => fs.readFileSync(path.join(root, 'static/js', name), 'utf8');
let passed = 0;
function test(name, action) { action(); passed++; console.log(`OK: ${name}`); }

function chartEnvironment({ reduced = false, cdn = true, present = true } = {}) {
  const element = { hidden: false }, fallback = { hidden: true };
  const options = [], events = {}, mediaEvents = {};
  const chart = { setOption: (option) => options.push(option), resize: () => chart.resized = true, dispose: () => chart.disposed = true };
  const document = {
    documentElement: {}, body: { append() {} },
    getElementById: (id) => id === 'chart_home' ? (present ? element : null) : fallback,
    createElement: () => ({ style: {}, remove() {} }),
  };
  const context = {
    document,
    window: { echarts: cdn ? { init: () => chart } : undefined, addEventListener: (name, fn) => events[name] = fn },
    echarts: { init: () => chart },
    getComputedStyle: () => ({ color: 'rgb(15, 118, 110)', getPropertyValue: () => 'Segoe UI' }),
    matchMedia: () => ({ matches: reduced, addEventListener: (name, fn) => mediaEvents[name] = fn }),
    ResizeObserver: class { constructor(fn) { events.resize = fn; } observe() {} disconnect() {} },
  };
  vm.runInNewContext(source('grafico_home.js'), context);
  return { element, fallback, options, events, mediaEvents, chart };
}

test('El gráfico desactiva animación con movimiento reducido y conserva las series', () => {
  const normal = chartEnvironment();
  const reduced = chartEnvironment({ reduced: true });
  assert.equal(normal.options[0].animation, true);
  assert.equal(reduced.options[0].animation, false);
  assert.deepEqual(JSON.parse(JSON.stringify(reduced.options[0].series)), JSON.parse(JSON.stringify(normal.options[0].series)));
  normal.mediaEvents.change({ matches: true });
  assert.equal(normal.options.at(-1).animation, false);
});
test('Resize del contenedor y retorno desde caché conservan el gráfico', () => {
  const environment = chartEnvironment();
  environment.events.resize();
  assert.equal(environment.chart.resized, true);
  environment.events.pagehide({ persisted: true });
  assert.notEqual(environment.chart.disposed, true);
  environment.events.pagehide({ persisted: false });
  assert.equal(environment.chart.disposed, true);
});
test('Ausencia de CDN muestra fallback; ausencia de contenedor no falla', () => {
  const missing = chartEnvironment({ cdn: false });
  assert.equal(missing.element.hidden, true);
  assert.equal(missing.fallback.hidden, false);
  assert.equal(chartEnvironment({ present: false }).options.length, 0);
});

test('Cerrar un diálogo con movimiento reducido no espera una animación', () => {
  const handlers = {}, attributes = {};
  const trigger = { setAttribute: (name, value) => attributes[name] = value, isConnected: true, getClientRects: () => [1], focus: () => trigger.focused = true };
  const classes = new Set();
  const dialog = { open: false, classList: { contains: (name) => classes.has(name), add: (name) => classes.add(name), remove: (name) => classes.delete(name) }, addEventListener: (name, fn) => handlers[name] = fn, querySelectorAll: () => [], showModal() { this.open = true; }, close() { this.open = false; handlers.close(); } };
  const context = {
    window: {}, document: { activeElement: trigger, body: { style: { overflow: '' } }, addEventListener() {}, querySelector: () => null, querySelectorAll: (selector) => selector === 'dialog' ? [dialog] : [] },
    matchMedia: () => ({ matches: true, addEventListener() {} }),
    clearTimeout() {}, setTimeout() { throw new Error('No debe esperar en movimiento reducido'); },
  };
  vm.runInNewContext(source('interfaz.js'), context);
  context.window.baseDialogs.open(dialog, trigger);
  assert.equal(context.document.body.style.overflow, 'hidden');
  assert.equal(attributes['aria-expanded'], 'true');
  context.window.baseDialogs.close(dialog);
  assert.equal(dialog.open, false);
  assert.equal(context.document.body.style.overflow, '');
  assert.equal(attributes['aria-expanded'], 'false');
  assert.equal(trigger.focused, true);
});

test('Notificaciones tratan HTML como texto y mantienen errores persistentes', () => {
  const timers = [];
  function element() { return { dataset: {}, children: [], style: {}, className: '', setAttribute(name, value) { this[name] = value; }, append(...children) { this.children.push(...children); }, addEventListener() {}, querySelector: () => null, contains: () => false, matches: () => false }; }
  const notifications = element();
  const serverError = element(); serverError.dataset.toastType = 'error extra';
  const context = {
    window: {}, document: { querySelector: () => notifications, querySelectorAll: () => [serverError], createElement: element },
    setTimeout: (fn) => timers.push(fn), clearTimeout() {},
  };
  vm.runInNewContext(source('mensajes.js'), context);
  assert.equal(serverError.dataset.kind, 'error');
  assert.equal(serverError.role, 'alert');
  assert.equal(timers.length, 0);
  const malicious = '<img src=x onerror=alert(1)>';
  context.window.error(malicious);
  const toast = notifications.children[0];
  assert.equal(toast.children[0].children[1].textContent, malicious);
  assert.equal(toast.children[0].children[1].innerHTML, undefined);
  assert.equal(timers.length, 0);
  context.window.success('Guardado');
  assert.equal(timers.length, 1);
});
console.log(`${passed} comprobaciones JS aprobadas. Emulación de contratos, no prueba de navegador.`);
