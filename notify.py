import requests, json, ovh, os

with open('config.json') as f: config = json.load(f)
with open('endpoints.json') as f: endpoints = json.load(f)
path = os.path.dirname(os.path.realpath(__file__))
if os.path.isfile(f"{path}/history.json"):
    with open('history.json') as f: history = json.load(f)
else:
    history = {}

selectedEndpoint = endpoints["ca.api.ovh.com"]

client = ovh.Client(
    endpoint=selectedEndpoint['endpoint'],
    application_key=config['application_key'],
    application_secret=config['application_secret'],
    consumer_key=config['consumer_key'],
)

result = client.get("/dedicated/server")
for dedi in result:
    if not dedi in history:
        resp = requests.post(config['gotify'], json={"message": dedi,"priority": 10,"title": "New baguette detected"})

with open(f"{path}/history.json", 'w') as f: json.dump(result, f, indent=4)