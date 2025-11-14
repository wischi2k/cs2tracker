import os, requests
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT  = os.getenv("TELEGRAM_CHAT_ID")

def tg_send(text: str) -> bool:
    if not TOKEN or not CHAT:
        print("[TG] fehlt Konfiguration – bitte TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in .env setzen.")
        print("[TG] Nachricht wäre:", text)
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": 1
            },
            timeout=15
        )
        if not r.ok:
            print("[TG] Fehler:", r.text)
        return r.ok
    except Exception as e:
        print("[TG] Exception:", e)
        return False
