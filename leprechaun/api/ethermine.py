import sys
import requests as rq
from cachetools import cached, TTLCache

currency_precision = 18

@cached(TTLCache(maxsize=sys.maxsize, ttl=120))
def request(page, addr):
    url = f"https://api.ethermine.org/miner/{addr[2:]}/{page}"
    page = rq.get(url)
    page.raise_for_status()
    data = page.json()

    if data["status"] != "OK":
        raise RuntimeError(data["error"])

    return data["data"]

def payouts(addr):
    return request("payouts", addr)

def stats(addr):
    return request("currentStats", addr)

def dashboard(addr):
    return request("dashboard", addr)

def totalpaid(addr):
    data = payouts(addr)

    total = 0
    for entry in data:
        total += entry["amount"]

    total /= 10**currency_precision
    return total

def totaldue(addr):
    data = dashboard(addr)

    total = data["currentStatistics"].get("unpaid", 0) / 10**currency_precision
    return total
