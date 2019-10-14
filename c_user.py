from __future__ import print_function

import sr, sys
import getpass
import mailer

class user:
    """Manage user accounts.
    Subcommands:
     - list - List all users
     - info - Display user information
     - add - Add a user
     - rm - Remove a user
     - groups - Display a list of groups a user is in
     - auto - Create, set a random password, and email the new user
     - passwd - Set the user password
     - rand_pass - Set the user password randomly.
     """

    def __init__(self, args):
        self.commands = { "help" : self.help,
                          "info" : self.info,
                          "add" : self.add,
                          "rm" : self.delete,
                          "list" : self.list,
                          "groups" : self.groups,
                          "auto" : self.auto,
                          "passwd" : self.passwd,
                          "rand_pass" : self.rand_pass
                          }

        if len(args) < 1:
            self.help([])
            return

        if args[0] in self.commands:
            cmd = args[0]

            if len(args) == 1:
                args = []
            else:
                args = args[1:]

            self.commands[cmd](args)
        else:
            print(self.__doc__)

    def _get_user(self, username, match_case = True):
        return sr.users.user(username, match_case)

    def help(self, args):
        if len(args) < 1:
            print(self.__doc__)
            return

        if args[0] in self.commands:
            print(self.commands[args[0]].__doc__)

        sys.exit(0)

    def add(self, args):
        """Add a user.
Usage:
	user add USERNAME FIRST_NAME LAST_NAME EMAIL"""

        if len(args) < 4:
            print(self.add.__doc__)
            return

        # Avoid creating multiple users with similar names
        u = self._get_user( args[0], match_case = False )

        if u.in_db:
            print("User '%s' already exists" % ( u.username ))
            return

        u.cname = args[1]
        u.sname = args[2]
        u.email = args[3]

        if u.save():
            print("User '%s' successfully created." % (args[0]))
        else:
            print("Failed to create user '%s'")

    def list(self, args):
        """List all users"""
        if len(args) > 0:
            print(self.list.__doc__)
            return

        print(" ".join(sr.users.list()))

    def delete(self, args):
        """Delete a user.
Usage:
	user rm USERNAME(S)"""
        if len(args) < 1:
            print(self.delete.__doc__)
            return

        for username in args:
            u = self._get_user( username )
            groups = u.groups()

            if not u.in_db:
                print("User '%s' doesn't exist" % ( username ))
                continue

            if u.delete():
                print("User '%s' deleted" % (username))

                for group in groups:
                    g = sr.group(group)
                    g.user_rm(u.username)
                    g.save()

            else:
                print("Error: User '%s' could not be deleted")

    def info(self, args):
        """Print information about a user.
Usage:
	user info USERNAME"""

        if len(args) < 1:
            print(self.info.__doc__)
            return

        u = self._get_user( args[0] )

        if not u.in_db:
            print("User '%s' not found\n" % (args[0]))
        else:
            print(u)

    def auto(self, args):
        """Automate user creation:
  * Create the new user
  * Set a random password
  * Email them the new password

Usage:
	user auto USERNAME FIRST_NAME LAST_NAME EMAIL [LANG]
"""
        if len(args) < 4:
            print(self.auto.__doc__)
            return

        # Avoid creating multiple users with similar names
        u = self._get_user( args[0], match_case = False )

        if u.in_db:
            print("User '%s' already exists" % (args[0] ))
            return

        u.cname = args[1]
        u.sname = args[2]
        u.email = args[3]

        if not u.save():
            return False

        if len(args) > 4:
            u.set_lang( args[4] )
        else:
            "Default to English"
            u.set_lang( "english" )

        mailer.send_template( "welcome", u, { "PASSWORD": u.init_passwd } )
        print("User '%s' created and mailed." % (args[0]))

    def passwd(self,args):
        """Set the user password.
Usage:
	user passwd USERNAME
"""

        if len(args) < 1:
            print(self.passwd.__doc__)
            return

        uname = args[0]

        u = self._get_user( uname )

        if not u.in_db:
            print("User '%s' not found\n" % ( uname ))
            return

        if u.set_passwd( new = getpass.getpass("New password:") ):
            print("Password set")
        else:
            print("Failed to set password")


    def rand_pass(self, args):
        """Email the user a new random password.
Usage:
	user rand_pass USERNAME"""

        if len(args) < 1:
            print(self.rand_pass.__doc__)
            return

        uname = args[0]
        u = self._get_user( uname )

        if not u.in_db:
            print("User '%s' not found\n" % ( uname ))
            return False

        new_passwd = sr.users.GenPasswd()
        u.set_passwd( new = new_passwd )
        mailer.send_template( "new-password", u, { "PASSWORD": new_passwd } )
        return True

    def groups(self, args):
        """Display a list of the groups a user is in.
Usage:
	user groups USERNAME"""

        if len(args) < 1:
            print(self.groups.__doc__)
            return

        uname = args[0]

        u = self._get_user( uname )

        if not u.in_db:
            print("User '%s' not found\n" % ( uname ))
        else:
            groups = u.groups()

            if len(groups) == 0:
                print("'%s' is not in any groups." % (uname))
            else:
                print(" ".join(groups))
