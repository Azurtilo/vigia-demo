"""Medición sRGB de los tokens de las tres paletas; no acredita toda la UI."""

import json
from pathlib import Path


def rgb(hex_color):
    return tuple(int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5))


def mix(first, second, weight):
    return tuple(a * weight + b * (1 - weight) for a, b in zip(first, second))


def luminance(color):
    linear = [
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in color
    ]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def ratio(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def check(name, foreground, background, minimum=4.5):
    value = ratio(foreground, background)
    assert value >= minimum, f"{name}: {value:.2f} < {minimum}"
    return {"uso": name, "ratio": round(value, 2), "minimo": minimum}


white, black, page = rgb("#ffffff"), rgb("#000000"), rgb("#f2f5f8")
results = {}
for name, hex_color in (
    ("petroleo", "#0f766e"),
    ("ciruela", "#7e22ce"),
    ("cobre", "#9a3412"),
):
    brand = rgb(hex_color)
    results[name] = [
        check("blanco sobre marca", white, brand),
        check("blanco sobre hover", white, mix(brand, black, 0.82)),
        check("marca sobre selección tenue", brand, mix(brand, white, 0.09)),
        check("enlace sobre superficie", brand, white),
        check("enlace sobre página", brand, page),
        check("foco sobre página", brand, page, 3),
    ]
results["comunes"] = [
    check("texto sobre página", rgb("#182536"), page),
    check("ayuda sobre página", rgb("#506177"), page),
    check("límite de control sobre superficie", rgb("#758599"), white, 3),
    check("límite de control sobre página", rgb("#758599"), page, 3),
    check("éxito sobre fondo", rgb("#166534"), rgb("#ecfdf3")),
    check("error sobre fondo", rgb("#b42318"), rgb("#fff1f0")),
    check("aviso sobre fondo", rgb("#854d0e"), rgb("#fef9e8")),
    check("información sobre fondo", rgb("#1e40af"), rgb("#eff6ff")),
    check("blanco sobre peligro", white, rgb("#b42318")),
]
destination = Path(__file__).parent / "evidencia" / "contraste.json"
destination.write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(results, ensure_ascii=False, indent=2))
