from datetime import datetime
import logging
import re
from xml.etree import ElementTree

from actions import Action
from mobileme import MobileMe, MobileMeAction
from webservice import WebService


class Google(WebService):
    loginform_url = 'https://www.google.com/accounts/ServiceLogin'
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

    def _js_post(self, url, data={}, headers={}):
        headers.update({'X-ManualHeader': 'true'})
        return super(Google, self)._post(url, data, headers)

    def update_latitude(self, timestamp, latitude, longitude, accuracy):
        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info('Updating latitude location (%s, %s) ~%sm @ %s', longitude, latitude, accuracy, datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S'))
        data = {
            't': 'ul',
            'mwmct': 'iphone',
            'mwmcv': '5.8',
            'mwmdt': 'iphone',
            'mwmdv': '30102',
            'auto': 'true',
            'nr': '180000',
            'cts': timestamp*1000, # epoch in miliseconds
            'lat': '%s' % latitude,
            'lng': '%s' % longitude,
            'accuracy': accuracy,
        }
        return (self._js_post('http://maps.google.com/glm/mmap/mwmfr', data).code == 200)

    def get_history(self, start, end):
        url = 'http://www.google.com/latitude/apps/history/kml'
        data = {
            'startDay': start.strftime('%m/%d/%Y'),
            'endDay': end.strftime('%m/%d/%Y'),
        }
        self._logger.info('Fetching latitude history from %s until %s', start.strftime('%d/%m/%Y'), end.strftime('%d/%m/%Y'))
        kml = self._get(url, data).read()
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug('Got KML:')
            for line in kml.split('\n'):
                self._logger.debug('\t%s', line)
        return Location.history_from_kml(kml)

    def locate_friends(self):
        data = {
            'gpsc': 'false',
            'mwmct': 'iphone',
            'mwmcv': '5.8',
            'mwmdt': 'iphone',
            'mwmdv': '30000',
            't': 'fs'
        }
        self._logger.info("Locating friends...")
        resp = self._js_post('http://maps.google.com/glm/mmap/mwmfr', data).read().replace('\n', '')
        friends = []
        rx = re.compile('\[,\[,"-?\d+",3,1,1,,0\],"(?P<email>[^"]+)","(?P<name>[^"]+)",(?P<phone>[^,]*),(?P<lat>-?\d+),(?P<lon>-?\d+),"(?P<timestamp>\d{10})\d{3}",(?P<accuracy>\d*),\["(?P<address>[^"]*)","(?P<city_state>[^"]*)"]')
        for friend in rx.findall(resp):
            self._logger.debug('Found friend "%s"' % friend[1])
            friends.append({
                'email': friend[0],
                'location': Location(**{
                    'dt': datetime.fromtimestamp(int(friend[5])/1000),
                    'latitude': friend[3],
                    'longitude': friend[4],
                    'accuracy': friend[6],
                    'reversegeo': ('%s, %s' % (friend[7], friend[8])).strip(', ')
                }),
                'name': friend[1],
                'phone': friend[2]
            })
        return friends

class Location(object):
    """ Represents a Latitude "Check In". """
    def __init__(self, dt, latitude, longitude, accuracy, altitude=0, reversegeo=None):
        self.accuracy = accuracy
        self.altitude = altitude
        self.datetime = dt
        self.latitude = latitude
        self.longitude = longitude
        self.reversegeo = reversegeo

    def __str__(self):
        return '(%s, %s) ~%sm @ %s' % (
            self.latitude,
            self.longitude,
            self.accuracy,
            self.datetime.strftime('%d/%m/%Y %H:%M:%S'),
        )

    @classmethod
    def from_kml(cls, kml):
        if isinstance(kml, basestring):
            kml = ElementTree.fromstring(kml)
        longitude, latitude, altitude = kml.find('.//Point/coordinates').text.split(',')
        for data in kml.findall('.//Data/'):
            if data.attrib['name'] == 'accuracy':
                accuracy = data.find('value').text
            if data.attrib['name'] == 'timestamp':
                dt = datetime.fromtimestamp(int(data.find('value').text)/1000)
        return cls(dt, latitude, longitude, accuracy, altitude, reversegeo=kml.find('.//description/').text)

    @classmethod
    def history_from_kml(cls, kml):
        if isinstance(kml, basestring):
            kml = kml.replace('http://www.opengis.net/kml/2.2', '') # it just makes parsing the tags easier - should probably use lxml
            kml = ElementTree.fromstring(kml)
        return sorted((Location.from_kml(placemark) for placemark in kml.findall('.//Placemark')), key=lambda l: l.datetime)

class GoogleAction(Action):
    required_args = (
        ('g_user', 'Google Username', False),
        ('g_pass', 'Google Password', True),
    )
    def __init__(self, *args, **kwargs):
        super(GoogleAction, self).__init__(*args, **kwargs)
        self.parser.add_argument('-g', '--google-user', dest='g_user', help='Google username, will be prompted for if not provided', metavar='GOOGLEUSER')
        self.parser.add_argument('-G', '--google-pass', dest='g_pass', help='Google password, will be prompted for if not provided', metavar='GOOGLEPASS')

class GetHistoryAction(GoogleAction):
    keyword = 'get_history'
    required_arguments = (
        ('start', 'Start Date', False),
        ('end', 'End Date', False),
    )
    def setup(self):
        date = lambda date_str: datetime.strptime(date_str, '%d/%m/%Y')
        self.parser.add_argument('start', type=date, help='Start date range (format: dd/mm/yyyy)', metavar='start_date')
        self.parser.add_argument('end', type=date, help='End date range (format: dd/mm/yyyy)', metavar='end_date')

    def main(self):
        g = Google(self.args.g_user, self.args.g_pass)
        for loc in g.get_history(self.args.start, self.args.end):
            print loc

class LocateFriends(GoogleAction):
    keyword = 'locate_friends'
    def main(self):
        g = Google(self.args.g_user, self.args.g_pass)
        for friend in g.locate_friends():
            print '%s - %s\t\n%s' % (friend['name'], friend['location'].reversegeo, friend['location'])

class UpdateAction(GoogleAction, MobileMeAction):
    keyword = 'update'
    def main(self):
        g = Google(self.args.g_user, self.args.g_pass)
        m = MobileMe(self.args.m_user, self.args.m_pass)
        l = m.locate_device()
        g.update_latitude(timestamp=l.timestamp, latitude=l.latitude, longitude=l.longitude, accuracy=l.accuracy)
