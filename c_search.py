from __future__ import print_function

import sys

import sr

class CmdSearch(object):
    """Find user accounts.
    Subcommands:
     - email - by email address
     - first - by first name
     - last - by last name
     - name - by full name
     """

    def __init__(self, args):
        self.commands = { 'email': ("email", "email address", "EMAIL")
#                       , 'name' : ("email", "full name", "FIRST LAST")
                        , 'first': ("cname", "first name", "FIRST_NAME")
                        , 'last' : ("sname", "last name", "LAST_NAME")
                        }

        if len(args) < 1 or args[0] == 'help' or \
                args[0] not in self.commands or len(args) < 2:
            self.help(args)
            return

        self._search(*args)

    def help(self, args):
        if len(args) < 1 or args[0] == 'help':
            print(self.__doc__)
            return

        if args[0] in self.commands:
            print("""Find a user by their {0}.
Usage:
	search email {1}""".format(*self.commands[args[0]][1:]))

        sys.exit(0)

    def _search(self, key, value):

        kwargs = { self.commands[key][0]: value }
        userids = sr.users.user.search(**kwargs)

        if len(userids) == 0:
            print("No matches.")
        else:
            print("Found {0} users:".format(len(userids)))
            print("\n".join(userids))
