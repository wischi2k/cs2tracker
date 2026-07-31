from __future__ import annotations

import html
import json
import re
from urllib.parse import quote, unquote

import requests
from bs4 import BeautifulSoup


class SteamClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
                )
            }
        )

    @staticmethod
    def parse_market_hash_from_url(steam_url: str) -> str | None:
        m = re.search(r"/market/listings/730/([^/?#]+)", steam_url or "")
        return unquote(m.group(1)) if m else None

    @staticmethod
    def _normalize_name_for_match(value: str) -> str:
        cleaned = (value or "").strip().casefold()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    @staticmethod
    def _find_exact_search_match(results: list[dict], market_hash: str) -> dict | None:
        wanted = SteamClient._normalize_name_for_match(market_hash)
        for candidate in results:
            desc = candidate.get("asset_description") or {}
            names = [
                SteamClient._normalize_name_for_match(candidate.get("name") or ""),
                SteamClient._normalize_name_for_match(candidate.get("hash_name") or ""),
                SteamClient._normalize_name_for_match(desc.get("market_hash_name") or ""),
            ]
            if wanted in names:
                return candidate
        return None

    @staticmethod
    def _normalize_category(type_txt: str) -> str:
        t = (type_txt or "").lower()
        if any(k in t for k in ["behaelter", "behälter", "kiste", "case", "container"]):
            return "Kiste"
        if "sticker" in t or "aufkleber" in t:
            return "Sticker"
        if "agent" in t:
            return "Agent"
        if "key" in t or "schluessel" in t or "schlüssel" in t:
            return "Schluessel"
        if "patch" in t:
            return "Patch"
        if "music" in t or "musik" in t:
            return "Musik-Kit"
        if "glove" in t or "handschuh" in t:
            return "Handschuhe"
        if "knife" in t or "messer" in t:
            return "Messer"
        return "Waffen-Skin"

    @staticmethod
    def _resolve_icon_url(icon_path: str | None) -> str | None:
        if not icon_path:
            return None
        if icon_path.startswith("http://") or icon_path.startswith("https://"):
            return icon_path
        return f"https://steamcommunity-a.akamaihd.net/economy/image/{icon_path}"

    @staticmethod
    def parse_eur_to_cents(price_str: str) -> int | None:
        if not price_str:
            return None
        s = price_str.replace("\u00a0", "")
        s = s.replace("€", "").replace("EUR", "").strip()
        s = re.sub(r"[^0-9,.\-]", "", s)
        if not s:
            return None
        s = s.replace("--", "00")
        is_negative = s.startswith("-")
        s = s.lstrip("-")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            val = float(s)
            if is_negative:
                val = -val
            return int(round(val * 100))
        except ValueError:
            return None

    def fetch_price_cents(self, market_hash: str) -> int | None:
        url = (
            "https://steamcommunity.com/market/priceoverview/"
            f"?appid=730&currency=3&market_hash_name={quote(market_hash)}"
        )
        try:
            resp = self._session.get(url, timeout=15)
            if resp.status_code == 429:
                return None
            txt = resp.text.lstrip("\ufeff")
            data = json.loads(txt)
            if not isinstance(data, dict) or not data.get("success"):
                return None
            price_str = data.get("lowest_price") or data.get("median_price") or ""
            return self.parse_eur_to_cents(price_str)
        except Exception:
            return None

    def fetch_meta_for_hash(self, market_hash: str) -> tuple[str, str | None, str | None]:
        query = quote(market_hash)
        try:
            url = (
                "https://steamcommunity.com/market/search/render/"
                f"?appid=730&norender=1&count=20&query={query}"
            )
            j = self._session.get(url, timeout=10).json()
            if j.get("success") and j.get("results"):
                selected = self._find_exact_search_match(j["results"], market_hash)
                if selected is not None:
                    result_name = (selected.get("name") or selected.get("hash_name") or market_hash).strip()
                    desc = selected.get("asset_description") or {}
                    icon = self._resolve_icon_url(desc.get("icon_url") or desc.get("icon_url_large"))
                    cat = self._normalize_category(desc.get("type") or "")
                    return (result_name, icon, cat)

            url_wide = (
                "https://steamcommunity.com/market/search/render/"
                f"?appid=730&norender=1&count=100&query={query}"
            )
            j_wide = self._session.get(url_wide, timeout=12).json()
            if j_wide.get("success") and j_wide.get("results"):
                selected = self._find_exact_search_match(j_wide["results"], market_hash)
                if selected is not None:
                    result_name = (selected.get("name") or selected.get("hash_name") or market_hash).strip()
                    desc = selected.get("asset_description") or {}
                    icon = self._resolve_icon_url(desc.get("icon_url") or desc.get("icon_url_large"))
                    cat = self._normalize_category(desc.get("type") or "")
                    return (result_name, icon, cat)
        except Exception:
            pass

        try:
            page = self._session.get(
                f"https://steamcommunity.com/market/listings/730/{quote(market_hash)}",
                timeout=10,
            ).text
            soup = BeautifulSoup(page, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else market_hash
            if " - Steam Community Market" in title:
                name = title.replace(" - Steam Community Market", "")
                name = re.sub(r"^\s*Counter-Strike\s*[\d]?\s*-\s*", "", name).strip()
            else:
                name = market_hash

            type_el = soup.select_one("#largeiteminfo_item_type")
            item_type = type_el.get_text(strip=True) if type_el else ""
            cat = self._normalize_category(item_type)

            icon_el = soup.select_one("#largeiteminfo_item_icon img")
            icon = icon_el.get("src") if icon_el else None
            if not icon:
                m_img = re.search(
                    r"https://[a-z0-9.-]*/economy/image/[^\"'\\\s<]+",
                    page,
                    re.IGNORECASE,
                )
                icon = html.unescape(m_img.group(0)) if m_img else None
            if not icon:
                m_icon_path = re.search(r'"icon_url"\s*:\s*"([^"]+)"', page)
                if m_icon_path:
                    icon = self._resolve_icon_url(html.unescape(m_icon_path.group(1)))

            return (name, icon, cat)
        except Exception:
            return (market_hash, None, None)
