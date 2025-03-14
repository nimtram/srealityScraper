import requests
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime
import sys

# Discord webhook URLs
NEW_LISTINGS_WEBHOOK_URL = "https://discord.com/api/webhooks/1347919755402805334/U3rNngNL6xVRhmBUDPQfOed6HroFTgDGEzHXFlnhNP-s4t7n2qtjvj_HQBIdamhjlCHW"
REMOVED_LISTINGS_WEBHOOK_URL = "https://discord.com/api/webhooks/1347921188562931763/2_G_tATk3-wSCrSxZIW_qTN8mCgk5zl8-PBxtyYnteHmU7Rb8ZJ4Lit6gc73fCRx-tp8"
STATUS_WEBHOOK_URL = "https://discord.com/api/webhooks/1347921782296023041/TV8VRdw77kWzf1W5ygqYewpIJH8YnVyIyJNghKmnaxLGu4uWvc9h_-g50XS7IaHqh70U"

# File to store listings
DATA_FILE = "byty.json"

# Base URL for Sreality listings search
BASE_URL = "https://www.sreality.cz/hledani/prodej/byty/praha-6?velikost=1%2B1%2C2%2B1%2C2%2Bkk&vlastnictvi=osobni&cena-do=7300000"

def get_listing_links(page_url):
    """Load the page and return a list of links to apartment listings"""
    response = requests.get(page_url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code != 200:
        print(f'Error loading page {page_url}: {response.status_code}')
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []

    # Find all apartment listing links on the page
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/detail/prodej/byt' in href:  # Only apartment links
            full_url = 'https://www.sreality.cz' + href
            links.append(full_url)

    return list(set(links))  # Remove duplicates

def load_saved_listings():
    """Load previously saved listings from the JSON file"""
    file_path = os.path.abspath(DATA_FILE)  # Získá absolutní cestu k souboru
    print(f"Looking for the file at: {file_path}")  # Vypíše absolutní cestu k souboru
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                saved_data = json.load(f)
                if isinstance(saved_data, dict) and "listings" in saved_data and "total_count" in saved_data:
                    print(f"Total count loaded: {saved_data['total_count']}")  # Vypíše hodnotu total_count
                    return saved_data
                else:
                    print("Structure is incorrect, returning default values.")
                    return {"listings": [], "total_count": 0}  # Default if structure is incorrect
            except json.JSONDecodeError:
                print("Error decoding JSON, returning default values.")
                return {"listings": [], "total_count": 0}  # Handle invalid JSON format
    else:
        print("File does not exist, returning default values.")
        return {"listings": [], "total_count": 0}  # Default if file doesn't exist


def save_listings(listings, total_count):
    """Save current listings and total count to a JSON file"""
    file_path = os.path.abspath(DATA_FILE)  # Získá absolutní cestu k souboru
    print(f"Saving to the file at: {file_path}")  # Vypíše absolutní cestu k souboru
    data = {"listings": listings, "total_count": total_count}
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
            print("Listings successfully saved.")
    except Exception as e:
        print(f"Error saving listings: {e}")

def send_discord_notification(webhook_url, message):
    """Send a message to Discord"""
    payload = {"content": message}
    response = requests.post(webhook_url, json=payload)

    if response.status_code != 204:
        print(f"Error sending message: {response.status_code}")
    else:
        print(f"Message sent successfully to {webhook_url}")

def send_status_message(total_count):
    """Send status message to Discord every hour"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"Počet bytů: {total_count}\nKontrola byla spuštěna v {current_time}"
    send_discord_notification(STATUS_WEBHOOK_URL, message)

def main():
    """Main function - checks and saves the apartment listings"""
    all_links = []
    page = 1

    # Load current apartment listings
    while True:
        page_url = BASE_URL + f'&strana={page}'
        print(f'Processing page {page}...')
        
        links = get_listing_links(page_url)
        if not links:
            print(f'End! Page {page} does not contain any apartments.')
            break
        
        all_links.extend(links)
        page += 1

    all_links = list(set(all_links))  # Remove duplicates
    total_count = len(all_links)

    # Load previously saved listings
    saved_data = load_saved_listings()
    saved_listings = saved_data["listings"]
    saved_total_count = saved_data["total_count"]

    # Compare changes
    new_listings = list(set(all_links) - set(saved_listings))
    removed_listings = list(set(saved_listings) - set(all_links))

    # If there are new listings, send a notification to the "new listings" webhook
    if new_listings:
        new_message = f"Nové nabídky:\n" + "\n".join(new_listings)
        send_discord_notification(NEW_LISTINGS_WEBHOOK_URL, new_message)

    # If some listings were removed, send a notification to the "removed listings" webhook
    if removed_listings:
        removed_message = f"Smazané nabídky:\n" + "\n".join(removed_listings)
        send_discord_notification(REMOVED_LISTINGS_WEBHOOK_URL, removed_message)

    # Save the new listings and total count
    save_listings(all_links, total_count)

    # Send hourly status message
    send_status_message(total_count)

    print(f"Total apartments found: {total_count}.")

if __name__ == "__main__":
    message = "Bot byl spuštěn."
    send_discord_notification(STATUS_WEBHOOK_URL, message)
    while True:
        main()
        time.sleep(1800)


