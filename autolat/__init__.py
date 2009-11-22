from datetime import datetime
import getpass
import logging

import argparse

from webservice import WebService
from google import Google
from mobileme import MobileMe


def main():
    parser = argparse.ArgumentParser(prog='autolat')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Increase verbosity level (INFO)')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='Display debug information (DEBUG)')
    # add actions
    action_parsers = parser.add_subparsers(title='actions', description='valid actions', dest='action')
    # this little bit of magic builds a dictionary mapping action keywords to an instance of their class
    actions = dict((keyword, cls(action_parsers.add_parser(keyword))) for keyword, cls in Action.get_actions())
    # setup verbosity and invoke action
    args = parser.parse_args()
    if args.verbose and not args.debug:
        logging.getLogger('autolat').setLevel(logging.INFO)
    elif args.debug:
        logging.getLogger('autolat').setLevel(logging.DEBUG)
    return actions[args.action](args)

class Action(object):
    keyword = ''
    required_args = ()

    @classmethod
    def get_actions(cls):
        return [(action.keyword, action) for action in cls._get_actions() if action.keyword and action.keyword not in locals()['_[1]']]

    @classmethod
    def _get_actions(cls):
        yield cls
        for subcls in cls.__subclasses__():
            for subsubcls in subcls._get_actions():
                yield subsubcls

    def __init__(self, parser):
        # this builds a unique list of required arguments working up from the base classes.. Very hacky, but gets the job done.
        self.required_args = [arg_tuple for cls in reversed(self.__class__.__mro__) for arg_tuple in getattr(cls, 'required_args', ()) if not arg_tuple in locals()['_[1]']]
        self.parser = parser
        self.setup()

    def __call__(self, args):
        self.args = args
        self._get_required_args()
        self.main()

    def _get_required_args(self):
        for arg_tuple in self.required_args:
            if getattr(self.args, arg_tuple[0], None) is None:
                val = self._prompt_for_arg(*arg_tuple)
                setattr(self.args, arg_tuple[0], val)

    def _prompt_for_arg(self, name, prompt, hidden):
        val = getattr(self.args, name, None)
        if val is None:
            prompt = '%s: ' % prompt
            val = raw_input(prompt) if not hidden else getpass.getpass(prompt)
        return val

    def setup(self):
        pass

    def main(self):
        raise Exception("Abstract Action")

class GoogleAction(Action):
    required_args = (
        ('g_user', 'Google Username', False),
        ('g_pass', 'Google Password', True),
    )
    def __init__(self, *args, **kwargs):
        super(GoogleAction, self).__init__(*args, **kwargs)
        self.parser.add_argument('-g', '--google-user', dest='g_user', help='Google username, will be prompted for if not provided', metavar='GOOGLEUSER')
        self.parser.add_argument('-G', '--google-pass', dest='g_pass', help='Google password, will be prompted for if not provided', metavar='GOOGLEPASS')

class MobileMeAction(Action):
    required_args = (
        ('m_user', 'MobileMe Username', False),
        ('m_pass', 'MobileMe Password', True),
    )
    def __init__(self, *args, **kwargs):
        super(MobileMeAction, self).__init__(*args, **kwargs)
        self.parser.add_argument('-m', '--mobileme-user', dest='m_user', help='MobileMe username, will be prompted for if not provided', metavar='MOBILEMEUSER')
        self.parser.add_argument('-M', '--mobileme-pass', dest='m_pass', help='MobileMe password, will be prompted for if not provided', metavar='MOBILEMEPASS')

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
        try:
            return m.msg_device(**kwargs)
        except m.MultipleDevicesFound:
            print "Error: Multiple devices found in account:"
            for id in m.devices():
                print "\t%s" % id
            print
            kwargs['device_id'] = raw_input("Select a device: ")
            return m.msg_device(**kwargs)

class UpdateAction(GoogleAction, MobileMeAction):
    keyword = 'update'
    def main(self):
        g = Google(self.args.g_user, self.args.g_pass)
        m = MobileMe(self.args.m_user, self.args.m_pass)
        l = m.locate_device()
        g.update_latitude(timestamp=l.timestamp, latitude=l.latitude, longitude=l.longitude, accuracy=l.accuracy)
