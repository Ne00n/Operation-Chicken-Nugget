import requests, json, time, ovh, os

path = os.path.dirname(os.path.realpath(__file__))
with open(f'{path}/config.json') as f: config = json.load(f)
with open(f'{path}/endpoints.json') as f: endpoints = json.load(f)
if os.path.isfile(f"{path}/history.json"):
    with open(f'{path}/history.json') as f: history = json.load(f)
else:
    history = {}

if not "gotify" in config:
    print("Please set the gotify url in the config") 
    config['gotify'] = ""
if not "endpoint" in config:
    print("Please set the endpoint in config.") 
    config['endpoint'] = ""
with open(f"{path}/config.json", 'w') as f: json.dump(config, f, indent=4)
if not config['endpoint'] or not config['gotify']: exit()

selectedEndpoint = config['endpoint']

client = ovh.Client(
    endpoint=selectedEndpoint['endpoint'],
    application_key=config['application_key'],
    application_secret=config['application_secret'],
    consumer_key=config['consumer_key'],
)

result = client.get("/dedicated/server")
for dedi in result:
    if not dedi in history:
        for run in range(3):
            try:
                requests.post(config['gotify'], json={"message": dedi,"priority": 10,"title": "New baguette detected"})
                break
            except Exception as e:
                print(f"Failed to post {config['gotify']} got error '{e}' retrying...")
                time.sleep(5)

with open(f"{path}/history.json", 'w') as f: json.dump(result, f, indent=4)