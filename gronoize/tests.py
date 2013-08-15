#-*- coding: utf-8 -*-

from gronoize.constants import MEMCACHE_NONE
from gronoize.decorators import memoize
from gronoize.utils import _get
from gronoize.utils import delete
from gronoize.utils import get
from gronoize.utils import get_many
from gronoize.utils import invalidate
from gronoize.utils import invalidatev
from gronoize.utils import localcache_clear
from gronoize.utils import localcache_get
from gronoize.utils import localcache_put
from gronoize.utils import put


# Testy
if __name__ == "__main__":
    import unittest
    from time import sleep

    class Memoize2TestCase(unittest.TestCase):
        """Klasa testujaca biblioteke memoize2
        """

        def setUp(self):
            self.key_prefix = "__memoize__unittest5."
            self.to_delete = []


        def tearDown(self):
            global local_memoize_cache
            if self.to_delete:
                delete(*self.to_delete)


        # Test StandardApi
        def testStandardApiBase(self):
            """Test dla funkcji put i get bez zadnych dodatkowych ustawien
            """
            key = self.key_prefix + "StandardApi.Base"
            self.to_delete.append(key)
            data = "proba"

            # Sprawdzenie czy po wrzuceinu do cache otrzymam dane spowrotem (bez cache lokalnego)
            put(key, data, 0, None, False)
            gdata = get(key, False)
            self.assertEqual(data, gdata, u"Blad zwracanych danych z memoize: %s != %s" % (data, gdata))

            # Ten sam test tylko z cache lokaklnym
            put(key, data)
            gdata = get(key)
            self.assertEqual(data, gdata, u"Blad zwracanych danych z memoize: %s != %s" % (data, gdata))


        def testStandardApiTimeout(self):
            """Test dla funkcji put i get z timeout (localcache False bo on nie ma timeout tylko memcache)
            """
            key1 = self.key_prefix + "StandardApi.timeout.k1"
            key2 = self.key_prefix + "StandardApi.timeout.k2"
            self.to_delete.extend([key1, key2])
            data = "proba"

            # dlugi timeout ktorego nie przekroczymy
            put(key1, data, 100, None, False)
            gdata = get(key1, False)
            self.assertEqual(data, gdata, u"Błąd zwracanych danych z memoize. 100 sekund jeszcze chyba nie upłuneło. [data=%s, gdata=%s]" % (data, gdata))

            # przekroczenie timeoutu i sprawdzenei czy invalidowalo dane
            put(key2, data, 1, None, False)
            sleep(2)
            gdata = get(key2, False)
            self.assertNotEqual(data, gdata, u"Memoize zwrócił dane a powinny być już przeterminowane. [data=%s, gdata=%s]" % (data, gdata))


        def testStandardApiVkey(self):
            """Test dzialania danych powiazanych kluczemwersji
            """
            vkey = self.key_prefix + "StandardApi.vkey.vkey"
            key1 = self.key_prefix + "StandardApi.timeout.k1"
            key2 = self.key_prefix + "StandardApi.timeout.k2"
            data = "vkey-test"
            self.to_delete.extend([key1, key2, vkey])

            # Wrzucamy dane do obu kluczy (z vkey) i pobieramy je
            put(key1, data, 0, vkey, False)
            put(key2, data, 0, vkey, False)

            for key in (key1, key2):
                gdata = get(key, False)
                self.assertEqual(data, gdata, u"Problem z danymi w memoize. key=%s, %s != %s" % (key, data, gdata))

            # Sprawdzamy czy dane wrzucone do cache dobrze zostaly zapisane
            gdata = _get(key1, False)
            #self.assertTrue(isinstance(gdata, tuple), u"Dane w cache powinny miec krotke przy vkey. gdata=%s" % str(gdata)) # Wcale ze nie
            self.assertTrue(isinstance(gdata, dict), u"Dane w cache powinny byc w slowniku przy vkey. gdata=%s" % str(gdata))
            gdata = get(key1, False)
            self.assertEqual(data, gdata, u"Problem z danymi w memoize. gdata=%s" % str(gdata))

            # incalidujemy klucz wersi i sprawdzamy czy invalidowalo klucze
            invalidatev(vkey)
            self.assertNotEqual(data, get(key1, False), u"Dane w cache salej sa mimo invalidate")
            self.assertNotEqual(data, get(key2, False), u"Dane w cache salej sa mimo invalidate")


        def testStandardApiNone(self):
            """Test sprawdzajacy wrzucanie None do cache
            """
            key = self.key_prefix + "StandardApi.none"
            self.to_delete.append(key)

            # Wrzucamy none i sprawdamy czy odpowie mi MEMCACHE_NONE
            put(key, None)
            gdata = get(key)
            self.assertEqual(gdata, MEMCACHE_NONE, u"Dane w cache inne niz oczekiwalismy.")


        def testStandardApiLocalCache(self):
            """Testujemy obsluge localcache
            """
            key1 = self.key_prefix + "StandardApi.local_cache.k1"
            key2 = self.key_prefix + "StandardApi.local_cache.k2"
            vkey = self.key_prefix + "StandardApi.local_cache.vkey"
            self.to_delete.extend([key1, key2, vkey])
            data = "test_local_cache"

            # Wrzucamy dane do cache lokalnego i pobieramy
            localcache_put(key1, data) #local_memoize_cache[key1] = data
            gdata = localcache_get(key1)
            self.assertEqual(gdata, data, u"Dane w cache sa inne: %s != %s" % (data, gdata))
            invalidate(key1)

            # Wrzucamy dane
            data = (1, data)

            localcache_put(vkey, 1) #local_memoize_cache[vkey] = 1
            localcache_put(key1, data) #local_memoize_cache[key1] = data
            localcache_put(key2, data) #local_memoize_cache[key2] = data

            gdata = localcache_get(key1)
            self.assertEqual(data[1], gdata[1], u"Dane w cache sa inne: %s != %s" % (data[1], gdata[1]))

            # invalidujemy vkey
            invalidatev(vkey)

            gdata = localcache_get(key1)
            self.assertNotEqual(data[1], gdata, u"Dane w cache nie zostaly zinvalidowane")

        def testLocalcacheClear(self):
            """Test czyszczenia lokalnego cache"""
            key = self.key_prefix + "localcache.k1"
            test_data = 'test-localclear'
            put(key, test_data, l1=True)
            data = localcache_get(key)

            self.assertEqual(data['value'] if isinstance(data, dict) else data, test_data, "Dane w lokalnym keszu sa rozne od danych wejsciowych %s=%s" % (data, test_data))

            localcache_clear()
            data = localcache_get(key)
            self.assertEqual(data, None, "Nie dziala czyszczenie lokalnego cache")


        def testDecorate(self):
            """Test dekoratora klasycznego memoize
            """
            key = self.key_prefix + "memoize.k1"
            vkey = self.key_prefix + "memoize.vkey"
            self.to_delete.append(key)

            # test klasycznego memoize bez zadnych dodatkowych opcji
            self.data = 2
            @memoize(key)
            def test1(a):
                self.data += 2
                return a**self.data

            self.assertEqual(test1(2), test1(2), u"dane w cache rozne  test1=%s  test2=%s" % (test1(2), test1(2)))
            delete(key)


            # test klasycznego memoize z vkey
            self.data=2
            @memoize(key, vkey)
            def test4(a):
                self.data += 2
                return a**self.data

            gdata = test4(2)
            invalidatev(vkey)
            gdata2 = test4(2)
            self.assertNotEqual(gdata2, gdata, u"Nie zinvalidowalo vkey")

            # test timeout memoize
            delete(key, vkey)
            @memoize(key_function=key, vkey_function=None, timeout=1, allow_none=False, l1=False)
            def test5(a):
                self.data += 2
                return a**self.data
            gdata = test5(2)
            sleep(2)
            self.assertNotEqual(test5(2), gdata, u"Nie usunieto danych z cache")

        def testMany(self):
            keys = [self.key_prefix + "StandardApi.Many.%d" % i for i in range(100)]
            self.to_delete.extend(keys)
            data = "proba"

            # Sprawdzenie czy po wrzuceinu do cache otrzymam dane spowrotem (bez cache lokalnego)
            for key in keys:
                put(key, data, 0, None, False)
            gdata = get_many(keys, False)
            self.assertEqual(len(gdata), len(keys), u"Zwrócono jedynie %d z %d elementów." % (len(data), len(keys)))
            for (k, v) in gdata.iteritems():
                self.assertEqual(data, v, u"Blad zwracanych danych z memoize: %s != %s" % (data, v))

            # Ten sam test tylko z cache lokaklnym
            for key in keys:
                put(key, data)
            gdata = get_many(keys)
            self.assertEqual(len(gdata), len(keys), u"Zwrócono jedynie %d z %d elementów." % (len(data), len(keys)))
            for (k, v) in gdata.iteritems():
                self.assertEqual(data, v, u"Blad zwracanych danych z memoize: %s != %s" % (data, v))

    unittest.main()
    import sys
    sys.exit(0)

    @memoize(lambda a, b : "%splus%s" % (a,b), timeout = 1 )
    def test1(a, b):
        return a + b

    def test2(a, b):
        return a * b

    def group_vkey(a,b ):
        return "dupa" + str(a)

    @memoize(lambda a, b : "%rdo%s" % (a,b), group_vkey, timeout = 1 )
    def test3_1(a,b):
        return a**b

    @memoize(lambda a, b : "%rna%s" % (a,b), group_vkey, timeout = 1 )
    def test3_2(a,b):
        return a/b

    @memoize(lambda a, b : "%rnaa%s" % (a,b), group_vkey, timeout = 1 )
    def raising(a, b):
        raise Exception("dupa")


    """
 memoize    DEBUG     memoize:101       MISS [5plus4]
 memoize    DEBUG     memoize:105       HIT [5plus4]
 memoize    DEBUG     memoize:101       MISS [3razy6]
 memoize    DEBUG     memoize:108       Forced MISS [3razy6] - regenerating
 memoize    DEBUG     memoize:105       HIT [3razy6]
 memoize    DEBUG     memoize:105       HIT [3razy6]
 memoize    DEBUG     memoize:120       NOVERSION - regenerating version from 1do2 to 27460653
 memoize    DEBUG     memoize:127       VMISS (object not in memcache) [1do2], setting to v27460653
 memoize    DEBUG     memoize:127       VMISS (object not in memcache) [1do3], setting to v27460653
 memoize    DEBUG     memoize:127       VMISS (object not in memcache) [2na2], setting to v310000875
 memoize    DEBUG     memoize:127       VMISS (object not in memcache) [2na3], setting to v310000875
 memoize    DEBUG     memoize:130       VHIT [1do2] v27460653
 memoize    DEBUG     memoize:130       VHIT [1do3] v27460653
 memoize    DEBUG     memoize:127       VMISS (object not in memcache) [2na2], setting to v1235160207
 memoize    DEBUG     memoize:127       VMISS (object not in memcache) [2na3], setting to v1235160207
    """

    test2 = memoize(lambda a, b : "%srazy%s" % (a,b), timeout = 1)(test2)

    test1(5, 4) # MISS
    test1(5, 4) # HIT
    test2(3, 6) # MISS
    test2(3, 6, __force_cache_invalidate_in_place = True) # Forced MISS
    test2(3, 6) # HIT
    test2(3, 6) # HIT

    test3_1(1,2) # VMISS
    test3_1(1,3) # VMISS
    test3_2(2,2) # VMISS
    test3_2(2,3) # VMISS

    invalidatev( group_vkey(2,2) )

    test3_1(1,2) #vhit
    test3_1(1,3) #vhit
    test3_2(2,2) #vmiss
    test3_2(2,3) #vmiss

    test3_1(1,2) # vhit
    test3_1(1,2, __force_cache_invalidate_in_place = True) # vhit
    test3_1(1,2) # vhit

    raising(1,2)

