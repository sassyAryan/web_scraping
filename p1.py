from bs4 import BeautifulSoup
import requests

URL = "https://www.zomato.com/ncr"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

page = requests.get(URL, headers=headers)
soup = BeautifulSoup(page.content, "html.parser")

print(soup.prettify())  