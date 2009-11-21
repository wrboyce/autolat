from datetime import datetime
import re
import time
import urllib

import simplejson as json

from webservice import WebService


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

    def __init__(self, *args, **kwargs):
        super(MobileMe, self).__init__(*args, **kwargs)
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
        resp = self._js_post('https://secure.me.com/wo/WebObjects/DeviceMgmt.woa/wa/LocateAction/locateStatus', data)
        if resp.code == 200:
            return Location(resp.read())
        return None # bzzt, something broke.

class Location(object):
    """ Holds location data returned from `MobileMe.WebService`

        Attributes:
            * accuracy (meters)
            * datetime
            * is_accurate
            * is_locate_finished
            * is_location_available
            * is_old_location_result
            * is_recent
            * latitude
            * longitude
            * status
            * status_string
            * timestamp
    """
    def __init__(self, json_data):
        data = json.loads(json_data)
        for k,v in data.iteritems():
            if k not in ('date', 'time'):
                setattr(self, self._uncamel(k), v)
            self.datetime = datetime.strptime('%s %s' % (data['date'], data['time']), '%B %d, %Y %I:%M %p')
            self.timestamp = int(time.mktime(self.datetime.timetuple()))

    def _uncamel(self, str):
        return ''.join('_%s' % c.lower() if c.isupper() else c for c in str)
