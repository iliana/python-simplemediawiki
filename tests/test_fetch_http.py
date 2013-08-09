# coding=utf-8

import simplemediawiki
import unittest
try:
    import simplejson as json
except ImportError:
    import json

try:
    import http.cookiejar as cookielib
except ImportError:
    import cookielib

UNICODE_TEST = u'κόσμε'


class FetchHttpTest(unittest.TestCase):
    def setUp(self):
        self.user_agent = simplemediawiki.build_user_agent(
            'python-simplemediawiki test suite', simplemediawiki.__version__,
            'https://github.com/ianweller/python-simplemediawiki')
        self.mw = simplemediawiki.MediaWiki('https://httpbin.org/',
                                            user_agent=self.user_agent)
        self.data = None

    def _do_post(self):
        self.data = json.loads(self.mw._fetch_http('https://httpbin.org/post',
                                                   {'butts': 'lol',
                                                    'unicode': UNICODE_TEST}))

    def test_get(self):
        data = json.loads(self.mw._fetch_http('https://httpbin.org/get',
                                              {'butts': 'lol',
                                               'unicode': UNICODE_TEST},
                                              force_get=True))
        assert data['args']['format'] == 'json'
        assert data['args']['unicode'] == UNICODE_TEST

    def test_post(self):
        self._do_post()
        assert self.data is not None
        assert self.data['form']['format'] == 'json'
        assert self.data['form']['unicode'] == UNICODE_TEST

    def test_user_agent(self):
        self._do_post()
        assert self.data['headers']['User-Agent'] == self.user_agent

    def test_gzip(self):
        data = json.loads(self.mw._fetch_http('https://httpbin.org/gzip', {},
                                              force_get=True))
        assert data['gzipped'] == True

    def test_cookies(self):
        self.mw._fetch_http('https://httpbin.org/cookies/set',
                            {'unicode': UNICODE_TEST},
                            force_get=True)
        data = json.loads(self.mw._fetch_http('https://httpbin.org/cookies', {},
                                              force_get=True))
        assert 'unicode' in data['cookies']
        assert data['cookies']['unicode'] == UNICODE_TEST

    def test_persistent_cookiejar(self):
        cookiejar = cookielib.CookieJar()
        mw1 = simplemediawiki.MediaWiki('https://httpbin.org/',
                                        cookiejar=cookiejar,
                                        user_agent=self.user_agent)
        mw1._fetch_http('https://httpbin.org/cookies/set',
                        {'unicode': UNICODE_TEST}, force_get=True)
        cookiejar = mw1._cj
        mw2 = simplemediawiki.MediaWiki('https://httpbin.org/',
                                        cookiejar=cookiejar,
                                        user_agent=self.user_agent)
        data = json.loads(mw2._fetch_http('https://httpbin.org/cookies', {},
                                          force_get=True))
        print(data)
        assert 'unicode' in data['cookies']
        assert data['cookies']['unicode'] == UNICODE_TEST
