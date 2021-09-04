import sys
from typing import Iterable
import requests as rq
from cachetools import cached, TTLCache


@cached(TTLCache(maxsize=sys.maxsize, ttl=60))
def _impl_stats(coins: str):
    """Query minerstat for coin information. Return unmodified data if no error was raised."""
    url = f"https://api.minerstat.com/v2/coins?list={coins}"
    page = rq.get(url)
    page.raise_for_status()
    data = page.json()
    return data

def stats(coins: Iterable):
    """Query minerstat for coin information. Return a list of dicts with info.

    See https://api.minerstat.com/docs-coins/documentation for more information.
    """
    return _impl_stats(",".join(sorted(coins)))
