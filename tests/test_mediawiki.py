# coding=utf-8

from datetime import datetime
import simplemediawiki
import unittest


class MediaWikiTest(unittest.TestCase):
    def setUp(self):
        self.user_agent = simplemediawiki.build_user_agent(
            'python-simplemediawiki test suite', simplemediawiki.__version__,
            'https://github.com/ilianaw/python-simplemediawiki')
        self.mw = simplemediawiki.MediaWiki('FIXME/api.php',
                                            user_agent=self.user_agent)

    def test_call(self):
        data = self.mw.call({'action': 'query',
                             'meta': 'siteinfo'})
        self.assertTrue('query' in data)
        self.assertTrue('general' in data['query'])

    def test_normalize_api_url_apidotphp(self):
        self.assertTrue(self.mw.normalize_api_url() is not None)

    def test_normalize_api_url_indexdotphp(self):
        mw = simplemediawiki.MediaWiki('FIXME/index.php',
                                       user_agent=self.user_agent)
        self.assertTrue(mw.normalize_api_url() is not None)
        self.assertTrue('api.php' in mw._api_url)

    def test_login_logout(self):
        self.assertTrue(self.mw.login('password', 'username'))
        data = self.mw.call({'action': 'query',
                             'meta': 'userinfo'})
        self.assertTrue('anon' not in data['query']['userinfo'])
        self.assertTrue(self.mw.logout())
        data = self.mw.call({'action': 'query',
                             'meta': 'userinfo'})
        self.assertTrue('anon' in data['query']['userinfo'])

    def test_limits_low(self):
        self.mw.login('password', 'username')
        self.assertEquals(self.mw.limits('low', 'high'), 'low')

    def test_limits_high(self):
        self.mw.login('passwordhigh', 'username')
        self.assertEquals(self.mw.limits('low', 'high'), 'high')

    def test_namespaces(self):
        namespaces = self.mw.namespaces()
        self.assertEquals(namespaces[-1], 'Special')
        self.assertEquals(namespaces[0], '')
        self.assertEquals(namespaces[1], 'Talk')

    def test_namespaces_nonpsuedo(self):
        namespaces = self.mw.namespaces(psuedo=False)
        self.assertTrue(-1 not in namespaces)

    def test_namespaces_psuedo(self):
        namespaces = self.mw.namespaces(psuedo=True)
        self.assertTrue(-1 in namespaces)

    def test_parse_date(self):
        self.assertEquals(self.mw.parse_date('2013-08-11T19:04:12Z'),
                          datetime(2013, 8, 11, 19, 4, 12, 0))

    def test_build_user_agent(self):
        user_agent = simplemediawiki.build_user_agent(
            'python-simplemediawiki test suite', simplemediawiki.__version__,
            'https://github.com/ilianaw/python-simplemediawiki')
        self.assertTrue('python-simplemediawiki' in user_agent)
        self.assertTrue(simplemediawiki.__version__ in user_agent)
        self.assertTrue('github.com/ilianaw/python-simplemediawiki' in
                        user_agent)
