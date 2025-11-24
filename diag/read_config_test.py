import json
from pprint import pprint

with open('fathom_config.json') as data_file:
    data = json.load(data_file)

pprint(data)