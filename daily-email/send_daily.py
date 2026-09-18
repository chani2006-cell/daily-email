#!/usr/bin/env python3
"""
שולח כל יום מייל אחד עם הקטע הבא מתוך days.json, ומדלג אוטומטית על שבתות.
המצב (איזה יום נשלח אחרון) נשמר בקובץ state.json שמתעדכן ונדחף חזרה לריפו
על ידי ה-workflow של GitHub Actions.
"""

import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")
BASE_DIR = Path(__file__).parent
DAYS_FILE = BASE_DIR / "days.json"
STATE_FILE = BASE_DIR / "state.json"

DOC_TITLE = "אמונה וביטחון – חיזוק יומי"


def load_days():
    with open(DAYS_FILE, encoding="utf-8") as f:
        # keys in JSON are strings; convert to int for easy math
        return {int(k): v for k, v in json.load(f).items()}


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"last_sent_day": 0, "last_sent_date": None}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_email(day_num: int, body: str):
    username = os.environ["MAIL_USERNAME"]
    app_password = os.environ["MAIL_APP_PASSWORD"]
    to_addr = os.environ["MAIL_TO"]

    subject = f"יום {day_num} – {DOC_TITLE}"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = to_addr

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(username, app_password)
        server.sendmail(username, [to_addr], msg.as_string())

    print(f"נשלח מייל עבור יום {day_num}")


def main():
    now_il = datetime.now(ISRAEL_TZ)
    today_str = now_il.date().isoformat()

    # שבת = לא שולחים (weekday(): Monday=0 ... Sunday=6, Saturday=5)
    if now_il.weekday() == 5:
        print("היום שבת בישראל — מדלגים.")
        return

    days = load_days()
    total = len(days)
    state = load_state()

    # כבר נשלח היום? (מגן מפני הרצה כפולה של ה-cron, ראו README)
    if state.get("last_sent_date") == today_str:
        print("כבר נשלח מייל היום — מדלגים.")
        return

    next_day = (state.get("last_sent_day", 0) % total) + 1
    if next_day not in days:
        print(f"אין טקסט עבור יום {next_day}, עוצר.", file=sys.stderr)
        sys.exit(1)

    send_email(next_day, days[next_day])

    state["last_sent_day"] = next_day
    state["last_sent_date"] = today_str
    save_state(state)


if __name__ == "__main__":
    main()
