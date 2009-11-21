from datetime import datetime
import getpass
import logging
from optparse import OptionParser
import sys


from webservice import WebService
from google import Google
from mobileme import MobileMe


def main():
    parser = OptionParser(usage='usage: %prog [action] [options]\nactions: update, get_history')
    parser.add_option('-g', '--google-user', dest='g_user', help='Google username, will be prompted for if not provided', metavar='GOOGLEUSER')
    parser.add_option('-G', '--google-pass', dest='g_pass', help='Google password, will be prompted for if not provided', metavar='GOOGLEPASS')
    parser.add_option('-m', '--mobileme-user', dest='m_user', help='MobileMe username, will be prompted for if not provided', metavar='MOBILEMEUSER')
    parser.add_option('-M', '--mobileme-pass', dest='m_pass', help='MobileMe password, will be prompted for if not provided', metavar='MOBILEMEPASS')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true', help='Increase verbosity level (INFO)')
    parser.add_option('-d', '--debug', dest='debug', action='store_true', help='Display debug information (DEBUG)')
    options, args = parser.parse_args()
    if not args:
        parser.print_help()
        sys.exit(1)
    elif args[0] == 'update':
        return _main_update(args, options)
    elif args[0] == 'get_history':
        return _main_get_history(args, options)
    else:
        parser.print_help()
        sys.exit(1)

def _get_opt(options, name, prompt, hidden=False):
    val = getattr(options, name, None)
    if val is None:
        prompt = '%s: ' % prompt
        val = raw_input(prompt) if not hidden else getpass.getpass(prompt)
    return val

def _main_update(args, options):
    g_user = _get_opt(options, 'g_user', 'Google Username')
    g_pass = _get_opt(options, 'g_user', 'Google Password', True)
    m_user = _get_opt(options, 'm_user', 'MobileMe Username')
    m_pass = _get_opt(options, 'm_user', 'MobileMe Password', True)

    logger = logging.getLogger('autolat')
    if getattr(options, 'verbose', False):
        logger.setLevel(logging.INFO)
    if getattr(options, 'debug', False):
        logger.setLevel(logging.DEBUG)

    g = Google(g_user, g_pass)
    m = MobileMe(m_user, m_pass)
    l = m.locate_device()
    g.update_latitude(timestamp=l.timestamp, latitude=l.latitude, longitude=l.longitude, accuracy=l.accuracy)

def _main_get_history(args, options):
    try:
        if not len(args) == 3:
            raise Exception
        start = datetime.strptime(args[1], '%d/%m/%Y')
        end = datetime.strptime(args[1], '%d/%m/%Y')
    except Exception:
        raise
        print "usage: get_history dd/mm/yyyy dd/mm/yyyy"
        sys.exit(1)
    g_user = _get_opt(options, 'g_user', 'Google Username')
    g_pass = _get_opt(options, 'g_user', 'Google Password', True)

    g = Google(g_user, g_pass)
    for loc in g.get_history(start, end):
        print '%s' % loc
