#!/usr/bin/env python

from __future__ import print_function

import argparse
import csv
import os
import re
import sys

import yaml

import c_teams
import mailer
import sr

# Note: we assume a a single team per school for now.

REQUIRED_COLUMNS = (
    'tla',
    'organisation_name',
    'first_name',
    'last_name',
    'email',
)

parser = argparse.ArgumentParser()
parser.add_argument(
    "csv_file",
    type=argparse.FileType(mode='r'),
    help="CSV file with columns '{}'.".format(
        "', '".join(REQUIRED_COLUMNS)
    ),
)
parser.add_argument(
    "--no-emails",
    action='store_true',
    help="Don't send emails to the team-leaders",
)
args = parser.parse_args()

# Grab a useful group

teachers = sr.group('teachers')
if not teachers.in_db:
    print("Group {0} doesn't exist".format('teachers'), file=sys.stderr)
    sys.exit(1)


# Check all rows have the required data
errors = []
teams_infos = []
for line_no, info in enumerate(csv.DictReader(args.csv_file), start=1):
    for col in REQUIRED_COLUMNS:
        if not info.get(col):
            errors.append("Line {} is missing a {}".format(line_no, col))
    teams_infos.append(info)

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    exit(1)

# Iterate through teams, fetch data, and create accounts.

count = 0
skipped = 0

for info in teams_infos:
    college_tla = info['tla'].strip().upper()
    org_name = info['organisation_name'].strip()
    first_name = info['first_name'].strip()
    last_name = info['last_name'].strip()
    email = info['email'].strip()

    # Does the desired college / team already exist?

    college_group = c_teams.get_college(college_tla)
    team_group = c_teams.get_team(college_tla)

    if college_group.in_db or team_group.in_db:
        print("College {0} or associated teams already in db, skipping import".format(college_tla), file=sys.stderr)
        skipped += 1
        continue

    print("Creating groups + account for {0}".format(college_tla), file=sys.stderr)

    newname = sr.new_username(college_tla, first_name, last_name)
    u = sr.users.user(newname)

    u.cname = first_name
    u.sname = last_name
    u.email = email
    u.save()
    u.set_lang('english')
    u.save()

    college_group.user_add(u)
    college_group.desc = org_name
    college_group.save()

    team_group.user_add(u)
    team_group.save()

    teachers.user_add(u)
    teachers.save()

    print("User {0} created".format(newname))

    if not args.no_emails:
        mailer.send_template("teacher_welcome", u, { "PASSWORD": u.init_passwd } )
        print("User {0} mailed".format(newname))

    count += 1

print("Created {0} teams and skipped {1} more".format(count, skipped), file=sys.stderr)
