autolat
=======

# Installation

Autolat can be installed easily via pip:

    $ pip install -e git+git://github.com/wrboyce/autolat.git#egg=autolat

## Dependencies

* argparse
* BeautifulSoup
* simplejson


# Usage

The easiest way to use autolat is to use the `autolat` command from your shell. If required options are not provided, they are prompted for:

    $ autolat [command] [options]

To automatically update your latitude location (without any prompts):

    $ autolat update -g googleuser -G googlepass -m mobilemeuser -M mobilemepass

To get your latitude location history between two specified dates (the password is prompted for in this example):

    $ autolat get_history dd/mm/yyyy dd/mm/yyyy -g googleuser

You can also send a message to your device:

    $ autolat msg_device Hello World

Locate your device:

    $ autolat locate_device

And lock your device with a PIN:

    $ autolat lock_device 1234

See `autolat -h`, or `autolat [action] -h`, for more information.


# API

The API is currently quite simplistic.

To update your current location:

    >>> from autolat import Google, MobileMe
    >>> g = Google(user, passwd)
    >>> m = MobileMe(user, passwd)
    >>> l = m.locate_device()
    >>> g.update_latitude(timestamp=l.timestamp, latitude=l.latitude, longitude=l.longitude, accuracy=l.accuracy)

To get your latitude history:

    >>> from autolat import Google
    >>> g = Google(user, passwd)
    >>> h = g.get_history(start=datetime, end=datetime)

To send a message to your device:

    >>> from autolat import MobileMe
    >>> m = MobileMe(user, passwd)
    >>> m.msg_device('Hello World')
    >>> m.msg_device('Hello World!', alarm=True)

To lock your device with a PIN:

    >>> from autolat import MobileMe
    >>> m = MobileMe(user, passwd)
    >>> m.lock_device(pin=1234)

# Stuff you probably won't need

## Google

### Location

`Google.get_history` will return a list of `google.Location` objects, which represent a KML <Placemark> tag and have the following attributes:

* `accuracy`
* `altitude`
* `datetime`
* `latitude`
* `longitude`

They can be initialised from a KML placemark easily:

    >>> from autolat.google import Location
    >>> kml = """<Placemark>...</Placemark>"""
    >>> Location.from_kml(kml)
    <google.Location>
    >>> # or, if from a ElementTree
    >>> from xml.etree import ElementTree
    >>> tree = ElementTree.fromstring(kml)
    >>> Location.from_kml(tree)
    <google.Location>

And a sorted history can be generated from a full KML in much the same way:

    >>> from autolat.google import Location
    >>> kml = """<kml>...</kml>"""
    >>> Location.history_from_kml(kml)
    [<google.Location>, <google.Location>, ...]

## MobileMe

### Location

`MobileMe.locate_device` returns a `mobileme.Location` object, which has the following attributes:

* `accuracy` (meters)
* `datetime`
* `is_accurate`
* `is_locate_finished`
* `is_location_available`
* `is_old_location_result`
* `is_recent`
* `latitude`
* `longitude`
* `status`
* `status_string`
* `timestamp`

### Devices

`MobileMe.get_device` will return a dictionary with the following keys:

* `cls`
* `id`
* `osver`
* `type`

### Multiple Devices

If thre are multiple devices registered to a Mobile Me account, a device_id will need to be specified:

    >>> from autolat import MobileMe
    >>> m = MobileMe(user, passwd)
    >>> m.get_devices()
    ['device1_id', 'device2_id', ...]
    >>> m.locate_device(device_id)
    <mobileme.Location>


## WebService

There is a base Web Service class which tries to handle logging into a webservice that doesn't provide an API. It can easily be extended to add custom services:

    from autolat import WebService

    class Example(WebService):
        loginform_url = 'http://example.com/account'
        loginform_data = {
            'page': 'login',
        } # http://example.com/account?page=login
        loginform_id = 'login_form'
        loginform_user_field = 'username'
        loginform_pass_field = 'password'
        loginform_persist_field = 'remember_me'

`WebService` provides two methods:

* `_get(url, data, headers)`
* `_post(url, data, headers)`


## Actions

Actions can easily be added to the `autolat` command by extending the `autolat.actions.Action` class:

    from autolat.actions import Action

    class ExampleAction(Action):
        keyword = 'example'

        def setup(self):
            self.parser.add_argument('foo')
            self.parser.add_argument('bar', nargs='*')

        def main(self)
            print '%s: %s' % (self.args.foo, ' '.join(self.args.bar))

`Action.setup` is called when the actions are loaded and gives you an opportinity to add arguments to the parser. See `argparse` for more information on this subject. `Action.main` is called when the relevant `Action.keyword` is called (eg `autolat example`). `Action.args` (available in `Action.main` is a `argparse.Namespace` object)
