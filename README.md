autolat
=======

# Basic Usage

The easiest way to use autolat is to use the `autolat` command from your shell. The help should be self explainatory. If required options are not provided, they are prompted for:

    $ autolat [command] [options]

Currently, the only command is `update`.


# API

The API is currently quite simplistic.

To update your current location:

    >>> from autolat import Google, MobileMe
    >>> g = Google(user, passwd)
    >>> m = MobileMe(user, passwd)
    >>> l = m.locate_device()
    >>> g.update_latitude(l)

To get your latitude history:

    >>> from autolat import Google
    >>> g = Google(user, passwd)
    >>> h = g.get_history(start='mm/dd/yyyy', end='mm/dd/yyyy')


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

If you have multiple devices registered to your Mobile Me account, you will need to specify which device you wish to locate.

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


# Todo

* `Google.update_latitude` takes a `mobileme.Location` object which is silly and restricting
* `Google.get_history` takes American stupid-endian dates, switch to `datetime` objects
