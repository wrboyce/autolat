import cookielib
import logging
import urllib
import urllib2
import re

import BeautifulSoup as beautifulsoup


class CookieJar(cookielib.CookieJar):
    """ Workaround for http://bugs.python.org/issue3924. """

    def _cookie_from_cookie_tuple(self, tup, request):
        name, value, standard, rest = tup
        version = standard.get('version', None)
        if version:
            version = int(version.strip('"'))
        standard['version'] = version
        tup = (name, value, standard, rest)
        return cookielib.CookieJar._cookie_from_cookie_tuple(self, tup, request)


class WebService(object):
    loginform_url = ''
    loginform_data = {}
    loginform_id = ''
    loginform_user_field = ''
    loginform_pass_field = ''
    loginform_persist_field = ''

    def __init__(self, user, passwd):
        self._setup_logger()
        self._cookiejar = CookieJar()
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cookiejar))
        self._user = user
        resp = self._auth(passwd)
        html = resp.read()
        self.xmanualheader = re.search("XsrfToken.*'(.*)'", html).group(1)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self._user)

    def _setup_logger(self):
        self._logger = logging.getLogger('autolat.%s' % self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)-7s%(name)s.%(funcName)s %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _get(self, url, data={}, headers={}):
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug('%s' % url)
            for k, v in headers.iteritems():
                self._logger.debug('h> %s: %s' % (k, v))
            for k, v in data.iteritems():
                self._logger.debug('d> %s=%s' % (k, v))
        if data:
            url = '%s?%s' % (url, urllib.urlencode(data))
        req = urllib2.Request(url, headers=headers)
        return self._opener.open(req)

    def _post(self, url, data={}, headers={}):
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug('%s' % url)
            for k, v in headers.iteritems():
                self._logger.debug('h> %s: %s' % (k, v))
            for k, v in data.iteritems():
                self._logger.debug('d> %s=%s' % (k, v))
        if isinstance(data, dict):
            data = urllib.urlencode(self.encoded_dict(data))
        req = urllib2.Request(url, data, headers)
        return self._opener.open(req)

    def _auth(self, passwd):
        self._logger.info('Authenticating...')
        resp = self._get(self.loginform_url, self.loginform_data)
        soup = beautifulsoup.BeautifulSoup(resp.read())
        form = soup.find('form', {'id': self.loginform_id})
        data = {}
        data[self.loginform_user_field] = self._user
        data[self.loginform_pass_field] = passwd
        data[self.loginform_persist_field] = 'yes'
        for el in form.findAll('input', {'type': 'hidden'}):
            data[el['name']] = el['value']
        return self._post(form['action'], data)

    def encoded_dict(self, in_dict):
        out_dict = {}
        for k, v in in_dict.iteritems():
            if isinstance(v, unicode):
                v = v.encode('utf8')
            elif isinstance(v, str):
                # Must be encoded in UTF-8
                v.decode('utf8')
            out_dict[k] = v
        return out_dict
