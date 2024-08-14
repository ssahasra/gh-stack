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

RequestFields = 'number,headRefName,baseRefName,url,title,author'

def getPullRequest(PR):
    Dump = subprocess.run(['gh', 'pr', 'view', Args.pr,
                           '--json', RequestFields],
                          capture_output=True)
    if Dump.returncode:
        exit("Unable to fetch specified pull request")
    PR = json.loads(Dump.stdout)
    return PR

def getPullRequestsForAuthor(Author):
    Dump = subprocess.run(['gh', 'pr', 'list',
                           '--author', Author,
                           '--json', RequestFields],
                          capture_output=True)
    if Dump.returncode:
        exit("Unable to fetch pull request for specified author")
    Pulls = { x['headRefName']:x for x in json.loads(Dump.stdout) }
    return Pulls

def printReversedStack(Stack, Pulls):
    for Head in reversed(Stack):
        PR = Pulls[Head]
        print(f"  - {PR['title']} [#{PR['number']}]")
        print(f"    {Head}")
        print(f"    {PR['url']}\n")

def printReversedStackList(Stacks, Pulls):
    Count = 1
    for Stack in Stacks.values():
        print(f'Stack {Count}:\n')
        Count += 1
        printReversedStack(Stack, Pulls)

def getStackForPullRequest(RequestId):
    PR = getPullRequest(RequestId)
    Author = PR['author']['login']
    Pulls = getPullRequestsForAuthor(Author)
    Stack = [PR['headRefName']]
    Base = PR['baseRefName']
    while Base in Pulls:
        Stack.append(Base)
        Base = Pulls[Base]['baseRefName']
    return Stack, Pulls

def printAllStacksForAuthor(Author):
    Pulls = getPullRequestsForAuthor(Author)
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
    printReversedStackList(Stacks, Pulls)

parser = argparse.ArgumentParser(description='Show all stacks of pull requests.')
parser.add_argument('--author', default="@me",
                    help='Show stacks for specified author')
parser.add_argument('--pr', help='Show the stack headed by specified PR')
Args = parser.parse_args()

if Args.pr:
    Stack, Pulls = getStackForPullRequest(Args.pr)
    printReversedStack(Stack, Pulls)
    exit()

printAllStacksForAuthor(Args.author)
