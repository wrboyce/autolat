from webservice import WebService

from google import Google
from mobileme import MobileMe


def main():
    import getpass
    import logging
    from optparse import OptionParser
    import sys

    parser = OptionParser(usage='usage: %prog update [options]')
    parser.add_option('-g', '--google-user', dest='g_user', help='Google username, will be prompted for if not provided', metavar='GOOGLEUSER')
    parser.add_option('-G', '--google-pass', dest='g_pass', help='Google password, will be prompted for if not provided', metavar='GOOGLEPASS')
    parser.add_option('-m', '--mobileme-user', dest='m_user', help='MobileMe username, will be prompted for if not provided', metavar='MOBILEMEUSER')
    parser.add_option('-M', '--mobileme-pass', dest='m_pass', help='MobileMe password, will be prompted for if not provided', metavar='MOBILEMEPASS')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true', help='Increase verbosity level (INFO)')
    parser.add_option('-d', '--debug', dest='debug', action='store_true', help='Display debug information (DEBUG)')
    options, args = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        sys.exit(1)
    if args[0] != 'update':
        parser.print_help()
        sys.exit(1)

    g_user = getattr(options, 'g_user', None)
    if g_user is None:
        g_user = raw_input('Google Username: ').strip()
    g_pass = getattr(options, 'g_pass', None)
    if g_pass is None:
        g_pass = getpass.getpass('Google Password: ').strip()
    m_user = getattr(options, 'm_user', None)
    if m_user is None:
        m_user = raw_input('Mobile Me Username: ').strip()
    m_pass = getattr(options, 'm_pass', None)
    if m_pass is None:
        m_pass = getpass.getpass('Mobile Me Password: ').strip()

    logger = logging.getLogger('autolat')
    if getattr(options, 'verbose', False):
        logger.setLevel(logging.INFO)
    if getattr(options, 'debug', False):
        logger.setLevel(logging.DEBUG)

    g = Google(g_user, g_pass)
    m = MobileMe(m_user, m_pass)
    l = m.locate_device()
    g.update_latitude(l)
