# python-simplemediawiki - Extremely low-level wrapper to the MediaWiki API
# Copyright (C) 2010 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""
simplemediawiki is an extremely low-level wrapper to the MediaWiki API. It
automatically handles cookies and gzip compression so that you can make basic
calls to the API in the easiest way possible. It also provides a few functions
to make day-to-day API access easier.

To use this module, instantiate a MediaWiki object, passing it the URL of
api.php for the wiki you want to work with. Calls go through MediaWiki.call().
A generic login wrapper as well as functions to determine limits and get a list
of namespaces are provided for your convenience.

>>> from simplemediawiki import MediaWiki
>>> wiki = MediaWiki('http://en.wikipedia.org/w/api.php')
>>> wiki.call({'action': 'query', 'prop': 'revisions', 'titles': 'Main Page'})
{u'query': {u'pages': {...}}}
"""

import cookielib
import gzip
from iso8601 import iso8601
import json
from StringIO import StringIO
import urllib
import urllib2


class MediaWiki():
    """
    Class to represent a MediaWiki installation with an enabled API.

    api_url: URL to api.php (usually similar to http://example.com/w/api.php)
    """
    _high_limits = None
    _namespaces = None
    _psuedo_namespaces = None
    _mediawiki_version = None

    def __init__(self, api_url, cookie_file=None, user_agent=DEFAULT_UA):
        self._api_url = api_url
        if cookie_file:
            self._cj = cookielib.MozillaCookieJar(cookie_file)
            try:
                self._cj.load()
            except IOError:
                self._cj.save()
                self._cj.load()
        else:
            self._cj = cookielib.CookieJar()
        self._opener = urllib2.build_opener(
                urllib2.HTTPCookieProcessor(self._cj)
        )
        self._opener.addheaders = [('User-agent', user_agent)]

    def _fetch_http(self, url, params):
        request = urllib2.Request(url, urllib.urlencode(params))
        request.add_header('Accept-encoding', 'gzip')
        response = self._opener.open(request)
        if isinstance(self._cj, cookielib.MozillaCookieJar):
            self._cj.save()
        if response.headers.get('Content-Encoding') == 'gzip':
            compressed = StringIO(response.read())
            gzipper = gzip.GzipFile(fileobj=compressed)
            data = gzipper.read()
        else:
            data = response.read()
        return data

    def call(self, params):
        """
        Make a call to the wiki. Returns a dictionary that represents the JSON
        returned by the API.
        """
        params['format'] = 'json'
        return json.loads(self._fetch_http(self._api_url, params))

    def normalize_api_url(self):
        """
        This function checks the given URL for a correct API endpoint and
        returns that URL, while also helpfully setting this object's API URL to
        it. If it can't magically conjure an API endpoint, it returns False.
        """
        data, data_json = self._normalize_api_url_tester(self._api_url)
        if data_json:
            return self._api_url
        else:
            # if there's an index.php in the URL, we might find the API
            if 'index.php' in self._api_url:
                test_api_url = self._api_url.split('index.php')[0] + 'api.php'
                print test_api_url
                test_data, test_data_json = \
                        self._normalize_api_url_tester(test_api_url)
                print (test_data, test_data_json)
                if test_data_json:
                    self._api_url = test_api_url
                    return self._api_url
            return False

    def _normalize_api_url_tester(self, api_url):
        data = self._fetch_http(api_url, {'action': 'query',
                                          'meta': 'siteinfo',
                                          'siprop': 'general',
                                          'format': 'json'})
        try:
            data_json = json.loads(data)
            # may as well set the version
            try:
                version_string = data_json['query']['general']['generator']
                self._mediawiki_version = version_string.split(' ', 1)[1]
            except KeyError:
                pass
            return (data, data_json)
        except ValueError:
            return (data, None)

    def login(self, user, passwd, token=None):
        """
        Convenience function for logging into the wiki. It should never be
        necessary to provide a token argument; it is part of the login process
        since MediaWiki 1.15.3 (see MediaWiki bug 23076).
        """
        data = {'action': 'login',
                'lgname': user,
                'lgpassword': passwd}
        if token:
            data['lgtoken'] = token
        result = self.call(data)
        if result['login']['result'] == 'Success':
            self._high_limits = None
            return True
        elif result['login']['result'] == 'NeedToken' and not token:
            return self.login(user, passwd, result['login']['token'])
        else:
            return False

    def logout(self):
        """
        Conveinence function for logging out of the wiki.
        """
        data = {'action': 'logout'}
        self.call(data)
        self._high_limits = None
        return True

    def limits(self, low, high):
        """
        Convenience function for determining appropriate limits in the API. If
        the logged in user has the "apihighlimits" right, it will return the
        high argument; otherwise it will return the low argument.
        """
        if self._high_limits == None:
            result = self.call({'action': 'query',
                                'meta': 'userinfo',
                                'uiprop': 'rights'})
            self._high_limits = 'apihighlimits' in \
                    result['query']['userinfo']['rights']
        if self._high_limits:
            return high
        else:
            return low

    def namespaces(self, psuedo=True):
        """
        Fetches a list of namespaces for this wiki.
        """
        if self._namespaces == None:
            result = self.call({'action': 'query',
                                'meta': 'siteinfo',
                                'siprop': 'namespaces'})
            self._namespaces = {}
            self._psuedo_namespaces = {}
            for nsid in result['query']['namespaces']:
                if int(nsid) >= 0:
                    self._namespaces[int(nsid)] = \
                            result['query']['namespaces'][nsid]['*']
                else:
                    self._psuedo_namespaces[int(nsid)] = \
                            result['query']['namespaces'][nsid]['*']
        if psuedo:
            retval = {}
            retval.update(self._namespaces)
            retval.update(self._psuedo_namespaces)
            return retval
        else:
            return self._namespaces

    @staticmethod
    def parse_date(date):
        """
        Converts dates provided by the MediaWiki API into datetime.datetime
        objects.
        """
        return iso8601.parse_date(date)


__author__ = 'Ian Weller <ian@ianweller.org>'
__version__ = '1.0.2'
DEFAULT_UA = 'python-simplemediawiki/%s ' + \
        '+https://github.com/ianweller/python-simplemediawiki' \
        % __version__
