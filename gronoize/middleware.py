#-*- coding: utf-8 -*-
"""
Middleware ten odpowiada za wyczyszczenie lokalnego cache przed i po requescie.
"""

from gronoize.utils import localcache_clear

class ClearLocalCacheMiddleware(object):
    def process_request(self, request):
        """Czyszczenie przy rozpoczeciu"""
        localcache_clear()
        
    def process_response(self, request, response):
        """Czyszczenie przy zakonczeniu"""
        localcache_clear()
        return response

