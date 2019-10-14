from __future__ import print_function

import sr, sys

class group:
    """Manage groups.
    Subcommands:
     - list - List all groups
     - members - Display members of a group
     - create - Create a group
     - rm - Delete a group
     - addusers - Add users to a group
     - delusers - Remove users from a group"""

    def __init__(self, args):
        self.commands = { "help" : self.help,
                          "members" : self.members,
                          "create" : self.create,
                          "rm" : self.delete,
                          "list" : self.list,
                          "addusers" : self.addusers,
                          "delusers" : self.delusers }

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

    def list(self, args):
        """List all groups."""

        if len(args) > 0:
            print(self.__doc__)
            return

        print("\n".join(sr.groups.list()))

    def help(self, args):
        if len(args) < 1:
            print(self.__doc__)
            return

        if args[0] in self.commands:
            print(self.commands[args[0]].__doc__)
        else:
            print("Command not found.")
            print(self.__doc__)

        sys.exit(0)

    def create(self, args):
        """Create a group.
Usage:
	group create GROUP_NAME [USERS]"""

        if len(args) < 1:
            print(self.create.__doc__)
            return

        g = sr.group( args[0] )

        if g.in_db:
            print("Group '%s' already exists" % (args[0] ))
            return

        if len(args) > 1:
            users = args[1:]
            g.user_add(users)

        g.save()

    def delete(self, args):
        """Delete a group
Usage:
	group rm GROUPNAME"""
        if len(args) < 1:
            print(self.delete.__doc__)
            return

        for gname in args:
            g = sr.group( gname )

            if not g.in_db:
                print("Group '%s' doesn't exist" % ( gname ))
                continue

            g.rm()
            print("Group '%s' deleted." % ( gname ))

    def members(self, args):
        """Display group members.
Usage:
	group members GROUPNAME"""

        if len(args) < 1:
            print(self.members.__doc__)
            return

        g = sr.group( args[0] )

        if not g.in_db:
            print("Group '%s' not found\n" % (args[0]))
        else:
            print(" ".join(g.members))

    def addusers(self, args):
        """Add users to a group
Usage:
	group addusers GROUPNAME USERS"""

        if len(args) < 2:
            print(self.addusers.__doc__)
            return

        gname = args[0]
        users = args[1:]

        g = sr.group(gname)

        if not g.in_db:
            print("Group '%s' not found." % ( gname ))
            return

        f = g.user_add( users )

        if len(f) > 0:
            print("WARNING: The following users were not found and so were not added:")
            print(", ".join(f))

        g.save()

    def delusers(self, args):
        """Remove users from a group
Usage:
	group delusers GROUPNAME USERS"""

        if len(args) < 2:
            print(self.addusers.__doc__)
            return

        gname = args[0]
        users = args[1:]

        g = sr.group(gname)

        if not g.in_db:
            print("Group '%s' not found." % ( gname ))
            return

        not_members = g.user_rm( users )
        g.save()

        for uname in not_members:
            print("Unable to remove non-member '%s' from '%s'" % ( gname, uname ))
