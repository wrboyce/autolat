import cookielib
import urllib
import urllib2

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
        self._cookiejar = CookieJar()
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cookiejar))
        self._user = user
        self._auth(passwd)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self._user)

    def _get(self, url, data={}, headers={}):
        if data:
            url = '%s?%s' % (url, urllib.urlencode(data))
        req = urllib2.Request(url, headers=headers)
        return self._opener.open(req)

    def _post(self, url, data={}, headers={}):
        data = urllib.urlencode(data)
        req = urllib2.Request(url, data, headers)
        return self._opener.open(req)

    def _auth(self, passwd):
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
