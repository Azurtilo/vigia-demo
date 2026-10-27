"""Dataclass settings as --prefix-* arguments plus an optional JSON file (spec 017)."""

import dataclasses
import json
import math
from pathlib import Path


def check_positive(config):
    """Every field finite and > 0; integer fields must be real integers."""
    for f in dataclasses.fields(config):
        value = getattr(config, f.name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{f.name} debe ser numérico.")
        if f.type is int and not isinstance(value, int):
            raise TypeError(f"{f.name} debe ser entero.")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{f.name} debe ser finito y mayor que cero.")


def from_file(cls, path, label):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    names = {f.name for f in dataclasses.fields(cls)}
    if not isinstance(data, dict) or set(data) - names:
        raise ValueError(f"Configuración de {label} inválida; claves admitidas: {sorted(names)}.")
    return cls(**data)


def add_arguments(parser, cls, prefix, title, settings_help):
    group = parser.add_argument_group(title)
    group.add_argument(f"--{prefix}-settings", help=settings_help)
    for f in dataclasses.fields(cls):
        group.add_argument(
            f"--{prefix}-" + f.name.replace("_", "-"),
            dest=f"{prefix}_" + f.name,
            type=int if f.type is int else float,
            help=f"por defecto {f.default}",
        )
    return group


def config_from_args(args, cls, prefix, label):
    """File values first, then explicit arguments; validation re-runs."""
    path = getattr(args, f"{prefix}_settings")
    base = from_file(cls, path, label) if path else cls()
    overrides = {
        f.name: getattr(args, f"{prefix}_" + f.name)
        for f in dataclasses.fields(cls)
        if getattr(args, f"{prefix}_" + f.name) is not None
    }
    return dataclasses.replace(base, **overrides)
