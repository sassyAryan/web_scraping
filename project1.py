
import requests
import time
import random
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from fake_useragent import UserAgent


ua = UserAgent()



TICKERS = [
    "AAPL","MSFT","TSLA","AMZN","GOOG","NVDA","META","NFLX","INTC","AMD",
    "ADBE","PYPL","CSCO","ORCL","IBM","PEP","KO","NKE","MCD","WMT",
    "UNH","JNJ","V","MA","PG","HD","DIS","XOM","CVX","BAC",
    "C","GS","MS","T","VZ","PFE","MRK","ABBV","LLY","BMY",
    "BA","CAT","GE","F","GM","UPS","FDX","COST","TGT","SBUX"
]  

OUT_CSV = "yahoo_50_stocks.csv"
MIN_DELAY = 1.0   
MAX_DELAY = 3.0   
TIMEOUT = 10      



def build_session(max_retries=3, backoff_factor=0.5):
    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def get_headers():
    headers = {
        "User-Agent": ua.random,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com"
    }
    return headers

def fetch_ticker(session, ticker):
    """
    Fetches the Yahoo chart endpoint for a ticker and returns a dict with core fields.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    try:
        r = session.get(url, headers=get_headers(), timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Request for {ticker} failed: {e}")
        return None

    try:
        j = r.json()
    except ValueError:
        print(f"[ERROR] Invalid JSON for {ticker}")
        return None

    # The JSON structure can vary if the ticker is invalid or blocked
    chart = j.get("chart", {})
    results = chart.get("result")
    if not results:
        print(f"[WARN] No result for {ticker} - possible invalid ticker or temporary block.")
        return None

    res = results[0]
    meta = res.get("meta", {})
    indicators = res.get("indicators", {})
    quote = indicators.get("quote", [{}])[0]

    def safe_get(d, key, default=None):
        return d.get(key, default) if isinstance(d, dict) else default

    out = {
        "symbol": ticker,
        "regularMarketPrice": safe_get(meta, "regularMarketPrice"),
        "previousClose": safe_get(meta, "previousClose"),
        "currency": safe_get(meta, "currency"),
        "exchangeName": safe_get(meta, "exchangeName"),
        "marketState": safe_get(meta, "marketState"),
        # Latest price/time from quote arrays (may be lists of historical values)
        "last_open": None,
        "last_high": None,
        "last_low": None,
        "last_close": None,
        "last_volume": None,
        "regularMarketTime": safe_get(meta, "regularMarketTime")
    }

    # indicators.quote contains lists that correspond to timestamps; take last non-None element
    def last_non_none(lst):
        if not isinstance(lst, list):
            return None
        for x in reversed(lst):
            if x is not None:
                return x
        return None

    out["last_open"] = last_non_none(quote.get("open"))
    out["last_high"] = last_non_none(quote.get("high"))
    out["last_low"] = last_non_none(quote.get("low"))
    out["last_close"] = last_non_none(quote.get("close"))
    out["last_volume"] = last_non_none(quote.get("volume"))

    return out

def main():
    session = build_session(max_retries=4, backoff_factor=1)
    rows = []
    for i, ticker in enumerate(TICKERS, start=1):
        print(f"[{i}/{len(TICKERS)}] Fetching {ticker} ...")
        result = fetch_ticker(session, ticker)
        if result:
            rows.append(result)
            print(f"  → {ticker} price: {result['regularMarketPrice']}")
        
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)

    if not rows:
        print("No data fetched. Exiting.")
        return

    df = pd.DataFrame(rows)
   
    if "regularMarketTime" in df.columns:
        df["regularMarketTime"] = pd.to_datetime(df["regularMarketTime"], unit="s", errors="coerce")

    
    df.to_csv(OUT_CSV, index=False)
    print(f"\nSaved {len(df)} rows to {OUT_CSV}")

if __name__ == "__main__":
    main()
