# coding: utf-8

import logging
from functools import wraps
from gronoize.constants import DEFAULT_TIMEOUT
from gronoize.constants import MEMCACHE_NONE
from gronoize.utils import get
from gronoize.utils import put

u"""
MEMOIZE 3.0.½

  Original idea: Marek Pułczyński
  Author: Łukasz 'pax' Żukowski
  Port and modifications: Mateusz 'matee' Pawlik
  Other contributors:
    - Paweł Pałucki (deepcopy, optionaladd, MEMOIZE_REFRESH)
    - Piotr Czesław Kalmus
    - Kamil Kieda
"""


log = logging.getLogger(__name__)

def memoize(key_function, vkey_function=None, timeout=DEFAULT_TIMEOUT,
            allow_none=False, l1=True, use_deepcopy=True, optionaladd=False):
    """
    Dekorator, ktory kaszuje wynik funkcji i zapisuje w memcached pod wskazanym kluczem.
      :key_function: funkcja, ktora przeksztalca args i kwargs na klucz do memcache,
                     jesli ta funkcja zwroci None zapytanie NIE JEST KESZOWANE
      :vkey_function: ---
      :l1: czy keszowac i inwalidowac wyniki w lokalnym keszu per resquest (WYMAGA MIDDELWARE!)
      :use_deepcopy: ---
      :timeout: maksymalny czas ważności danych w memkeszu (uwaga - memcached nie gwarantuje
                przechowywania danych aż do timeoutu)
      :optionaladd: - powoduje warunkowe wlozenie elementu, tylko wtedy jesli go jeszcze nie ma w cache
                    (rozwiazuje problem wyscigow i podwojne wkladanie wartosci przez dwa rownolegle procey)
      :MEMOIZE_REFRESH: - wymusza zaladowanie do cache nowych danych
    """
    def decorator(f):
        @wraps(f)
        def _wrapper(*args, **kwargs):
            add_to_cache = optionaladd

            # 1. Utworzenie kluczy
            key = key_function
            vkey = vkey_function
            time_out = timeout

            # opcjonalny argument MEMOIZE_REFRESH powoduje pominięcie cache
            # przy odczycie i wymuszenie zapisu danych do cache
            refresh = False
            if kwargs.has_key('MEMOIZE_REFRESH'):
                add_to_cache = False
                refresh = kwargs['MEMOIZE_REFRESH']
                del kwargs['MEMOIZE_REFRESH']

            if callable(key_function):
                key = key_function(*args, **kwargs)

            if key is not None:
                if callable(vkey_function):
                    vkey = vkey_function(*args, **kwargs)

                if callable(timeout):
                    time_out = timeout()

                log.debug("KEY %s", key)

                if not refresh:
                    # 2. Pobranie danych z memoize i zwrocenie jesli je mamy
                    result = get(key, l1, use_deepcopy=use_deepcopy)
                    if result is not None or result == MEMCACHE_NONE:
                        if result == MEMCACHE_NONE:
                            return
                        log.debug("Z CACHE")
                        return result

            # 3. Generowanie danych na nowo
            result = f(*args, **kwargs)

            if not allow_none and result is None:
                return

            if key is not None:
                put(key, result, time_out, vkey, l1, add_to_cache)

            return result
        return _wrapper
    return decorator

