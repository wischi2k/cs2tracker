from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ItemView:
    id: int
    name: str
    icon: str | None
    icon_updated_at: int 
    cat: str | None
    active: int
    buy: float | None
    cur: float | None
    net: float | None
    diff_g: float | None
    diff_n: float | None


@dataclass
class SelectedItemView:
    it: ItemView
    chart: dict[str, Any]
    alert_th: float | None
