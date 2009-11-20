import cookielib
from datetime import datetime
import re
import urllib
import urllib2

import BeautifulSoup as bs
import simplejson as json


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
        soup = bs.BeautifulSoup(resp.read())
        form = soup.find('form', {'id': self.loginform_id})
        data = {}
        data[self.loginform_user_field] = self._user
        data[self.loginform_pass_field] = passwd
        data[self.loginform_persist_field] = 'yes'
        for el in form.findAll('input', {'type': 'hidden'}):
            data[el['name']] = el['value']
        return self._post(form['action'], data)


class MobileMe(WebService):
    loginform_url = 'https://auth.me.com/authenticate'
    loginform_data = {
        'service': 'account',
        'ssoNamespace': 'primary-me',
        'reauthorize': 'Y',
        'returnURL': 'aHR0cHM6Ly9zZWN1cmUubWUuY29tL2FjY291bnQv'
    }
    loginform_id = 'LoginForm'
    loginform_user_field = 'username'
    loginform_pass_field = 'password'
    loginform_persist_field = 'keepLoggedIn'

    def __init__(self, user, passwd):
        super(MobileMe, self).__init__(user, passwd)
        self.devices = set()
        self._devices = {}
        self._get_devices()

    def _js_post(self, url, data={}, headers={}):
        headers.update({
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'X-Requested-With': 'XMLHTTPRequest',
            'X-Prototype-Version': '1.6.0.3',
            'X-Mobileme-Version': '1.0',
            'X-Mobileme-Isc': self._cookiejar._cookies['.secure.me.com']['/']['isc-secure.me.com'].value,
        })
        return self._post(url, data, headers)

    def _auth(self, passwd):
        super(MobileMe, self)._auth(passwd)
        data = {
            'anchor': 'findmyiphone',
            'lang': 'en',
        }
        self._get('https://secure.me.com/wo/WebObjects/Account2.woa', data, headers={'X-Mobileme-Version': '1.0'})

    def _get_devices(self):
        data = {'lang': 'en'}
        url = 'https://secure.me.com/wo/WebObjects/DeviceMgmt.woa?%s' % urllib.urlencode(data)
        html = self._js_post(url).read()
        for match in re.findall("new Device\(([^)]+)\)", html):
            _, id, type, cls, osver, _, _ = match.replace("'", '').split(', ')
            self._add_device(id, type, cls, osver)

    def _add_device(self, id, type, cls, osver):
        self._devices[id] = {
            'id': id,
            'type': type,
            'class': cls,
            'osver': osver,
        }

    def get_devices(self):
        return self._devices.keys()

    def get_device(self, id=None):
        if id is None:
            if len(self._devices) == 1:
                id = self._devices.keys()[0]
            else:
                return None # should do something more drastic here!
        return self._devices[id]

    def locate_device(self, device_id=None):
        device = self.get_device(device_id)
        if device is None:
            return None # blah.. drastic
        body = {
            'deviceId': device['id'],
            'deviceOsVersion': device['osver'],
        }
        data = {'postBody': json.dumps(body)}
        resp_data = json.loads(self._js_post('https://secure.me.com/wo/WebObjects/DeviceMgmt.woa/wa/LocateAction/locateStatus', data).read())
        dt = datetime.strptime('%s %s' % (resp_data['date'], resp_data['time']), '%B %d, %Y %I:%M %p')
        del(resp_data['date'], resp_data['time'])
        resp_data['date'] = dt
        return resp_data

class Google(WebService):
    loginform_url = 'https://www.google.com/accounts/ServiceLogin' # &continue=http://maps.google.com/maps/m%3Fmode%3Dlatitude
    loginform_data = {
        'service': 'friendview',
        'hl': 'en',
        'nui': '1',
        'continue': 'http://maps.google.com/maps/m?mode=latitude',
    }
    loginform_id = 'gaia_loginform'
    loginform_user_field = 'Email'
    loginform_pass_field = 'Passwd'
    loginform_persist_field = 'PersistentCookie'

    def update_latitude(self, date, lat, lng, accuracy):
        import time
        data = {
            't': 'ul',
            'mwmct': 'iphone',
            'mwmcv': '5.8',
            'mwmdt': 'iphone',
            'mwmdv': '30102',
            'auto': 'true',
            'nr': '180000',
            'cts': ('%s00' % time.mktime(date.timetuple())).replace('.', ''), # biggest. hack. ever.
            'lat': '%s' % lat,
            'lng': '%s' % lng,
            'accuracy': '%s' % accuracy,
        }
        return (self._post('http://maps.google.com/glm/mmap/mwmfr', data, {'X-ManualHeader': 'true'}).code == 200)

if __name__ == '__main__':
    import sys
    mm_user, mm_passwd = sys.argv[1:3]
    g_user, g_passwd = sys.argv[3:5]
    print "Logging into MobileMe..."
    m = MobileMe(mm_user, mm_passwd)
    print "Logging into Google..."
    g = Google(g_user, g_passwd)
    print "Locating iPhone..."
    l = m.locate_device()
    print "Updating Latitude..."
    g.update_latitude(l['date'], l['latitude'], l['longitude'], l['accuracy'])
    print "Done."
