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
            'accuracy': accuracy,
        }
        return (self._post('http://maps.google.com/glm/mmap/mwmfr', data, {'X-ManualHeader': 'true'}).code == 200)
