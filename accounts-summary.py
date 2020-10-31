#!/usr/bin/env python3

from __future__ import print_function

import sr
from c_teams import CmdList, print_table, TEAM_PREFIX, TEAM_PATTERN

team_leaders = set(sr.group('teachers').members)

rows = [
    ('Team', 'Leaders', 'Competitors')
]

for team_name in CmdList(()).get_names(TEAM_PREFIX, TEAM_PATTERN):
    team = sr.group(team_name)

    num_team_leaders = 0
    num_competitors = 0

    for member in team.members:
        if member in team_leaders:
            num_team_leaders += 1
        else:
            num_competitors += 1

    rows.append((
        team_name[len(TEAM_PREFIX):],
        str(num_team_leaders),
        str(num_competitors),
    ))

print_table(rows)
