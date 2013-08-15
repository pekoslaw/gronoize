# -*- coding: utf-8 -*-

from django.core.cache.backends.dummy import CacheClass as DummyCache

class CacheClass(DummyCache):
    def validate_key(self, key):
        if isinstance(key, tuple):
            key = key[1]
        super(CacheClass, self).validate_key(key)

