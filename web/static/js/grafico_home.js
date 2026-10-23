(() => {
  const element = document.getElementById("chart_home");
  const dataElement = document.getElementById("dashboard-plan-data");
  if (!element || !dataElement) return;
  const fallback = document.getElementById("chart-unavailable");
  const unavailable = () => {
    element.hidden = true;
    if (fallback) fallback.hidden = false;
  };
  if (!window.echarts) { unavailable(); return; }
  let chart;
  try {
    const plans = JSON.parse(dataElement.textContent);
    const styles = getComputedStyle(document.documentElement);
    function color(name) {
      const probe = document.createElement("span");
      probe.style.color = `var(${name})`;
      document.body.append(probe);
      const value = getComputedStyle(probe).color;
      probe.remove();
      return value;
    }
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const muted = color("--muted"), line = color("--border");
    element.hidden = false;
    chart = echarts.init(element, null, { renderer: "svg" });
    chart.setOption({
      animation: !reduced.matches,
      textStyle: { fontFamily: styles.getPropertyValue("--font-ui").trim() },
      grid: { left: 12, right: 40, bottom: 24, top: 12, containLabel: true },
      xAxis: {
        type: "value", minInterval: 1,
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: line } }
      },
      yAxis: {
        type: "category", inverse: true, data: plans.map(plan => plan.name),
        axisLabel: { color: muted, width: 105, overflow: "truncate" },
        axisLine: { show: false }, axisTick: { show: false }
      },
      series: [{
        type: "bar", name: "Suscripciones", barMaxWidth: 20,
        data: plans.map(plan => plan.total),
        itemStyle: { color: color("--chart-1"), borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: "right", color: color("--ink") }
      }]
    });
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(element);
    const updateMotion = event => chart.setOption({ animation: !event.matches });
    reduced.addEventListener("change", updateMotion);
    window.addEventListener("pagehide", event => {
      if (!event.persisted) {
        observer.disconnect();
        reduced.removeEventListener("change", updateMotion);
        chart.dispose();
      }
    });
  } catch {
    if (chart) chart.dispose();
    unavailable();
  }
})();
