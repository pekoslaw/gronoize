# -*- coding: utf-8 -*-
"""Memcached cache backend

CACHE_PICKLE_PROTOCOL
CACHE_SPIED_KEYS
CACHE_MIN_COMPRESSION_LEN
"""

import logging
import pickle
import zlib

from django.conf import settings
from django.core.cache.backends.base import InvalidCacheBackendError
from django.core.cache.backends.memcached import CacheClass as MemcCacheClass
from django.utils.encoding import smart_str as _smart_str
from django.utils.encoding import smart_unicode

log = logging.getLogger(__name__)

try:
    from hash_ring import MemcacheRing as MemClient
except ImportError:
    from memcache import Client as MemClient


ANGRY_CHARACTERS = [' ', '"', "'", '\n', '<', '>']

def check_key(key):
    if any(map(lambda c: c in key, ANGRY_CHARACTERS)):
        raise ValueError('disallowed%s character in cache key %s' % (ANGRY_CHARACTERS, key))


def gm_smart_str(s):
    if isinstance(s, tuple):
        serverhash, key = s
        key = _smart_str(key)
        check_key(key)
        return (serverhash, key)
    else:
        check_key(s)
        return _smart_str(s)

def _parsekey(key):
    """ return (srv, k) """
    if isinstance(key, tuple):
        return key
    if isinstance(key, list):
        raise ValueError("Memcached key must be a string or tuple, not list! %s", key)
    else:
        return '-', key

def _ispiedkey(k):
    """ return True/False """
    spied_keys = getattr(settings, 'CACHE_SPIED_KEYS', [])
    for rx in spied_keys:
        if rx.match(k):
            return True
    return False

def _calcsize(val):
    """ return size of val - tylko przy poziomie DEBUG """
    dbgp_size = '-'
    if val is None:
        return dbgp_size
    if log.getEffectiveLevel() <= logging.DEBUG:
        dbgp = pickle.dumps(val, getattr(settings, 'CACHE_PICKLE_PROTOCOL', 0))
        dbgp_size = len(dbgp)
        if getattr(settings, 'CACHE_MIN_COMPRESSION_LEN', 0) <= dbgp_size:
            dbgp = zlib.compress(dbgp)
            dbgp_size = len(dbgp)
    return dbgp_size

class CacheClass(MemcCacheClass):
    def __init__(self, server, params):
        MemcCacheClass.__init__(self, server, params)
        self._cache = MemClient(server.split(';'), pickleProtocol=getattr(settings, 'CACHE_PICKLE_PROTOCOL', 0))

    def add(self, key, value, timeout=0):
        """ dodano debugowanie """

        ### value to utf8
        if isinstance(value, unicode):
            value = value.encode('utf-8')

        ### debug
        srv,k = _parsekey(key)
        if _ispiedkey(k):
            # wylicz size
            size = _calcsize(value)
            log.debug('ADD %s %s %s',k, srv, size)

        ### add
        return self._cache.add(gm_smart_str(key),
                               value,
                               timeout or self.default_timeout,
                               getattr(settings, 'CACHE_MIN_COMPRESSION_LEN', 0)
                               )

    def get(self, key, default=None):
        """
        Dodane logowanie wybranych kluczy (missing)

        info: brak klucza takiego i takiego
        debug: kazde odpytanie do cache
        """
        ### get value
        val = self._cache.get(gm_smart_str(key))

        ### debug
        srv,k = _parsekey(key)
        if _ispiedkey(k):
            # wylicz size
            size = _calcsize(val)
            # log
            if val is None:
                log.info("%s %s %s %s", 'MISS', k, srv, size)
            else:
                log.debug("%s %s %s %s", 'HIT', k, srv, size)

        # return value
        if val is None:
            return default
        else:
            if isinstance(val, basestring):
                return smart_unicode(val)
            else:
                return val


    def set(self, key, value, timeout=0, zip=True):
        """
        Dodany ficzer z min_compression_len, aby mozliwa byla kompresja duzych kluczy.
        """
        ### value to utf8
        if isinstance(value, unicode):
            value = value.encode('utf-8')

        srv,k = _parsekey(key)
        if _ispiedkey(k):
            # wylicz size
            size = _calcsize(value)
            # log
            log.debug("%s %s %s %s", 'SET', k, srv, size)

        ### set
        return self._cache.set(gm_smart_str(key),
                               value,
                               timeout or self.default_timeout,
                               getattr(settings, 'CACHE_MIN_COMPRESSION_LEN', 0) if zip else 0)

    def delete(self, key):
        """ normlane kasowanie + DEBUG + zwracanie wartosci """
        ### debug
        srv,k = _parsekey(key)
        if _ispiedkey(k):
            log.debug('DELETE %s %s',k, srv)

        ### delete
        return self._cache.delete(gm_smart_str(key))

    def get_many(self, keys):
        """ get many z obslugi sledzenia kluczy """
        spiedkeys = [k for k in  keys if _ispiedkey(k)]
        if spiedkeys:
            log.debug('GETMULTI %s', ','.join(spiedkeys) )
        return self._cache.get_multi(map(gm_smart_str, keys))

