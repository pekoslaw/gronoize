#-*- coding: utf-8 -*-

"""Dostęp do memcache, pobieranie i usuwanie przechowywanych w nim danych. Logika cache poziomu 1,
kolejkowanie dostępu.
"""

import sys

import logging
import random
from copy import deepcopy
from django.conf import settings
from django.core.cache import cache
from gronoize.constants import MEMCACHE_NONE

log = logging.getLogger(__name__)

try:
    PREFIX = settings.CACHE_PREFIX
except Exception:
    PREFIX = ""

# Dane localmemoize
local_memoize_cache = {}

## Zarzadzanie Memoize, blokowanie i odblokowanie (kolejkowanie wpisow), cofniecie kolejki
blocked = False
queue = {}

## Funkcje podstawowe
def gen_version():
    """Generator wersji dla powiazania kluczy i vkluczy

    :return: numer wersji, czyli losowa liczba całkowita
    :rtype: int
    """
    return random.randint(0, sys.maxint)

def localcache_put(key, value):
    """Wklada dane do localcache.

    :param key: klucz pod którym zostaną zapamiętane dane
    :type key: str
    :param value: dane do zapamiętania
    """
    global local_memoize_cache
    local_memoize_cache[key] = value

def localcache_put_dict(values_dict):
    """Wklada dane do localcache.

    :param key: slownik z danymi do zapamietania
    :type key: dict
    """
    global local_memoize_cache
    local_memoize_cache.update(values_dict)

def localcache_get(key, use_deepcopy=True):
    """Pobranie danych z cache lokalnego

    :param key: klucz danych
    :type key: str
    :return: zapisane dane lub MEMCACHE_NONE jesli wrzucone bylo None
    """
    global local_memoize_cache

    # Sprawdzenie czy mamy dane w cache lokalnym
    if key not in local_memoize_cache:
        return

    if use_deepcopy:
        result = deepcopy(local_memoize_cache[key])
    else:
        result = local_memoize_cache[key]

    if isinstance(result, dict):
        if result.get('vkey') and result.get('version'):
            desired_version = localcache_get(result.get('vkey'), use_deepcopy=use_deepcopy)
            if desired_version != result['version']:
                return
        # Zwrocenie wynikow
        return result

    log.debug("LGET %r=%r", key, result)

    # Zwrocenie wynikow
    return result

def get(key, l1=True, use_deepcopy=True):
    """Funkcja pobiera dane dla podanego klucza z memoize.

    :param key: klucz pod ktorym trzymamy dane
    :type key: str
    :param l1: czy uzywac cache lokalnego (dicta o czasie życia równym czasowi
              życia jednej instancji django)
    :type l1: bool

    :return: - dane zapisane w memoize lub MEMCACHE_NONE jesli wrzucone bylo None
    """
    #global local_memoize_cache

    # wydobycie danych z LocalCache
    if l1:
        result = localcache_get(key, use_deepcopy=use_deepcopy)
        if result:
            # Jesli w wynikach jest vkey rozny od oczekiwanego
            log.debug("GET (l) %r=%r", key, result)

            # Wkładając dane do cache za pomocą put() zawsze wkładamy dicta.
            # Ten warunek zabezpiecza przed pobraniem jakiegoś vkey
            # trzymanego jako int.
            if isinstance(result, int):
                return
            elif result.get('vkey') and result.get('version'):
                desired_version = _get(result['vkey'], use_deepcopy=use_deepcopy)
                if desired_version != result['version']:
                    return
            return result['value']

    # wydobycie danych z MemCache
    result = cache.get(key)
    log.debug("FROM CACHE: %r", result)
    if not result:
        return

    # Sprawdzamy czy w odpowiedniej wersji
    if result.get('vkey') and result.get('version'):
        desired_version = _get(result['vkey'], False, use_deepcopy=use_deepcopy)
        if desired_version != result['version']:
            return

    # Wrzucenie do cache lokalnego i zwrocenie wyniku
    if l1:
        localcache_put(key, result)
        #local_memoize_cache[key] = result
    log.debug("GET %r=%r", key, result)
    return result['value']

def _put(key, value, timeout=0, l1=True, optionaladd=False):
    """Funkcja wrzucajaca dane bezposrednio do cache.

    :param key: klucz pod ktory wrzucamy dane.
    :type key: str
    :param value: dane do wrzucenia - jesli None to zamieniamy na MEMCACHE_NONE
    :param timeout: ilosc sekund trzymania danych w cache
    :type timeout: int
    :param l1: czy trzymać dane również w keszu lokalnym
    :type l1: bool

    jesli cache cos zwraca z metody add/set to tez to zwracamy (w celach testowych)
    """
    #global local_memoize_cache

    if value is None:
        value = MEMCACHE_NONE
    log.debug("_PUT %r=%r", key, value)

    # opcjonalne dodanie elementu do cache tylko wtedy jesli go jeszcze nie ma
    if optionaladd:
        resp = cache.add(key, value, timeout)
    else:
        resp = cache.set(key, value, timeout)

    if l1:
        localcache_put(key, deepcopy(value))
        #local_memoize_cache[key] = deepcopy(value)
    return resp

def _get(key, l1=True, use_deepcopy=True):
    """Pobiera dane z cache, lub localcache.
    :param key: lucz pod którym są dane
    :type key: str
    :param l1: czy szukać najpierw w localcache
    :type l1: bool
    """
    #global local_memoize_cache

    # wydobycie danych z LocalCache
    if l1:
        result = localcache_get(key, use_deepcopy=use_deepcopy)
        if result:
            return result

    # wydobycie danych z MemCache
    result = cache.get(key)
    log.debug("_GET %r=%r", key, result)
    if not result:
        return

    # Wrzucenie do cache lokalnego i zwrocenie wyniku
    if l1:
        localcache_put(key, result)
        #local_memoize_cache[key] = result
    return result


def _get_many(keys, l1=True, use_deepcopy=True):
    """Pobiera dane z cache, lub localcache.
    :param keys: klucze pod którymi są dane
    :type key: str
    :param l1: czy szukać najpierw w localcache
    :type l1: bool
    """
    results = {}

    # wydobycie danych z LocalCache
    if l1:
        for key in keys:
            result = localcache_get(key, use_deepcopy=use_deepcopy)
            if result:
                results[key] = result

    # wydobycie danych z MemCache
    cache_results = cache.get_many([k for k in keys if k not in results])
    if cache_results:
        # Wrzucenie do cache lokalnego i zwrocenie wyniku
        if l1:
            localcache_put_dict(cache_results)

        results.update(cache_results)

    return results


def put(key, value, timeout=0, vkey=None, l1=True, optionaladd=False):
    """Funkcja wrzucajaca dane do memoize.

    :param key: klucz pod ktory wrzucamy dane
    :type key: str
    :param value: dane do wrzucenia - jesli None to zmieniamy na MEMCACHE_NONE
    :param l1: czy rzucic do lokalnego cache
    :type l1: bool
    :param timeout: ilosc sekund trzymania danych w cache
    :type timeout: int
    :param optionaladd: set wykonuje sie opcjonalnie - rowiazuje problem wyscikow w memoize
    """
    #global local_memoize_cache
    log.debug("PUT %r=%r", key,value)
    value_dict = dict(value=None, vkey=None, version=None)
    value_dict['vkey'] = vkey

    if value is None:
        value = MEMCACHE_NONE

    if vkey:
        # przy kluczu wersji tworzymy nowa wersje i wrzucamy do memoize
        current_version = _get(vkey, l1)
        if not current_version:
            current_version = gen_version()
            _put(vkey, current_version, timeout, l1, optionaladd)
        value_dict['version'] = current_version

    # Reszta w obydwu przypadkach tak samo
    value_dict['value'] = value
    log.debug("PUT %r = dict: %r", key, value_dict)

    # opcjonalne dodanie do cache
    if optionaladd:
        resp = cache.add(key, value_dict, timeout)
    else:
        resp = cache.set(key, value_dict, timeout)

    if l1:
        localcache_put(key, deepcopy(value_dict))
        #local_memoize_cache[key] = deepcopy(value_dict)
    return resp


def get_many(keys, l1=True, use_deepcopy=True):
    """Funkcja pobiera dane dla podanych kluczy z memoize.

    :param keys: klucze pod ktorymi trzymamy dane
    :type key: str
    :param l1: czy uzywac cache lokalnego (dicta o czasie życia równym czasowi
              życia jednej instancji django)
    :type l1: bool

    :return: - slownik, ktorego kluczami sa klucze przekazane przez parametr keys,
               a wartosciami sa dane zapisane w memoize pod tymi kluczami lub
               MEMCACHE_NONE jesli wrzucone bylo None
    """
    results = {}
    l1_vkeys = set()
    l1_vkeys_results = {}

    # wydobycie danych z LocalCache
    if l1:
        l1_results = {}

        for key in keys:
            result = localcache_get(key, use_deepcopy=use_deepcopy)
            if result:
                # Wkładając dane do cache za pomocą put() zawsze wkładamy dicta.
                # Ten warunek zabezpiecza przed pobraniem jakiegoś vkey
                # trzymanego jako int.
                if isinstance(result, int):
                    continue

                l1_results[key] = result

        # pobieramy klucze
        l1_vkeys = set([v.get('vkey') for v in l1_results.itervalues() if v.get('vkey') and v.get('version')])
        l1_vkeys_results = _get_many(l1_vkeys, use_deepcopy=use_deepcopy)

        # sprawdzamy poprawnosc pobranych danych z localcache
        for (k, v) in l1_results.iteritems():
            if v.get('version') and v.get('vkey'):
                if v.get('version') != l1_vkeys_results.get(v.get('vkey')):
                    continue
            results[k] = v

    # wydobycie danych z MemCache (czego nie dalo sie wyciagnac z localcache)
    cache_results = cache.get_many([k for k in keys if k not in results])
    if cache_results:
        # dociagamy klucze wersji, ktorych jeszcze nie mamy
        cache_vkeys = set([v.get('vkey') for v in cache_results.itervalues() if v.get('vkey') and
                                                                                v.get('version') and
                                                                                v.get('vkey') not in l1_vkeys])
        cache_vkeys_results = _get_many(cache_vkeys, False, use_deepcopy=use_deepcopy)
        cache_vkeys_results.update(l1_vkeys_results)

        # sprawdzenie poprawnosci wersji danych
        valid_cache_results = {}
        for (k, v) in cache_results.iteritems():
            if v.get('version') and v.get('vkey'):
                if v.get('version') != cache_vkeys_results.get(v.get('vkey')):
                    continue
            valid_cache_results[k] = v

        if l1:
            localcache_put_dict(valid_cache_results)

        results.update(valid_cache_results)

    # pozostawiam w wynikowym slowniku jedynie dane
    # i usuwam smiecie dotyczace wersji
    final_dict = {}
    for (k, v) in results.iteritems():
        final_dict[k] = v['value'] if v is not None else None

    return final_dict


def delete(*keys):
    """Kasowanie wielu danych na raz z memoize

    :param keys: lista kluczy do skasowania
    """
    return invalidate(*keys)

def invalidatev(*keys, **kwargs):
    """Inwalidacja listy kluczy wersji poprzez ustawienie im nowej wartosci (przez co inwalidujemy wszystkie powiazane dane).

    :param keys: lista kluczy wersji do inwalidacji

    jesli cache cos zwraca z metody add/set to tez to zwracamy (w celach testowych)
    """
    #global local_memoize_cache
    resps = []
    for key in keys:
        v = gen_version()
        resps.append( cache.set(key, v) )
        localcache_put(key, v)
        #local_memoize_cache[key] = v
    return resps

def invalidate(*keys, **kwargs):
    """Inwalidacja danych ukrytych pod kluczem poprzez usuniecie ich z listy.

    :param keys: lista kluczy do inwalidacji
    """
    global local_memoize_cache

    resps = []
    for key in keys:
        resps.append( cache.delete(key) )
        if key in local_memoize_cache:
            del local_memoize_cache[key]
    return resps

def localcache_clear():
    """Czysci lokalny cache. Uzywane przez middleware, ktory czysci pamiec
    na poczatku requesta, i po jego zakonczeniu"""
    global local_memoize_cache
    local_memoize_cache = {}

