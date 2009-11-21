from datetime import datetime
import logging
from xml.etree import ElementTree

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
        return (self._post('http://maps.google.com/glm/mmap/mwmfr', data, {'X-ManualHeader': 'true'}).code == 200)

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

class Location(object):
    """ Represents a Latitude "Check In". """
    def __init__(self, dt, latitude, longitude, accuracy, altitude):
        self.accuracy = accuracy
        self.altitude = altitude
        self.datetime = dt
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return '(%s, %s) ~%sm @ %s' % (
            self.latitude,
            self.longitude,
            self.accuracy,
            self.datetime.strftime('%d/%m/%Y %H:%M:%S')
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
        return cls(dt, latitude, longitude, accuracy, altitude)

    @classmethod
    def history_from_kml(cls, kml):
        if isinstance(kml, basestring):
            kml = kml.replace('http://www.opengis.net/kml/2.2', '') # it just makes parsing the tags easier - should probably use lxml
            kml = ElementTree.fromstring(kml)
        return sorted((Location.from_kml(placemark) for placemark in kml.findall('.//Placemark')), key=lambda l: l.datetime)
