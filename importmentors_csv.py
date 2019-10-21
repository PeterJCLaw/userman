#!/usr/bin/env python

from __future__ import print_function

import argparse
import csv
import sys

import mailer
import sr

REQUIRED_COLUMNS = (
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
    help="Don't send emails to the mentors",
)
args = parser.parse_args()

# Grab a useful group

mentors = sr.group('mentors')
if not mentors.in_db:
    print("Group {0} doesn't exist".format('mentors'), file=sys.stderr)
    exit(1)


# Check all rows have the required data
errors = []
mentors_infos = []
for line_no, info in enumerate(csv.DictReader(args.csv_file), start=1):
    for col in REQUIRED_COLUMNS:
        if not info.get(col):
            errors.append("Line {} is missing a {}".format(line_no, col))

    if '@' not in info['email']:
        errors.append("Invalid email {!r} on line {}".format(info['email'], line_no))

    mentors_infos.append(info)

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    exit(1)

# Iterate through users, fetch data, and create accounts.

count = 0
skipped = 0

for info in mentors_infos:
    first_name = info['first_name'].strip()
    last_name = info['last_name'].strip()
    email = info['email'].strip()

    username = (first_name[0] + last_name).lower()

    u = sr.users.user(username)

    if u.in_db:
        print("Username {0} already in db, skipping import".format(username), file=sys.stderr)
        skipped += 1
        continue

    u.cname = first_name
    u.sname = last_name
    u.email = email
    u.save()
    u.set_lang('english')
    u.save()

    mentors.user_add(u)
    mentors.save()

    print("User {0} created".format(username))

    if not args.no_emails:
        mailer.send_template("mentor-welcome", u, { "PASSWORD": u.init_passwd } )
        print("User {0} mailed".format(username))

    count += 1

print("Created {0} mentors and skipped {1} more".format(count, skipped), file=sys.stderr)
