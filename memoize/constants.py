# coding: utf-8
"""Stale uzywane przez memoize i funkcje pomocnicze"""

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY

try:
    from django.conf import settings
    DEFAULT_TIMEOUT = settings.CACHE_DEFAULT_TIMEOUT
except Exception:
    DEFAULT_TIMEOUT = 2 * DAY   # Domyslny czas na jaki keszujemy

                                # Credits for special characters 
                                # used in MEMCACHE_NONE goes to Jiivan.
MEMCACHE_NONE = "ऋNoneद"        # Special value to have a distinction between
                                # real None and miss

