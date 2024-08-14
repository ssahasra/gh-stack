#!/usr/bin/env python3

# Copyright Sameer Sahasrabuddhe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import graphlib
import json
import subprocess

parser = argparse.ArgumentParser(description='Show all stacks of pull requests.')
parser.add_argument('--author', default="@me",
                    help='Show stacks for specified author')
Args = parser.parse_args()

Dump = subprocess.run(['gh', 'pr', 'list',
                       '--author', Args.author,
                       '--json', 'number,headRefName,baseRefName,url,title'],
                      capture_output=True)

Pulls = { x['headRefName']:x for x in json.loads(Dump.stdout) }

TS = graphlib.TopologicalSorter()
for PR in Pulls.values():
    Base = PR['baseRefName']
    Head = PR['headRefName']
    if Base in Pulls:
        TS.add(Head, Base)
    else:
        TS.add(Head)
TS.prepare()

Stacks = dict()
while TS.is_active():
    NewStacks = dict()
    for Head in TS.get_ready():
        TS.done(Head)
        Base = Pulls[Head]['baseRefName']
        if Base in Stacks:
            NewStacks[Head] = Stacks[Base] + [Head]
        else:
            NewStacks[Head] = [Head]

    Stacks = NewStacks

Count = 1
for Stack in Stacks.values():
    print(f'Stack {Count}:\n')
    Count += 1
    for Head in reversed(Stack):
        PR = Pulls[Head]
        print(f"  - {PR['title']} [#{PR['number']}]")
        print(f"    {Head}")
        print(f"    {PR['url']}\n")
