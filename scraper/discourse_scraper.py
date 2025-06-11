import requests
import json
import os
from time import sleep

# Replace this with YOUR actual _t cookie from the browser
COOKIES = {
    "_t": "4h%2F1FlLzIceBFvbPF4cwjePV66pu23a0a0U6VcsK30jw0lqsVDt%2FfsJjVj43dN%2BMWfoQ6s2xTySwpxReL%2FOLWAztQXmsDxhVOr0zrF4fi6MStBG5DdDt34mkowhc8sF5qpJJ9JeRH%2FdjOtx%2FZf60aCtVVoeQCFo4ZE3AFr5NCM3OYPUIQ%2FcZ06tmtI8TwnsfRgWBQdrXyQ5IrNIA%2B4xtGKbQZ5MTzihflNux2fK25ZBlylVrWm5OP6m%2BSpmvaEggjwSLfoVMMl42z26tx1SRYEsxiEkAr4eY7tJZ267J29GEJCjmEcGby%2FvlPPCWyRPi--hqXSv%2FWQWD08h%2BC2--Y7uwn8oJpp7Gwi7g8CSlFQ%3D%3D"  # ← replace this with your real `_t` cookie string
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_ID = 34  # TDS KB category ID
DATA_FILE = "scraper/discourse_data.json"

def fetch_category_topics(category_id, max_pages=10):
    topics = []
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)

    for page in range(max_pages):
        url = f"{BASE_URL}/c/courses/tds-kb/{category_id}.json?page={page}"
        print(f"🔍 Fetching page {page}...")

        response = session.get(url)
        if response.status_code != 200:
            print(f"❌ Failed to fetch page {page}, status code: {response.status_code}")
            break

        try:
            data = response.json()
        except Exception as e:
            print(f"⚠️ JSON decoding error: {e}")
            break

        if "topic_list" not in data:
            print("⚠️ No topic_list in response.")
            break

        page_topics = data["topic_list"].get("topics", [])
        if not page_topics:
            print("✅ No more topics found.")
            break

        topics.extend(page_topics)
        sleep(0.5)  # Respectful delay

    return topics

def save_topics_to_file(topics, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(topics)} topics to {filepath}")

def main():
    print("🚀 Starting Discourse scraper...")
    topics = fetch_category_topics(CATEGORY_ID, max_pages=10)
    save_topics_to_file(topics, DATA_FILE)

if __name__ == "__main__":
    main()
