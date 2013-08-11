# coding=utf-8

import simplemediawiki
import unittest


class MediaWikiTest(unittest.TestCase):
    def setUp(self):
        self.user_agent = simplemediawiki.build_user_agent(
            'python-simplemediawiki test suite', simplemediawiki.__version__,
            'https://github.com/ianweller/python-simplemediawiki')
        self.mw = simplemediawiki.MediaWiki(('https://simplemediawikitestsuite'
                                             '-ianweller.rhcloud.com/api.php'),
                                            user_agent=self.user_agent)

    def test_call(self):
        data = self.mw.call({'action': 'query',
                             'meta': 'siteinfo'})
        self.assertTrue('query' in data)
        self.assertTrue('general' in data['query'])

    def test_normalize_api_url_apidotphp(self):
        self.assertTrue(self.mw.normalize_api_url() is not None)

    def test_normalize_api_url_indexdotphp(self):
        mw = simplemediawiki.MediaWiki(('https://simplemediawikitestsuite'
                                        '-ianweller.rhcloud.com/index.php'),
                                       user_agent=self.user_agent)
        self.assertTrue(mw.normalize_api_url() is not None)
        self.assertTrue('api.php' in mw._api_url)

    def test_login(self):
        self.assertTrue(self.mw.login('password', 'username'))
