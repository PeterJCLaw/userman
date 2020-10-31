#!/usr/bin/env python3

import sys
import csv
import sr
from c_teams import get_college, get_team

TEAMS_MAP_FILE = 'teams_map.csv'
KICKSTART_USER_PREFIX = 'kick_'

def get_teams():
    with open(TEAMS_MAP_FILE) as f:
        for line in f:
            tla, name = line.strip().split(',')
            yield tla, name

def ensure_college(tla, name, user):
    grp = get_college(tla[0:3])
    if not grp.in_db:
        grp.desc = name

    grp.user_add(user)
    grp.save()

def ensure_team(tla, user):
    grp = get_team(tla)
    grp.user_add(user)
    grp.save()

def create_team_user(tla, college_name):
    tu = sr.user(KICKSTART_USER_PREFIX + tla)
    tu.cname = tla
    tu.sname = college_name
    tu.email = ''
    tu.save()
    return tu

def set_password(tu):
    passwd = sr.users.GenPasswd()
    tu.set_passwd(new = passwd)
    tu.save()
    return passwd

def create_all(team_source):
    students_group = sr.group('students')

    passwds = {}

    for tla, college_name in team_source:
        tu = create_team_user(tla.lower(), college_name)
        passwds[tu.username] = set_password(tu)

        ensure_college(tla, college_name, tu)
        ensure_team(tla, tu)
        students_group.user_add(tu)

    students_group.save()
    return passwds

if __name__ == '__main__':
    passwds_map = create_all(get_teams())
    for u, p in passwds_map.items():
        print(u, p)
