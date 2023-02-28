""" Dynatrace management zones request """

import argparse
from unicodedata import name
import yaml
import requests
import secrets
import json
from typing import List, NamedTuple

class NameHostGroup(NamedTuple):
    """ Holds team's entity and host-group-prefixes"""
    entity: int
    host_group: List[str]


# Defines the parser to accept arguments
parser = argparse.ArgumentParser(description='Dynatrace management zones tool')
# Argument defined for YML filename 
parser.add_argument("-f", "--filename", help = "Input YML file name", required=True)
args = parser.parse_args()
filename = args.filename.strip()

# Loads YML file passed as arg
with open(f"./{filename}") as stream:
    try:
        data_loaded  = yaml.safe_load(stream)
        team_names = []
        # Parses YML and creates a list of team names
        for item in data_loaded['teams']:
            # check if host-group-prefixes field is present
            if 'host-group-prefixes' in data_loaded['teams'][item]:
                # construct a namedtuple
                pos = NameHostGroup(data_loaded['teams'][item]['entity'], data_loaded['teams'][item]['host-group-prefixes'])
                team_names.append(pos)
            else:
                pos = NameHostGroup(data_loaded['teams'][item]['entity'],None)
                team_names.append(pos)
    except yaml.YAMLError as exc:
        print(exc)


def dt_auth(token: str, dt_url: str):
    """ Authentificates to Dynatrace using Token """ 
    try:
        resp = requests.get(dt_url, headers={'Authorization': "Api-Token " + token})
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def create_mz(token: str, dt_url: str, name: str):
    """ Creates a new management zone """
    try:
        headers = {'Authorization': "Api-Token " + token,
                   'Content-Type': 'application/json',}
        json_data = {'name': name,
                     'rule': []}

        resp = requests.post(dt_url, headers=headers, json=json_data)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_all_mz(token: str, dt_url: str) -> List[str]:
    """ Returns a dict with all available management zones """
    avail_mz = {}
    try:
        resp = requests.get(dt_url, headers={'Authorization': "Api-Token " + token})
        resp.raise_for_status()
        # Creates a list with available mz
        for nr, el in enumerate(resp.json()['values']):
            avail_mz[el['name']] = el['id']
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    return avail_mz


def deletes_all_rules(token: str, name: str, id:str):
    """ Deletes all the rules inside a MZ by overwritting with emty rules"""
    try:
        headers = {'Authorization': "Api-Token " + token}
        json_data = {
            'name': name,
            'rule': []}

        response = requests.put(f'https://heb24347.live.dynatrace.com/api/config/v1/managementZones/{id}',
                                headers=headers,
                                json=json_data)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def create_rule(token: str, name:str, id: str, payload:str):
    """ Creates a rule with predefined payload, by updating a MZ"""
    try:
        headers = {'Authorization': "Api-Token " + token}
        json_data = {
            'name': name,
            'rule': [payload]
                    }
        response = requests.put(f'https://heb24347.live.dynatrace.com/api/config/v1/managementZones/{id}',
                                headers=headers,
                                json=json_data)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

def add_rules(token: str, name: str, id: str, tup: NameHostGroup):
    """ Adds rules to mz"""
    if tup.host_group:
        for el in tup.host_group:
            payload = {'type': 'PROCESS_GROUP',
                    'enabled': True,
                    'propagationTypes': ['PROCESS_GROUP_TO_SERVICE',
                    'PROCESS_GROUP_TO_HOST'],
                    'conditions': [{'key': {'attribute': 'HOST_GROUP_NAME'},
                    'comparisonInfo': {'type': 'STRING',
                    'operator': 'BEGINS_WITH',
                    'value': el,
                    'negate': False,
                    'caseSensitive': True}}]}
            # Add rule to mz 
            create_rule(token, name, id, payload)
def main():
    # gets all mz 
    all_mz = get_all_mz(secrets.API_TOKEN, 'https://heb24347.live.dynatrace.com/api/config/v1/managementZones')
    for el in team_names:
        # Check if mz already exists
        if el.entity in all_mz.keys():
            # deletes all the rules 
            deletes_all_rules(secrets.API_TOKEN, el.entity, el.entity)
            # if there are non emty host-group-prefixes creates a new rule 
            add_rules(secrets.API_TOKEN, el.entity, el.entity, el)
        else:
            # creates a new mz
            create_mz(secrets.API_TOKEN, 'https://heb24347.live.dynatrace.com/api/config/v1/managementZones', el.entity)
            # adds rules to new mz if host-group-prefixes are present
            if el.host_group:
                add_rules(secrets.API_TOKEN, el.entity, el.entity, el)
                

if __name__ == "__main__":
    main()
