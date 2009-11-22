import logging
import getpass

import argparse


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
