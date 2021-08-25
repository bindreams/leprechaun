import sys
from itertools import count
import requests as rq
from cachetools import cached, TTLCache


@cached(TTLCache(maxsize=sys.maxsize, ttl=1200))
def rawassetprices(page=1):
    """Return a page of 500 asset prices. Switch page to get more results."""
    url = f"https://data.messari.io/api/v2/assets?fields=symbol,metrics/market_data/price_usd&limit=500&page={page}"
    page = rq.get(url)
    data = page.json()

    if "status" not in data:
        raise RuntimeError("Invalid address")

    return data


@cached(TTLCache(maxsize=sys.maxsize, ttl=1200))
def usdprice(symbol):
    """Return price in usd for cryptocurrency."""
    for page in count(1):
        data = rawassetprices(page)

        if len(data["data"]) == 0:
            raise ValueError(f"did not find price for currency '{symbol}'")

        for entry in data["data"]:
            if entry["symbol"] == symbol:
                return entry["metrics"]["market_data"]["price_usd"]


def usdprices(symbols):
    """Return prices in usd for symbols."""
    result = {}

    for symbol in symbols:
        result[symbol] = usdprice(symbol)
    
    return result
