#!/usr/bin/env python3
"""
שולח כל יום מייל אחד עם הקטע הבא מתוך days.json, ומדלג אוטומטית על שבתות.
המצב (איזה יום נשלח אחרון) נשמר בקובץ state.json שמתעדכן ונדחף חזרה לריפו
על ידי ה-workflow של GitHub Actions.
"""

import html
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
        return {int(k): v for k, v in json.load(f).items()}


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"last_sent_day": 0, "last_sent_date": None}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def build_html(day_num: int, body: str) -> str:
    safe_body = html.escape(body)
    return f"""\
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background-color:#f4f4f4;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:24px 12px;">
        <table role="presentation" width="600" style="max-width:600px; width:100%;
               background-color:#ffffff; border-radius:8px; padding:32px;"
               cellpadding="0" cellspacing="0">
          <tr>
            <td dir="rtl" align="right"
                style="font-family:Arial, Tahoma, sans-serif; font-size:20px;
                       line-height:1.7; color:#222222; text-align:right;">
              <div style="font-size:16px; color:#888888; margin-bottom:8px;">
                יום {day_num} &middot; {html.escape(DOC_TITLE)}
              </div>
              <div>{safe_body}</div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_email(day_num: int, body: str):
    username = os.environ["MAIL_USERNAME"]
    app_password = os.environ["MAIL_APP_PASSWORD"]
    to_addr = os.environ["MAIL_TO"]

    subject = f"יום {day_num} – {DOC_TITLE}"
    msg = MIMEText(build_html(day_num, body), "html", "utf-8")
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

    if now_il.weekday() == 5:
        print("היום שבת בישראל — מדלגים.")
        return

    days = load_days()
    total = len(days)
    state = load_state()

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
