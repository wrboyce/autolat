from datetime import datetime
import re
import time
import urllib

import simplejson as json

from actions import Action
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

    class MultipleDevicesFound(Exception):
        pass

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
            self._logger.info('Found device "%s"', id)
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
                self._logger.error('Multiple devices found and no ID specified, bailing.')
                raise MobileMe.MultipleDevicesFound('Device ID must be specified.')
        return self._devices[id]

    def locate_device(self, device_id=None):
        device = self.get_device(device_id)
        self._logger.info('Locating device "%(id)s"', device)
        body = {
            'deviceId': device['id'],
            'deviceOsVersion': device['osver'],
        }
        data = {'postBody': json.dumps(body)}
        resp = self._js_post('https://secure.me.com/wo/WebObjects/DeviceMgmt.woa/wa/LocateAction/locateStatus', data)
        if resp.code == 200:
            return Location(resp.read())
        self._logger.error('Locate device "%s" failed!', device['id'])

    def msg_device(self, msg, alarm=False, device_id=None):
        device = self.get_device(device_id)
        self._logger.info('Sending "%s" to device "%s" with%s alarm', msg, device['id'], 'out' if not alarm else '')
        body = {
            'deviceClass': device['class'],
            'deviceId': device['id'],
            'deviceOsVersion': device['osver'],
            'deviceType': device['type'],
            'message': msg,
            'playAlarm': 'Y' if alarm else 'N',
        }
        data = {'postBody': json.dumps(body)}
        resp = self._js_post('https://secure.me.com/wo/WebObjects/DeviceMgmt.woa/wa/SendMessageAction/sendMessage', data)
        resp_data = json.loads(resp.read())
        if resp_data['status'] == 1:
            return True
        self._logger.error('Sending message to device "%s" failed!', device['id'])
        self._logger.debug('%s', resp_data)

    def lock_device(self, pin, device_id=None):
        pin = str(pin)
        if len(pin) != 4 or not pin.isdigit():
            self._logger.error('PIN must be 4 digits')
        device = self.get_device(device_id)
        self._logger.info('Locking device "%s"', device['id'])
        body = {
            'deviceClass': device['class'],
            'deviceId': device['id'],
            'deviceOsVersion': device['osver'],
            'devicePasscode': pin,
            'devicePinConstraint': 'Y',
            'deviceType': device['type'],
        }
        data = {'postBody': json.dumps(body)}
        resp = self._js_post('https://secure.me.com/wo/WebObjects/DeviceMgmt.woa/wa/SendRemoteLockAction/sendRemoteLock', data)
        resp_data = json.loads(resp.read())
        if resp_data['status'] == 1:
            return True
        self._logger.error('Locking device "%s" failed!', device['id'])
        self._logger.debug('%s', resp_data)

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

    def __str__(self):
        return '(%s, %s) ~%sm @ %s' % (self.latitude, self.longitude, self.accuracy, self.datetime.strftime('%d/%m/%y %H:%M:%S'))

    def _uncamel(self, str):
        return ''.join('_%s' % c.lower() if c.isupper() else c for c in str)

class MobileMeAction(Action):
    required_args = (
        ('m_user', 'MobileMe Username', False),
        ('m_pass', 'MobileMe Password', True),
    )
    def __init__(self, *args, **kwargs):
        super(MobileMeAction, self).__init__(*args, **kwargs)
        self.parser.add_argument('-m', '--mobileme-user', dest='m_user', help='MobileMe username, will be prompted for if not provided', metavar='MOBILEMEUSER')
        self.parser.add_argument('-M', '--mobileme-pass', dest='m_pass', help='MobileMe password, will be prompted for if not provided', metavar='MOBILEMEPASS')

    def _with_device(self, inst, func, kwargs):
        try:
            return func(**kwargs)
        except MobileMe.MultipleDevicesFound:
            print "Error: Multiple devices found in account:"
            for id in inst.devices():
                print "\t%s" % id
            print
            kwargs['device_id'] = raw_input("Select a device: ")
            return func(**kwargs)

class MsgDeviceAction(MobileMeAction):
    keyword = 'msg_device'
    def setup(self):
        self.parser.add_argument('-D', '--device', dest='device', help='Device ID', metavar='DEVICE')
        self.parser.add_argument('-a', '--alarm', dest='alarm', action='store_true', help='Play a sound for 2 minutes with this message')
        self.parser.add_argument('message', nargs='+', help='Message to be sent to device')

    def main(self):
        m = MobileMe(self.args.m_user, self.args.m_pass)
        kwargs = {
            'msg': ' '.join(self.args.message),
            'alarm': self.args.alarm,
            'device_id': self.args.device,
        }
        return self._with_device(m, m.msg_device, kwargs)

class LocateDeviceAction(MobileMeAction):
    keyword = 'locate_device'
    def setup(self):
        self.parser.add_argument('-D', '--device', dest='device', help='Device ID', metavar='DEVICE')

    def main(self):
        m = MobileMe(self.args.m_user, self.args.m_pass)
        kwargs = {'device_id': self.args.device}
        print self._with_device(m, m.locate_device, kwargs)

class LockDeviceAction(MobileMeAction):
    keyword = 'lock_device'
    def setup(self):
        self.parser.add_argument('-D', '--device', dest='device', help='Device ID', metavar='DEVICE')
        self.parser.add_argument('pin', type=int, help='PIN to lock the device with', metavar='PIN')

    def main(self):
        m = MobileMe(self.args.m_user, self.args.m_pass)
        kwargs = {
            'pin': self.args.pin,
            'device_id': self.args.device,
        }
        return self._with_device(m, m.lock_device, kwargs)
