from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from urllib.parse import quote, unquote

import time as _time

import requests
from bs4 import BeautifulSoup

from app.domain.wear import append_wear_condition, extract_wear_condition


class SteamClient:
    def __init__(self) -> None:
        self.was_rate_limited = False
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
    def _fetch_json_with_curl(url: str) -> dict | None:
        curl_bin = shutil.which("curl")
        if not curl_bin:
            return None
        try:
            proc = subprocess.run(
                [curl_bin, "-fsS", "--compressed", "--max-time", "25", url],
                capture_output=True,
                check=False,
                text=True,
                timeout=30,
            )
        except Exception:
            return None
        if proc.returncode != 0 or not proc.stdout:
            return None
        try:
            data = json.loads(proc.stdout.lstrip("\ufeff"))
        except Exception:
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _fetch_text_with_curl(url: str, follow_redirects: bool = False) -> str | None:
        curl_bin = shutil.which("curl")
        if not curl_bin:
            return None
        args = [curl_bin, "-fsS", "--compressed", "--max-time", "25"]
        if follow_redirects:
            args.append("-L")
        args.append(url)
        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                check=False,
                text=True,
                timeout=30,
            )
        except Exception:
            return None
        if proc.returncode != 0 or not proc.stdout:
            return None
        return proc.stdout.lstrip("\ufeff")

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

    def _fetch_listing_lowest_price_cents(self, market_hash: str) -> int | None:
        """Fallback: parse the lowest EUR gross listing price from Steam's listing page.

        `priceoverview` is the small endpoint, but Steam sometimes rate-limits it while
        the listing page still renders. The new market page embeds listing data as an
        escaped JSON payload with `strSubtotal` values such as `€125.51`.
        """
        url = f"https://steamcommunity.com/market/listings/730/{quote(market_hash)}"
        html_text = self._fetch_text_with_curl(url, follow_redirects=True)
        if not html_text:
            return None

        prices: list[int] = []
        for match in re.finditer(r'strSubtotal\\+":\\+"([^\\]+)', html_text):
            cents = self.parse_eur_to_cents(match.group(1))
            if cents is not None and cents > 0:
                prices.append(cents)
        return min(prices) if prices else None

    def fetch_price_cents(self, market_hash: str) -> int | None:
        self.was_rate_limited = False
        url = (
            "https://steamcommunity.com/market/priceoverview/"
            f"?appid=730&currency=3&market_hash_name={quote(market_hash)}"
        )
        try:
            resp = self._session.get(url, timeout=15)
            if resp.status_code == 429:
                fallback_cents = self._fetch_listing_lowest_price_cents(market_hash)
                if fallback_cents is not None:
                    return fallback_cents
                self.was_rate_limited = True
                return None
            txt = resp.text.lstrip("\ufeff")
            data = json.loads(txt)
            if not isinstance(data, dict) or not data.get("success"):
                return self._fetch_listing_lowest_price_cents(market_hash)
            price_str = data.get("lowest_price") or data.get("median_price") or ""
            cents = self.parse_eur_to_cents(price_str)
            return cents if cents is not None else self._fetch_listing_lowest_price_cents(market_hash)
        except Exception:
            return self._fetch_listing_lowest_price_cents(market_hash)

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

    def resolve_steam_id(self, raw_input: str) -> str | None:
        """Akzeptiert SteamID64, Profil-URL (/profiles/... oder /id/...) oder Vanity-Namen."""
        self.was_rate_limited = False
        raw = (raw_input or "").strip()
        if not raw:
            return None
        if re.fullmatch(r"7656119\d{10}", raw):
            return raw
        m = re.search(r"steamcommunity\.com/profiles/(7656119\d{10})", raw)
        if m:
            return m.group(1)
        m = re.search(r"steamcommunity\.com/id/([^/?#]+)", raw)
        vanity = m.group(1) if m else raw
        if not re.fullmatch(r"[A-Za-z0-9_-]{2,64}", vanity):
            return None
        try:
            xml_resp = self._session.get(
                f"https://steamcommunity.com/id/{quote(vanity)}?xml=1", timeout=10
            )
            if xml_resp.status_code == 429:
                self.was_rate_limited = True
                return None
            m = re.search(r"<steamID64>\s*(7656119\d{10})\s*</steamID64>", xml_resp.text)
            if m:
                return m.group(1)

            page_resp = self._session.get(
                f"https://steamcommunity.com/id/{quote(vanity)}", timeout=10
            )
            if page_resp.status_code == 429:
                self.was_rate_limited = True
                return None
            m = re.search(r'"steamid"\s*:\s*"(7656119\d{10})"', page_resp.text)
            return m.group(1) if m else None
        except Exception:
            return None

    def fetch_inventory(self, steam_id64: str) -> tuple[list[dict] | None, str | None]:
        """CS2-Inventar (app 730, context 2) laden. Liefert (Items, Fehlertext).

        Items sind pro market_hash aggregiert: {market_hash, name, wear, icon, category, qty}.
        Nur marketable Items (nur die haben einen Steam-Market-Preis).
        """
        self.was_rate_limited = False
        base = f"https://steamcommunity.com/inventory/{steam_id64}/730/2"
        aggregated: dict[str, dict] = {}
        last_assetid: str | None = None
        for _page in range(10):
            url = f"{base}?l=german&count=2000"
            if last_assetid:
                url += f"&start_assetid={last_assetid}"
            try:
                resp = self._session.get(url, timeout=20)
            except Exception:
                return None, "Steam ist gerade nicht erreichbar. Bitte spaeter erneut versuchen."
            if resp.status_code == 403:
                return None, "Das Inventar ist privat. Bitte in den Steam-Privatsphaere-Einstellungen auf 'Oeffentlich' stellen."
            if resp.status_code == 429:
                data = self._fetch_json_with_curl(url)
                if data is None:
                    self.was_rate_limited = True
                    return None, "Steam-Rate-Limit erreicht (429). Bitte ein paar Minuten warten."
            else:
                try:
                    data = resp.json()
                except Exception:
                    data = None
                if not isinstance(data, dict):
                    data = self._fetch_json_with_curl(url)
            if not isinstance(data, dict) or not data.get("success"):
                return None, "Inventar konnte nicht geladen werden (unerwartete Steam-Antwort)."

            descriptions = {
                f"{d.get('classid')}_{d.get('instanceid')}": d
                for d in (data.get("descriptions") or [])
            }
            for asset in data.get("assets") or []:
                key = f"{asset.get('classid')}_{asset.get('instanceid')}"
                desc = descriptions.get(key)
                if not desc or int(desc.get("marketable") or 0) != 1:
                    continue
                mh = (desc.get("market_hash_name") or "").strip()
                if not mh:
                    continue
                entry = aggregated.get(mh)
                if entry is None:
                    display_name = append_wear_condition(desc.get("name"), mh)
                    aggregated[mh] = {
                        "market_hash": mh,
                        "name": display_name,
                        "wear": extract_wear_condition(mh),
                        "icon": self._resolve_icon_url(desc.get("icon_url") or desc.get("icon_url_large")),
                        "category": self._normalize_category(desc.get("type") or ""),
                        "qty": 1,
                    }
                else:
                    entry["qty"] += 1

            if data.get("more_items"):
                last_assetid = str(data.get("last_assetid") or "")
                if not last_assetid:
                    break
                _time.sleep(3)
                continue
            break

        items = sorted(aggregated.values(), key=lambda x: x["name"].casefold())
        if not items:
            return None, "Keine marktfaehigen CS2-Items im Inventar gefunden."
        return items, None
