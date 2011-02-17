# python-simplemediawiki - Extremely low-level wrapper to the MediaWiki API
# Copyright (C) 2011 Red Hat, Inc.
# Primary maintainer: Ian Weller <iweller@redhat.com>
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
:py:mod:`simplemediawiki` is an extremely low-level wrapper to the `MediaWiki
API`_. It automatically handles cookies and gzip compression so that you can
make basic calls to the API in the easiest and fastest way possible. It also
provides a few functions to make day-to-day API access easier.

To use this module, initialize a :py:class:`MediaWiki` object, passing it the
URL of api.php for the wiki you want to work with. Calls go through
:py:func:`MediaWiki.call`. A generic login wrapper as well as functions to
determine limits and get a list of namespaces are provided for your
convenience.

>>> from simplemediawiki import MediaWiki
>>> wiki = MediaWiki('http://en.wikipedia.org/w/api.php')
>>> wiki.call({'action': 'query', 'prop': 'revisions', 'titles': 'Main Page'})
{u'query': {u'pages': {...}}}

.. _`MediaWiki API`: http://www.mediawiki.org/wiki/API:Main_page
"""

import cookielib
import gzip
try:
    import simplejson as json
except ImportError:
    import json
from kitchen.text.converters import to_bytes
from StringIO import StringIO
import urllib
import urllib2

__author__ = 'Ian Weller <iweller@redhat.com>'
__version__ = '1.1'
DEFAULT_UA = ('python-simplemediawiki/%s '
              '+https://github.com/ianweller/python-simplemediawiki') \
        % __version__


class MediaWiki(object):
    """
    Create a new object to access a wiki via *api_url*.

    If you're interested in saving session data across multiple
    :py:class:`MediaWiki` objects, provide a filename *cookie_file* to where
    you want to save the cookies.

    Applications that use simplemediawiki should change the *user_agent*
    argument to something that can help identify the application if it is
    misbehaving. It's recommended to use :py:func:`build_user_agent` to create
    a `User-Agent`_ string that will be most helpful to server administrators.
    Wikimedia sites enforce using a correct User-Agent; you should read
    `Wikimedia's User-Agent policy`_ if you plan to be accessing those wikis.

    .. tip::
       If a user of your application may not know how to get the correct API
       URL for their MediaWiki, you can try getting the right one with
       :py:func:`MediaWiki.normalize_api_url`.

    :param api_url: URL for the path to the API endpoint
    :param cookie_file: path to a :py:class:`cookielib.MozillaCookieJar` file
    :param user_agent: string sent as ``User-Agent`` header to web server

    .. _`User-Agent`: http://en.wikipedia.org/wiki/User_agent
    .. _`Wikimedia's User-Agent policy`:
        http://meta.wikimedia.org/wiki/User-Agent_policy
    """
    _high_limits = None
    _namespaces = None
    _psuedo_namespaces = None

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
        self._opener.addheaders = [('User-Agent', user_agent)]

    def _fetch_http(self, url, params):
        """
        Standard HTTP request handler for this class with gzip and cookie
        support. This was separated out of :py:func:`MediaWiki.call` to make
        :py:func:`MediaWiki.normalize_api_url` useful.

        .. note::
           This function should not be used. Use :py:func:`MediaWiki.call`
           instead.

        :param url: URL to send POST request to
        :param params: dictionary of query string parameters
        """
        params['format'] = 'json'
        # urllib.urlencode expects str objects, not unicode
        fixed = dict([(to_bytes(b[0]), to_bytes(b[1]))
                      for b in params.items()])
        request = urllib2.Request(url, urllib.urlencode(fixed))
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
        Make an API call to the wiki. *params* is a dictionary of query string
        arguments. For example, to get basic information about the wiki, run:

        >>> wiki.call({'action': 'query', 'meta': 'siteinfo'})

        which would make a call to
        ``http://domain/w/api.php?action=query&meta=siteinfo&format=json``
        (except the query string would be sent in POST).

        :param params: dictionary of query string parameters
        :returns: dictionary containing API response
        """
        return json.loads(self._fetch_http(self._api_url, params))

    def normalize_api_url(self):
        """
        Checks that the API URL used to initialize this object actually returns
        JSON. If it doesn't, make some educated guesses and try to find the
        correct URL.

        :returns: a valid API URL or ``None``
        """
        def tester(self, api_url):
            """
            Attempts to fetch general information about the MediaWiki instance
            in order to test whether *api_url* will return JSON.
            """
            data = self._fetch_http(api_url, {'action': 'query',
                                              'meta': 'siteinfo'})
            try:
                data_json = json.loads(data)
                return (data, data_json)
            except ValueError:
                return (data, None)

        data, data_json = tester(self, self._api_url)
        if data_json:
            return self._api_url
        else:
            # if there's an index.php in the URL, we might find the API
            if 'index.php' in self._api_url:
                test_api_url = self._api_url.split('index.php')[0] + 'api.php'
                print test_api_url
                test_data, test_data_json = tester(self, test_api_url)
                print (test_data, test_data_json)
                if test_data_json:
                    self._api_url = test_api_url
                    return self._api_url
            return None

    def login(self, user, passwd):
        """
        Logs into the wiki with username *user* and password *passwd*. Returns
        ``True`` on successful login.

        :param user: username
        :param passwd: password
        :returns: ``True`` on successful login, otherwise ``False``
        """
        def do_login(self, user, passwd, token=None):
            """
            Login function that handles CSRF protection (see `MediaWiki bug
            23076`_). Returns ``True`` on successful login.

            .. _`MediaWiki bug 23076`:
                https://bugzilla.wikimedia.org/show_bug.cgi?id=23076
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
                return do_login(self, user, passwd, result['login']['token'])
            else:
                return False

        return do_login(self, user, passwd)

    def logout(self):
        """
        Logs out of the wiki.

        :returns: ``True``
        """
        data = {'action': 'logout'}
        self.call(data)
        self._high_limits = None
        return True

    def limits(self, low, high):
        """
        Convenience function for determining appropriate limits in the API. If
        the (usually logged-in) client has the ``apihighlimits`` right, it will
        return *high*; otherwise it will return *low*.

        It's generally a good idea to use the highest limit possible; this
        reduces the amount of HTTP requests and therefore overhead. Read the
        API documentation for details on the limits for the function you are
        using.

        :param low: value to return if client does not have ``apihighlimits``
        :param high: value to return if client has ``apihighlimits``
        :returns: *low* or *high*
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
        Fetches a list of namespaces for this wiki and returns them as a
        dictionary of namespace IDs corresponding to namespace names. If
        *psuedo* is ``True``, the dictionary will also list psuedo-namespaces,
        which are the "Special:" and "Media:" namespaces (special because they
        have no content associated with them and their IDs are negative).

        :param psuedo: boolean to determine inclusion of psuedo-namespaces
        :returns: dictionary of namespace IDs and names
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
        Converts `ISO 8601`_ dates generated by the MediaWiki API into
        :py:class:`datetime.datetime` objects.

        This will return a time in what your wiki thinks is UTC. Plan
        accordingly for bad server configurations.

        .. _`ISO 8601`: http://en.wikipedia.org/wiki/ISO_8601

        :param date: string ISO 8601 date representation
        :returns: :py:class:`datetime.datetime` object
        """
        # MediaWiki API dates are always of the format
        #   YYYY-MM-DDTHH:MM:SSZ
        # (see $formats in wfTimestamp() in includes/GlobalFunctions.php)
        return datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')


def build_user_agent(application_name, version, url):
    """
    Build a good User-Agent header string that can help server administrators
    contact you if your application is misbehaving. This string will also
    contain a reference to python-simplemediawiki.

    See the documentation for :py:class:`simplemediawiki.MediaWiki` for good
    reasons why you should use a custom User-Agent string for your application.

    :param application_name: your application's name
    :param version: your application's version
    :param url: a URL where smoeone can find information about your \
            application or your email address
    :returns: User-Agent string
    """
    return '%s/%s %s/%s (+%s)' % (application_name, version,
                                  'python-simplemediawiki', __version__, url)
