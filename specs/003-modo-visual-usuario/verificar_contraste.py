"""Mide pares sRGB desde tokens reales; no sustituye revisión visual completa."""

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]
css = (root / "static/css/tokens.css").read_text(encoding="utf-8")
light_css, dark_css = css.split('html[data-mode="dark"]', 1)


def declarations(source):
    return dict(re.findall(r"(--[\w-]+):\s*([^;]+);", source))


def color(value, tokens):
    value = value.strip()
    if value.startswith("var("):
        return color(tokens[value[4:-1]], tokens)
    if value.startswith("#"):
        return tuple(int(value[i : i + 2], 16) / 255 for i in (1, 3, 5))
    if value.startswith("color-mix("):
        parts = value[len("color-mix(") : -1].split(",")[1:]
        parsed = [
            re.fullmatch(
                r"\s*(var\(--[\w-]+\)|#[\da-fA-F]{6})(?:\s+(\d+)%)?\s*", part
            ).groups()
            for part in parts
        ]
        weights = [float(weight) / 100 if weight else None for _, weight in parsed]
        if weights[0] is None:
            weights[0] = 1 - weights[1] if weights[1] is not None else 0.5
        if weights[1] is None:
            weights[1] = 1 - weights[0]
        colors = [color(token, tokens) for token, _ in parsed]
        return tuple(
            (a * weights[0] + b * weights[1]) / sum(weights) for a, b in zip(*colors)
        )
    raise ValueError(value)


def luminance(rgb):
    return sum(
        (v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) * weight
        for v, weight in zip(rgb, (0.2126, 0.7152, 0.0722))
    )


pairs = []
for background in ("--page", "--surface", "--surface-muted"):
    for foreground in ("--ink", "--muted", "--brand", "--danger"):
        pairs.append((foreground, background, 4.5))
    pairs.extend([(token, background, 3) for token in ("--focus", "--control-border")])
pairs += [
    ("--on-brand", "--brand", 4.5),
    ("--on-brand", "--brand-hover", 4.5),
    ("--brand", "--brand-soft", 4.5),
]
for state in ("success", "danger", "warning", "info"):
    pairs.append((f"--{state}", f"--{state}-soft", 4.5))
pairs += [("--on-danger", "--danger", 4.5), ("--on-danger", "--danger-hover", 4.5)]
pairs += [(token, "--surface", 3) for token in ("--chart-1", "--chart-2", "--chart-3")]

results = {}
for brand, clear, dark in (
    ("petroleo", "#0f766e", "#5eead4"),
    ("ciruela", "#7e22ce", "#c084fc"),
    ("cobre", "#9a3412", "#fdba74"),
):
    for mode in ("light", "dark"):
        tokens = declarations(light_css)
        if mode == "dark":
            tokens.update(declarations(dark_css))
        tokens.update({"--brand-light": clear, "--brand-dark": dark})
        measurements = []
        for foreground, background, minimum in pairs:
            high, low = sorted(
                (
                    luminance(color(tokens[foreground], tokens)),
                    luminance(color(tokens[background], tokens)),
                ),
                reverse=True,
            )
            ratio = (high + 0.05) / (low + 0.05)
            assert ratio >= minimum, (
                f"{brand}/{mode} {foreground}/{background}: {ratio:.2f} < {minimum}"
            )
            measurements.append(
                {
                    "texto": foreground,
                    "fondo": background,
                    "ratio": round(ratio, 2),
                    "minimo": minimum,
                }
            )
        results[f"{brand}/{mode}"] = measurements
destination = Path(__file__).parent / "evidencia/contraste.json"
destination.parent.mkdir(exist_ok=True)
destination.write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(
    f"{sum(map(len, results.values()))} pares correctos en seis combinaciones marca/modo; fuente tokens.css."
)
