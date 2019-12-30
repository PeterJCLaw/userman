from __future__ import print_function

import os, sys, csv, sr, re
import mailer

TEAM_PREFIX = sr.TEAM_PREFIX
TEAM_PATTERN = "^%s[0-9A-Z]+$" % TEAM_PREFIX
COLLEGE_PREFIX = sr.COLLEGE_PREFIX
COLLEGE_PATTERN = "^%s[0-9A-Z]+$" % COLLEGE_PREFIX

try:
    input = raw_input
except NameError:
    pass

def get_team(tid):
    return sr.group( TEAM_PREFIX + str(tid) )

def get_college(cid):
    return sr.group( COLLEGE_PREFIX + str(cid) )

def list_groups_with_prefix(prefix):
    return sr.groups.list("%s*" % prefix)

def search_colleges(s):
    "Search through the colleges to find one with s its name"
    groups = list_groups_with_prefix(COLLEGE_PREFIX)

    res = []

    for gname in groups:
        group = sr.group(gname)

        if s.upper() in group.desc.upper():
            res.append(group)

    return res

def college_find( numsub ):
    colnum = None
    try:
        colnum = int(numsub)
    except ValueError:
        pass

    if colnum == None:
        cols = search_colleges(numsub)
    else:
        return get_college(colnum)

    if len(cols) > 1:
        # TODO: prompt the user
        print("\"%s\" matches more than one college." % numsub)
        sys.exit(1)

    if len(cols) == 0:
        print("\"%s\" matches no colleges." % numsub)
        sys.exit(1)

    return cols[0]

def new_team():
    i = 1
    tg = get_team(i)

    while tg.in_db:
        i += 1
        tg = get_team(i)

    return i

def print_table( rows ):
    widths = []
    for colnum in range(0, len(rows[0])):
        w = 0
        for row in rows:
            w = max(w, len(row[colnum]))
        widths.append(w)

    for row in rows:
        for colnum in range(0, len(row)):
            v = row[colnum]
            sys.stdout.write( v )
            sys.stdout.write( " " * (4 + widths[colnum] - len(v)) )
        sys.stdout.write( "\n" )

class CmdBase:
    def __init__(self, args):
        abort = False

        if hasattr(self, "min_args") and len(args) < self.min_args:
            print("Too few arguments to command.")
            abort = True

        if hasattr(self, "max_args") and len(args) > self.max_args:
            print("Too many arguments to command")
            abort = True

        if abort:
            if hasattr(self, "usage"):
                print("Usage: %s" % self.usage)
            sys.exit(1)

class CmdList(CmdBase):
    max_args = 0

    def __init__(self, args):
        CmdBase.__init__(self, args)

    def get_names(self, prefix, pattern):
        glist = list_groups_with_prefix(prefix)
        regex = re.compile(pattern)
        filtered = [gname for gname in glist if regex.match(gname)]
        return filtered

class CmdTeamList(CmdList):
    desc = "List the teams"

    def __init__(self, args):
        CmdList.__init__(self, args)

        names = self.get_names(TEAM_PREFIX, TEAM_PATTERN)

        for gname in names:
            print(gname)

class CmdTeamCreateCSV(CmdBase):
    desc = "Create a new team from a CSV file"
    usage = "COLLEGE_(NUMBER|SUBSTR) CSV_FILE [lang=LANG] [team=TEAMNO]"
    min_args, max_args = 2, 4

    def __init__(self, args):
        CmdBase.__init__(self, args)
        CDESC, CSV_FNAME = args[0], args[1]

        college_group = college_find( CDESC )
        newusers = self.form_new_users( CSV_FNAME, college_group )

        print()
        print("Will create %i users" % len(newusers))

        disp = [["username", "fname", "lname", "email"]]
        disp += [ [u.username, u.cname, u.sname, u.email] for u in newusers ]
        print_table( disp )

        teamno = None
        lang = "english"

        for arg in args[2:]:
            name, val = arg.split("=")

            if name == "team":
                teamno = int(val)
            elif name == "lang":
                lang = val
            else:
                raise Exception("Unsupported argument \"%s\"", arg)

        if teamno == None:
            teamno = new_team()

        print()
        print("They will form team %i." % teamno)
        print("And will be associated with %s: %s." % ( college_group.name, college_group.desc ))

        students_group = sr.group("students")
        team_group = get_team(teamno)

        print("Is this OK? (yes/no)", end=' ')
        resp = input()
        resp = resp.lower().strip()

        if resp == "yes":
            print("Creating users...")

            for u in newusers:
                print("\t", u.username)
                passwd = sr.users.GenPasswd()
                # Password has to be set after user is in db
                u.save()
                u.set_passwd( new = passwd )
                u.set_lang( lang )
                mailer.send_template( "welcome", u, { "PASSWORD": passwd } )

            print("Saving groups.")
            for g in students_group, team_group, college_group:
                g.user_add(newusers)
                g.save()

    def form_new_users(self, csv_fname, college_group):
        "Create the new user objects -- not in db yet."
        rows = self.read_csv( csv_fname )

        # Returns dictionary
        # keys are columns, values are column numbers
        colmap = self.discover_columns(rows)

        newusers = []

        for row in rows:
            fname, lname, email = [row[colmap[x]] for x in ["fname", "lname", "email"]]

            tmpset = [x.username for x in newusers]
            uname = sr.new_username(college_group, fname, lname, tmpset)
            u = sr.user( uname )
            u.cname = fname.strip().capitalize()
            u.sname = lname.strip().capitalize()
            u.email = email.strip().lower()
            newusers.append(u)

        return newusers

    def score_fname(self, col):
        fname = os.path.join( os.path.dirname(__file__), "data/yob2009.txt" )
        census = csv.reader( open(fname, "r") )
        census_fnames = set()
        for row in census:
            census_fnames.add( row[0].upper() )

        s = 0
        col = [x.upper() for x in col]
        for val in col:
            if val in census_fnames:
                s += 1

        return s

    def score_lname(self, col):
        fname = os.path.join( os.path.dirname(__file__), "data/surnames.txt" )
        census = open(fname, "r")

        census_lnames = set()
        for row in census.readlines():
            census_lnames.add( row.strip().upper() )

        s = 0
        col = [x.strip().upper() for x in col]
        for val in col:
            if val in census_lnames:
                s += 1

        return s

    def score_email(self, col):
        s = 0

        for val in col:
            if '@' in val:
                s += 1

        return s

    def discover_columns(self, rows):
        "Return a map of columns to use given csv rows"
        score_funcs = { "fname": self.score_fname,
                        "lname": self.score_lname,
                        "email": self.score_email }
        cols = { "fname":0, "lname":0, "email":0 }
        max_cols = max([len(row) for row in rows])
        scores = [dict(cols) for x in range(0, max_cols)]

        for colnum in range(0, max_cols):
            col = []
            for row in rows:
                try:
                    col.append( row[colnum] )
                except IndexError:
                    pass

            for field, fn in score_funcs.items():
                scores[colnum][field] += fn(col)

        for colname in cols.keys():
            colscores = [x[colname] for x in scores]
            cols[colname] = self.find_max_score(colscores)[0]

        while True:
            print("*" * 40)
            print("Column arrangement:")
            print(cols)

            print()
            print(" y = yes, create this team.")
            print(" change COLNAME colnum")
            print(" q = quit this utility")
            print(" e = show an example line")
            print("Command:", end=' ')

            resp = input()
            if len(resp) == 0:
                continue

            if resp[0] == "y":
                break

            if resp == "q":
                sys.exit(1)

            if resp == "e":
                print(rows[0])
                continue

            ss = resp.split()
            if ss[0] == "change":
                if len(ss) < 3:
                    print("Please specify a column name and number")
                    continue
                colname, num = ss[1], int(ss[2])
                if colname not in cols:
                    print("Invalid field name \"%s\"." % colname)
                    continue
                if num >= max_cols or num < 0:
                    print("Invalid column number.")
                    continue

                cols[colname] = num

        return cols


    def find_max_score(self, colscores):
        m = max(colscores)
        n = 0
        cols = []
        for score in colscores:
            if score == m:
                cols.append(n)
            n += 1
        return cols

    def read_csv(self, fname):
        csvfile = open( fname, "r" )
        r = csv.reader(csvfile)
        rows = []

        for row in r:
            rows.append([x.strip() for x in row])

        return rows

class CmdTeamInfo(CmdBase):
    desc = "Show information about a team"
    usage = "TEAM_ID"
    min_args, max_args = 1, 1

    def __init__(self, args):
        CmdBase.__init__(self, args)

        tid = args[0]
        tg = get_team(tid)
        if not tg.in_db:
            print("Team '%s' do not exist" % tid)
            sys.exit(1)

        # Group people into teachers, students, mentors and misc:
        g = ["teachers", "students", "mentors"]
        groups = {}
        team_grouped = {}

        for gname in g:
            groups[gname] = sr.group(gname)
            team_grouped[gname] = []

        for uname in tg.members:
            for gname, g in groups.items():
                if uname in g.members:
                    team_grouped[gname].append(uname)

        print("Team", tid)
        print()

        for status, ulist in team_grouped.items():
            if len(ulist):
                print(len(ulist), "%s:" % status)
                ulist.sort()

                for u in ulist:
                    print("\t%s" % u)
                print()
            else:
                print("No %s." % status)

        # Work out what college they're from
        college_gnames = set()

        for uname in team_grouped["students"] + team_grouped["teachers"]:
            u = sr.user(uname)
            assert u.in_db

            for gname in u.groups():
                if re.match( COLLEGE_PATTERN, gname ) != None:
                    college_gnames.add( gname )

        college_gnames = list(college_gnames)
        college_gnames.sort()
        if len(college_gnames):
            print("Colleges:")
            for gname in college_gnames:
                print("\t%s" % gname)
        else:
            print("No associated college.")

class CmdCollegeList(CmdList):
    desc = "List colleges"

    def __init__(self, args):
        CmdList.__init__(self, args)

        names = self.get_names(COLLEGE_PREFIX, COLLEGE_PATTERN)

        for gname in names:
            g = sr.group(gname)

            if hasattr(g, "desc"):
                desc = g.desc
            else:
                desc = "(no description)"

            print("%s: %s" % (gname, desc))

class CmdCollegeInfo(CmdBase):
    desc = "Show information about a college"
    usage = "COLLEGE_(NUMBER|SUBSTR)"
    min_args, max_args = 1,1

    def __init__(self, args):
        CmdBase.__init__(self, args)
        CDESC = args[0]
        college = college_find( CDESC )
        print("%s: %s" % (college.name , college.desc))

        teams = set()

        for uname in college.members:
            u = sr.user(uname)

            for g in u.groups():
                if re.match( TEAM_PATTERN, g ) != None:
                    teams.add(g)

        print("Teams:")
        for team in teams:
            print("\t -", team)

class CmdCollegeCreate(CmdBase):
    desc = "Create a new college"
    usage = "college create DESCRIPTION"
    min_args, max_args = 1,1

    def __init__(self, args):
        CmdBase.__init__(self, args)
        desc = args[0]

        g = self.next_free_college()
        g.desc = desc
        g.save()

        print("Created college group \"%s\"" % g.name)

    def next_free_college(self):
        i = 1

        while True:
            cg = get_college(i)
            if not cg.in_db:
                return cg
            i += 1

class CmdTeams:
    desc = "Team management commands"
    cmds = { "list": CmdTeamList,
             "from-csv": CmdTeamCreateCSV,
             "info": CmdTeamInfo }

    def __init__(self, args):
        if len(args) < 1 or args[0] not in self.cmds:
            if len(args):
                print("Invalid command")
            else:
                print("Manage teams.\n")

            print("Valid subcommands:")

            for cmd_name, cmdf in self.cmds.items():
                print("     - %s: %s" % ( cmd_name, cmdf.desc ))
            sys.exit(1)

        self.cmds[args[0]](args[1:])

class CmdColleges:
    desc = "Team management commands"
    cmds = { "info" : CmdCollegeInfo,
             "list": CmdCollegeList,
             "create": CmdCollegeCreate }

    def __init__(self, args):
        if len(args) < 1 or args[0] not in self.cmds:
            if len(args):
                print("Invalid command")
            else:
                print("Manage college groups.\n")
            print("Valid subcommands:")
            for cmd_name, cmdf in self.cmds.items():
                print("     - %s: %s" % ( cmd_name, cmdf.desc ))
            sys.exit(1)

        self.cmds[args[0]](args[1:])
