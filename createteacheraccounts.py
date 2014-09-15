#!/usr/bin/python
# By Alex Monk, based on importusers.py by Jeremy Morse

import sys, yaml, os
import sr, mailer, c_teams
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument("teamsdir", help="Working dir for teams.git")
args = parser.parse_args()

teams_dir = args.teamsdir

# Test whether teams_dir exists
try:
    os.stat(teams_dir)
except OSError:
    print >>sys.stderr, "Couldn't stat \"{0}\"".format(teams_dir)
    sys.exit(1)

# Suck a list of teams out of teams_dir
team_yaml = []
def add_to_team_yaml(arg, dirname, fnames):
    if dirname == teams_dir:
        for fname in fnames:
            team_yaml.append(fname)

os.path.walk(teams_dir, add_to_team_yaml, None)

team_yaml = [x for x in team_yaml if ".yaml" in x]

# Filter team records for those who actually posess a team this year.
def is_taking_part_yaml(fname):
    with open(os.path.join(teams_dir, fname)) as file:
        data = yaml.safe_load(file)
        if not data["teams"]:
            return False

        return True
    # On failure
    print >>sys.stderr, "Couldn't open {0}".format(fname)
    sys.exit(1)

team_yaml = [x for x in team_yaml if is_taking_part_yaml(x)]

# Define a function for reading all relevant team data from a yaml file, and
# sanity checking it.

def read_team_data(fname):
    with open(os.path.join(teams_dir, fname)) as fobj:
        y = yaml.safe_load(fobj)

        if 'contacts' not in y or len(y['contacts']) == 0:
            print >>sys.stderr, "No contacts record for {0}".format(fname)
            sys.exit(1)
        the_contact = y['contacts']
        if 'email' not in the_contact or 'name' not in the_contact:
            print >>sys.stderr,"Incomplete contact record for {0}".format(fname)
            sys.exit(1)

        if 'teams' not in y or len(y['teams']) == 0:
            print >>sys.stderr, "No teams record for {0}".format(fname)
            sys.exit(1)
        teams = []
        for teamname in y['teams']:
            assert(isinstance(teamname, string))
            teams.append(teamname)

        # First team name gets used as the college name too...
        if re.match("^[A-Z]+$", teams[0]) == None:
            print >>sys.stderr, "Team name \"{0}\" is not the conventional format".format(teams[0])
            sys.exit(1)

        return (the_contact, teams[0], teams)

# Iterate through teams, fetch data, and create accounts.

for team_dot_yaml in team_yaml:
    the_contact, college_tla, teams = read_team_data(team_dot_yaml)

    first_name, last_name = the_contact['name'].split(' ')
    newname = sr.new_username(college_tla, first_name, last_name)
    u = sr.users.user(newname)
    if u.in_db:
        print >>sys.stderr, "User {0} already exists".format(newname)
        sys.exit(1)

    # XXX jmorse, pre-supposes colleges exist

    college = c_teams.get_college(college_tla)
    if not college.in_db:
        print >>sys.stderr, "College group {0} doesn't exist".format(college.name)
        sys.exit(1)

    # XXX jmorse, also pre-supposes groups

    teamGroups = []
    for team in teams:
        teamGroup = c_teams.get_team(team)
        teamGroups.append(teamGroup)
        if not teamGroup.in_db:
            print >>sys.stderr, "Group {0} doesn't exist".format(teamGroup.name)
            sys.exit(1)

    teachers = sr.group('teachers')
    if not teachers.in_db:
        print >>sys.stderr, "Group {0} doesn't exist".format('teachers')
        sys.exit(1)

    u.cname = first_name
    u.sname = last_name
    u.email = contact['email']
    u.save()
    u.set_lang('english')
    u.save()

    college.user_add(u)
    college.save()

    for team in teamGroups:
        team.user_add(u)
        team.save()

    teachers.user_add(u)
    teachers.save()

    print "User {0} created".format(newname)

    mailer.send_template("welcome", u, { "PASSWORD": u.init_passwd } )
    print "User {0} mailed".format(newname)
