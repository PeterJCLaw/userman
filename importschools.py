#!/usr/bin/env python3
# By Alex Monk, based on importusers.py by Jeremy Morse

from __future__ import print_function

import argparse
import os
import re
import sys

import yaml

import c_teams
import mailer
import sr

parser = argparse.ArgumentParser()
parser.add_argument("teamsdir", help="Working dir for teams.git")
parser.add_argument(
    "--no-emails",
    action='store_true',
    help="Don't send emails to the team-leaders"
)
args = parser.parse_args()

teams_dir = args.teamsdir

# Test whether teams_dir exists
try:
    os.stat(teams_dir)
except OSError:
    print("Couldn't stat \"{0}\"".format(teams_dir), file=sys.stderr)
    sys.exit(1)

# Suck a list of teams out of teams_dir
team_yaml = []
def add_to_team_yaml(_, dirname, fnames):
    if dirname == teams_dir:
        for fname in fnames:
            team_yaml.append(fname)

os.path.walk(teams_dir, add_to_team_yaml, None)

team_yaml = [x for x in team_yaml if re.match(r"^[A-Z]+\.yaml$", x) != None]

# Filter team records for those who actually posess a team this year.
def is_taking_part_yaml(fname):
    with open(os.path.join(teams_dir, fname)) as file:
        data = yaml.safe_load(file)
        if not data["teams"]:
            return False

        return True
    # On failure
    print("Couldn't open {0}".format(fname), file=sys.stderr)
    sys.exit(1)

team_yaml = [x for x in team_yaml if is_taking_part_yaml(x)]

# Define a function for reading all relevant team data from a yaml file, and
# sanity checking it.

def read_team_data(fname):
    with open(os.path.join(teams_dir, fname)) as fobj:
        y = yaml.safe_load(fobj)

        if 'contacts' not in y or len(y['contacts']) == 0:
            print("No contacts record for {0}".format(fname), file=sys.stderr)
            sys.exit(1)
        the_contact = y['contacts'][0] # Pick the first contact
        if 'email' not in the_contact or 'name' not in the_contact:
            print("Incomplete contact record for {0}".format(fname), file=sys.stderr)
            sys.exit(1)

        if 'teams' not in y or len(y['teams']) == 0:
            print("No teams record for {0}".format(fname), file=sys.stderr)
            sys.exit(1)

        if 'name' not in y:
            print("No school name record for {0}".format(fname), file=sys.stderr)
            sys.exit(1)

        teams = []
        for teamname in y['teams']:
            assert(isinstance(teamname, basestring))
            teams.append(teamname)

        # First team name gets used as the college name too...
        if re.match("^[A-Z]+$", teams[0]) == None:
            print("Team name \"{0}\" is not the conventional format".format(teams[0]), file=sys.stderr)
            sys.exit(1)

        return (the_contact, teams[0], teams, y['name'])

# Grab a useful group

teachers = sr.group('teachers')
if not teachers.in_db:
    print("Group {0} doesn't exist".format('teachers'), file=sys.stderr)
    sys.exit(1)

# Iterate through teams, fetch data, and create accounts.

count = 0
skipped = 0

for team_dot_yaml in team_yaml:
    team_leader, college_tla, teams, team_name = read_team_data(team_dot_yaml)

    # Does the desired college / team already exist?

    college = c_teams.get_college(college_tla)

    teamGroups = []
    for team in teams:
        teamGroup = c_teams.get_team(team)
        teamGroups.append(teamGroup)

    if college.in_db or len([x for x in teamGroups if x.in_db]) != 0:
        print("College {0} or associated teams already in db, skipping import".format(college_tla), file=sys.stderr)
        skipped += 1
        continue

    print("Creating groups + account for {0}".format(college_tla), file=sys.stderr)

    # Split at most once -- assume additional name parts go in the last name
    first_name, last_name = team_leader['name'].split(' ', 1)
    newname = sr.new_username(college_tla, first_name, last_name)
    u = sr.users.user(newname)

    u.cname = first_name
    u.sname = last_name
    u.email = team_leader['email']
    u.save()
    u.set_lang('english')
    u.save()

    college.user_add(u)
    college.desc = team_name
    college.save()

    for team in teamGroups:
        team.user_add(u)
        team.save()

    teachers.user_add(u)
    teachers.save()

    print("User {0} created".format(newname))

    if not args.no_emails:
        mailer.send_template("teacher_welcome", u, { "PASSWORD": u.init_passwd } )
        print("User {0} mailed".format(newname))

    count += 1

print("Created {0} teams and skipped {1} more".format(count, skipped), file=sys.stderr)
