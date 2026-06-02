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

selectedEndpoint = endpoints[config['endpoint']]

client = ovh.Client(
    endpoint=selectedEndpoint['endpoint'],
    application_key=config['application_key'],
    application_secret=config['application_secret'],
    consumer_key=config['consumer_key'],
)

dedis = client.get("/dedicated/server")
for dedi in dedis:
    print(f"Checking {dedi}")
    if not dedi in history:
        print(f"New dedi detected: {dedi}")
        history[dedi] = {"detected":int(time.time()),"notified":0,"errors":{"hardware":0}}

    if not "hardware" in history[dedi] and history[dedi]['errors']['hardware'] <= 2:
        try:
            hardware = client.get(f"/dedicated/server/{dedi}/specifications/hardware")
            history[dedi]['hardware'] = hardware
        except Exception as e:
            print(f"Failed to fetch hardware got error {e}")
            history[dedi]['errors']['hardware'] += 1
            continue
    elif history[dedi]['errors']['hardware'] > 2:
        history[dedi]['hardware'] = "Unable to fetch hardware."
    
    if not history[dedi]['notified']:
        for run in range(3):
            try:
                requests.post(config['gotify'], json={"message": json.dumps(history[dedi]['hardware'], indent=4),"priority": 10,"title": f"New baguette detected {dedi}"})
                history[dedi]['notified'] = 1
                break
            except Exception as e:
                print(f"Failed to post {config['gotify']} got error '{e}' retrying...")
                time.sleep(5)

with open(f"{path}/history.json", 'w') as f: json.dump(history, f, indent=4)