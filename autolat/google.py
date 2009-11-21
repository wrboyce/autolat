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

    def update_latitude(self, location):
        data = {
            't': 'ul',
            'mwmct': 'iphone',
            'mwmcv': '5.8',
            'mwmdt': 'iphone',
            'mwmdv': '30102',
            'auto': 'true',
            'nr': '180000',
            'cts': location.timestamp*1000,
            'lat': '%s' % location.latitude,
            'lng': '%s' % location.longitude,
            'accuracy': location.accuracy,
        }
        return (self._post('http://maps.google.com/glm/mmap/mwmfr', data, {'X-ManualHeader': 'true'}).code == 200)
