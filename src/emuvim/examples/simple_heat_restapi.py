import requests
import yaml
import json

files = {'file': open('postheat.yaml', 'rb')}
headers = {'Accept': 'application/x-yaml', 'Content-Type': 'application/x-yaml'}
r = requests.post('http://127.0.0.1:5000', files=files, headers=headers)
print headers
json_data = r.json()
print json_data
