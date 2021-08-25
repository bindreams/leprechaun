import sys
import requests as rq
from cachetools import cached, TTLCache

currency_precision = 12

@cached(TTLCache(maxsize=sys.maxsize, ttl=60))
def stats(addr):
    url = f"https://supportxmr.com/api/miner/{addr}/stats"
    page = rq.get(url)
    data = page.json()

    return data

def totalpaid(addr):
    data = stats(addr)
    total = data["amtPaid"] / 10**currency_precision
    return total

def totaldue(addr):
    data = stats(addr)
    total = data["amtDue"] / 10**currency_precision
    return total
