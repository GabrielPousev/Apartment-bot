import requests
import json
import time
from datetime import datetime, timedelta

# ==========================================
# הגדרות אישיות - מלא כאן את הפרטים שלך
# ==========================================
TELEGRAM_TOKEN = "8618582216:AAECI7jE8Q4OkmeSq-V8iApUT9-qbwL8orY"      # הטוקן מ-BotFather
CHAT_ID = "1761397353"           # ה-ID מ-userinfobot

# ==========================================
# הגדרות חיפוש
# ==========================================
MAX_PRICE = 3800
MIN_ROOMS = 2
MAX_ROOMS = 2
MAX_AGE_HOURS = 48  # רק דירות שעלו ב-48 שעות האחרונות

CITIES = ["תל אביב יפו", "רמת גן", "גבעתיים"]

# ==========================================
# קוד הבוט - אין צורך לשנות כלום מכאן
# ==========================================

seen_ids_file = "seen_ids.json"

def load_seen_ids():
    try:
        with open(seen_ids_file, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_seen_ids(ids):
    with open(seen_ids_file, "w") as f:
        json.dump(list(ids), f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"שגיאה בשליחת הודעה: {e}")

def search_yad2(city):
    url = "https://gw.yad2.co.il/feed-search-legacy/realestate/rent"
    params = {
        "city": city,
        "rooms": f"{MIN_ROOMS}-{MAX_ROOMS}",
        "price": f"0-{MAX_PRICE}",
        "forceLdLoad": "true"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"שגיאה בחיפוש {city}: {e}")
    return None

def is_recent(date_str):
    try:
        # יד2 מחזירה תאריך בפורמט: "2024-01-15T10:30:00"
        ad_date = datetime.fromisoformat(date_str.replace("Z", ""))
        cutoff = datetime.now() - timedelta(hours=MAX_AGE_HOURS)
        return ad_date > cutoff
    except:
        return True  # אם אין תאריך, נכלול את הדירה

def format_message(ad, city):
    address = ad.get("address", {})
    street = address.get("street", {}).get("text", "")
    house = address.get("house", {}).get("text", "")
    
    price = ad.get("price", "לא צוין")
    rooms = ad.get("rooms", "לא צוין")
    floor = ad.get("floor", {}).get("text", "")
    size = ad.get("squareMeter", "")
    
    ad_id = ad.get("id", "")
    link = f"https://www.yad2.co.il/item/{ad_id}"
    
    msg = f"🏠 <b>דירה חדשה נמצאה!</b>\n\n"
    msg += f"📍 <b>כתובת:</b> {street} {house}, {city}\n"
    msg += f"💰 <b>מחיר:</b> {price} ₪\n"
    msg += f"🛏 <b>חדרים:</b> {rooms}\n"
    if floor:
        msg += f"🏢 <b>קומה:</b> {floor}\n"
    if size:
        msg += f"📐 <b>גודל:</b> {size} מ\"ר\n"
    msg += f"\n🔗 <a href='{link}'>לחץ לפרטים</a>"
    
    return msg

def check_apartments():
    seen_ids = load_seen_ids()
    new_count = 0

    for city in CITIES:
        print(f"מחפש ב{city}...")
        data = search_yad2(city)
        
        if not data:
            continue
            
        ads = data.get("data", {}).get("feed", {}).get("feed_items", [])
        
        for ad in ads:
            ad_id = ad.get("id")
            if not ad_id or ad_id in seen_ids:
                continue
            
            # בדיקת תאריך
            date_added = ad.get("date_added", "")
            if date_added and not is_recent(date_added):
                continue
            
            # שלח הודעה
            message = format_message(ad, city)
            send_telegram(message)
            seen_ids.add(ad_id)
            new_count += 1
            
            time.sleep(1)  # המתנה קצרה בין הודעות
    
    save_seen_ids(seen_ids)
    print(f"נמצאו {new_count} דירות חדשות")

def main():
    print("🤖 בוט דירות מתחיל לעבוד...")
    send_telegram("✅ הבוט עלה לאוויר! אחפש דירות כל 10 דקות.")
    
    while True:
        try:
            check_apartments()
        except Exception as e:
            print(f"שגיאה: {e}")
        
        print("ממתין 10 דקות...")
        time.sleep(600)  # 10 דקות

if __name__ == "__main__":
    main()
