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

    def test_login(self):
        self.assertTrue(self.mw.login('password', 'username'))
