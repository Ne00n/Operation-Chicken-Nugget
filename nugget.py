import requests, hashlib, json, time, ovh, sys, os
from datetime import datetime
from random import randint

with open('config.json') as f: config = json.load(f)
with open('endpoints.json') as f: endpoints = json.load(f)
path = os.path.dirname(os.path.realpath(__file__))

if not "autoPay" in config: exit("autoPay missing in config.")
if not "anyDatacenter" in config: exit("anyDatacenter missing in config.")

if len(sys.argv) == 1:
    planConfig = {}
    print("Please select the endpoint for the catalog")
    for index, option in enumerate(endpoints): print(index, option)
    selected = input("Endpoint: ")
    for index, option in enumerate(endpoints):
        if int(selected) == index:
            selectedEndpoint = endpoints[option]
            selectedEndpoint['endpointAPI'] = option
            break
else:
    if os.path.isfile(f"{path}/plans/{sys.argv[1]}"):
        print(f"Loading {sys.argv[1]}")
        with open(f"{path}/plans/{sys.argv[1]}") as handle: planConfig = json.loads(handle.read())
        selectedEndpoint = endpoints[planConfig['endpoint']]
        selectedEndpoint['endpointAPI'] = planConfig['endpoint']
    else:
        exit(f"Unable to find file plans/{sys.argv[1]}")

def call(url,payload=None,runs=10):
    for run in range(runs):
        try:
            if payload:
                response = requests.post(url, headers=headers, data=json.dumps(payload))
            else:
                response = requests.get(url, headers=headers)
            if response.status_code == 200: return response
            print(f"Got {response.status_code} for {url} retrying...")
            print(json.dumps(response.json(), indent=4))
        except Exception as e:
            print(f"Failed to fetch {url} got error '{e}' retrying...")
        time.sleep(5)
    exit(f"Unable to fetch {url}")

headers = {'Accept': 'application/json','X-Ovh-Application':config['application_key'],'X-Ovh-Consumer':config['consumer_key'],
'Content-Type':'application/json;charset=utf-8','Host':selectedEndpoint['endpointAPI']}

def datacenterToRegion(availableDataCenter):
    if "bhs" in availableDataCenter:
        return "canada"
    elif "vin" in availableDataCenter or "hil" in availableDataCenter:
        return "northamerica"
    else:
        return "europe"

if len(sys.argv) == 1:
    print(f"Loading catalog from {selectedEndpoint['catalog']}")
    catalogRaw = call(selectedEndpoint['catalog'])
    catalog = catalogRaw.json()
    catalogUnsorted = {}
    currency = catalog['locale']['currencyCode']

    for plan in catalog['plans']:
        for price in plan['pricings']:
            if "installation" in price['capacities']: continue
            if price['interval'] != 1: continue
            catalogUnsorted[plan['planCode']] = {"price":int(price['price']),"plan":plan}

    catalogSorted = dict(sorted(catalogUnsorted.items(), key=lambda item: item[1]['plan']['invoiceName']))

    for index, (planCode,data) in enumerate(catalogSorted.items()):
        if not "product" in data['plan']: continue
        print(f"{index} {data['plan']['invoiceName']} ({planCode}, {data['price'] / 1000_000_00} {currency})")

    print("What plan do you want to buy? e.g 2 for KS-LE-B")

    lookup = input()
    for offerIndex, (planCode,data) in enumerate(catalogSorted.items()):
        if "product" in data['plan'] and offerIndex == int(lookup):
            planConfig['planCode'] = planCode
            for addon in data['plan']['addonFamilies']:
                if addon['mandatory'] != True: continue
                if len(addon['addons']) == 1:
                    planConfig[addon['name']] = addon['addons'][0]
                    print(f"Automatically selected configuration: {addon['addons'][0]}")
                    continue
                for index, option in enumerate(addon['addons']): print(index, option)
                print("Please select configuration")
                selected = input()
                for index, option in enumerate(addon['addons']):
                    if int(selected) == index: planConfig[addon['name']] = option
            break


    # Our: {'planCode': '24ska01', 'storage': 'softraid-1x480ssd-24ska01', 'bandwidth': 'bandwidth-100-24sk', 'memory': 'ram-64g-noecc-2133-24ska01', 'endpoint': 'ca.api.ovh.com', 'datacenter': 'rbx', 'region': 'europe'}
    # Their: {'fqn': '24ska01.ram-64g-noecc-2133.softraid-1x480ssd', 'planCode': '24ska01', 'memory': 'ram-64g-noecc-2133', 'server': '24ska01', 'storage': 'softraid-1x480ssd'}
    # split by `-` and take all but last part
    memoryName = "-".join(planConfig['memory'].split("-")[:-1])
    storageName = "-".join(planConfig['storage'].split("-")[:-1])
    planConfig['fqn'] = f"{planConfig['planCode']}.{memoryName}.{storageName}"

    print(f"Loading availability for {planConfig['fqn']}")
    dcWanted = []

    availabilityRaw = call(f'{selectedEndpoint["availability"]}?excludeDatacenters=false&planCode={planConfig["planCode"]}&server={planConfig["planCode"]}')
    availability = availabilityRaw.json()
    print("Available in the following datacenters")
    if not availability:
        print(f"Failed to fetch availability, please enter the desired datacenters manualy.")
        planConfig['datacenter'] = input()
    else:
        for index, datacenter in enumerate(availability[0]['datacenters']):
            print(datacenter['datacenter'])
        print("Please enter the desired datacenter e.g waw you can also enter multiple like fra,gra,sbg")
        print("Keep in mind, they have to be in the same region.")
        planConfig['datacenter'] = input()

    planConfig['region'] = datacenterToRegion(planConfig['datacenter'])
    planConfig['endpoint'] = selectedEndpoint['endpointAPI']
print(f"Your selected config")
print(planConfig)
filename = f"{path}/plans/{planConfig['planCode']}-{planConfig['memory']}-{planConfig['datacenter']}.json"
with open(filename, 'w') as f: json.dump(planConfig, f, indent=4)
print(f"Saved as {filename}")
time.sleep(2)

# Instantiate. Visit https://api.ovh.com/createToken/?GET=/me
# to get your credentials
client = ovh.Client(
    endpoint=selectedEndpoint['endpoint'],
    application_key=config['application_key'],
    application_secret=config['application_secret'],
    consumer_key=config['consumer_key'],
)

# Print nice welcome message
print("Welcome", client.get('/me')['firstname'])

def createCart(config, planConfig, selectedEndpoint, call, client):
    #getting current time
    print("\tGetting Time")

    response = call(f"https://{selectedEndpoint['endpointAPI']}/1.0/auth/time")
    timeDelta = int(response.text) - int(time.time())

    # creating a new cart
    cart = client.post("/order/cart", ovhSubsidiary=config['ovhSubsidiary'], _need_auth=False)

    #assign new cart to current user
    client.post("/order/cart/{0}/assign".format(cart.get("cartId")))

    #putting KS-A into cart
    #result = client.post(f'/order/cart/{cart.get("cartId")}/eco',{"duration":"P1M","planCode":"22sk010","pricingMode":"default","quantity":1})
    #apparently this shit sends malformed json whatever baguette
    payload = {'duration':'P1M','planCode':planConfig['planCode'],'pricingMode':'default','quantity':quantity}

    call(f"https://{selectedEndpoint['endpointAPI']}/1.0/order/cart/{cart.get('cartId')}/eco", payload)
    #getting current cart
    response = call(f"https://{selectedEndpoint['endpointAPI']}/1.0/order/cart/{cart.get('cartId')}")
    #modify item for checkout
    itemID = response.json()['items'][0]

    print(f'\tGetting current cart {cart.get("cartId")}')

    #set configurations
    configurations = [
        {'label':'region','value':planConfig['region']},
        {'label':'dedicated_datacenter','value':planConfig['datacenter']},
        {'label':'dedicated_os','value':'none_64.en'}
    ]

    for entry in configurations:
        print(f"\tSetting {entry}")
        call(f"https://{selectedEndpoint['endpointAPI']}/1.0/order/cart/{cart.get('cartId')}/item/{itemID}/configuration",entry)

    #set options
    options = [
        {'itemId':itemID,'duration':'P1M','planCode':planConfig['bandwidth'],'pricingMode':'default','quantity':quantity},
        {'itemId':itemID,'duration':'P1M','planCode':planConfig['storage'],'pricingMode':'default','quantity':quantity},
        {'itemId':itemID,'duration':'P1M','planCode':planConfig['memory'],'pricingMode':'default','quantity':quantity}
    ]
    for option in options:
        print(f"\tSetting {option}")
        call(f"https://{selectedEndpoint['endpointAPI']}/1.0/order/cart/{cart.get('cartId')}/eco/options", option)


    return timeDelta,cart

def checkoutCart(dc, cart, timeDelta):
    retry = 0
    print(f"Checking out cart '{cart.get('cartId')}' for {dc}, auto pay: {config['autoPay']}")

    payload={'autoPayWithPreferredPaymentMethod':config['autoPay'],'waiveRetractationPeriod':config['autoPay']}
    #prepare sig
    target = f"https://{selectedEndpoint['endpointAPI']}/1.0/order/cart/{cart.get('cartId')}/checkout"
    now = str(int(time.time()) + timeDelta)

    signature = hashlib.sha1()
    signature.update("+".join([config['application_secret'], config['consumer_key'],'POST', target, json.dumps(payload), now]).encode('utf-8'))
    headers['X-Ovh-Signature'] = "$1$" + signature.hexdigest()
    headers['X-Ovh-Timestamp'] = now

    try:
        response = requests.post(target, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print(response.status_code)
            print(json.dumps(response.json(), indent=4))

            url = response.json()['url']

            if(config['autoPay']):
                print(f"Success! You got an order for server in {dc}")
            else:
                print(f"Success! You got an order for server in {dc}, go and pay the invoice!")

            print(f"Done, see order at {url}")
            return True
        else:
            print("Got non 200 response code on checkout, retrying")
            print(json.dumps(response.json(), indent=4))
            retry += 1

            if retry > 15:
                print("Failed too many times, trying another datacenter if requested")
                return False

    except Exception as e:
        print(f"Unable to submit order got '{e}' as error")
        retry += 1
        if retry > 15:
            print("Failed too many times, trying another datacenter if requested")
            return False

# Each DC has its own cart
carts = {}

for dc in dcWanted:
    planConfig['region'] = datacenterToRegion(dc)

    print(f"Preparing cart for {dc} in {planConfig['region']}")

    planConfig['datacenter'] = dc
    carts[dc] = createCart(config, planConfig, selectedEndpoint, call, client)

    print(f"Cart for {dc} ready")

def checkStock(stock, planConfig):
    if not stock:
        print(f"Empty location list for {planConfig['planCode']}, not available for order anymore?")
        return False

    configurationWanted = [fqn for fqn in stock if fqn['fqn'] == planConfig['fqn']]

    if len(configurationWanted) == 0:
        print(f"No matching fqn found in availability list for {planConfig['fqn']}")
        return False
    elif len(configurationWanted) > 1:
        print(f"Multiple matching fqns found in availability list for {planConfig['fqn']}")
        return False
    else:
        configurationWanted = configurationWanted[0]

    unavailable_statuses = ['unavailable', 'comingSoon']

    # all datacenters where availability != unavailable
    allStock = [dc['datacenter'] for dc in configurationWanted['datacenters']]
    stockAvailable = [dc['datacenter'] for dc in configurationWanted['datacenters'] if (dc['availability'] not in unavailable_statuses)]

    if stockAvailable and len(stockAvailable) > 0:
        print(f"| Available: {stockAvailable}")

        # check if any of the available datacenters is in the cart
        for dc in dcWanted:
            if dc in stockAvailable:
                print(f"\nYAY, got server in stock at {dc}!\n")
                timeDelta, cart = carts[dc]
                del carts[dc]
                checkoutCart(dc, cart, timeDelta)

                return True
    else:
        print(f"| no stock ({' '.join(allStock)})")

while True:
    #the order expires after about 1 day
    for check in range(70000):
        now = datetime.now()
        print(f'Run {check+1} {now.strftime("%H:%M:%S")} {planConfig['planCode']} ', end='')

        # Fetch stock
        try:
            response = requests.get(f'{selectedEndpoint["availability"]}?excludeDatacenters=false&planCode={planConfig["planCode"]}')
        except Exception as e:
            print(f"Failed to fetch stock got error '{e}' retrying...")
            time.sleep(2)

            continue

        # Parse stock & buy if available
        if response.status_code == 200:
            stock = response.json()
            score = 0
            if not stock:
                print(f"Unable to find {planConfig['planCode']} in availability.")
                time.sleep(randint(5,10))
                continue
            for configuration in stock:
                if not configuration['memory'] in planConfig['memory'] or not configuration['storage'] in planConfig['storage']: continue
                for datacenter in configuration['datacenters']:
                    if datacenter['availability'] != "unavailable" and datacenter['availability'] != "comingSoon" and config['anyDatacenter']:
                        availableDataCenter = datacenter['datacenter']
                        score = score +1
                        break
                    elif datacenter['availability'] != "unavailable" and datacenter['availability'] != "comingSoon" and datacenter['datacenter'] in planConfig['datacenter']:
                        availableDataCenter = datacenter['datacenter']
                        score = score +1
                        break
        else:
            time.sleep(randint(5,10))
            continue
        #lets checkout boooyaaa
        if score >= 1:
            #autopay should be set to true if you want automatic delivery, otherwise it will just generate a invoice
            payload={'autoPayWithPreferredPaymentMethod':config['autoPay'],'waiveRetractationPeriod':config['autoPay']}
            #prepare sig
            target = f"https://{selectedEndpoint['endpointAPI']}/1.0/order/cart/{cart.get('cartId')}/checkout"
            now = str(int(time.time()) + timeDelta)
            signature = hashlib.sha1()
            signature.update("+".join([config['application_secret'], config['consumer_key'],'POST', target, json.dumps(payload), now]).encode('utf-8'))
            headers['X-Ovh-Signature'] = "$1$" + signature.hexdigest()
            headers['X-Ovh-Timestamp'] = now
            try:
                response = requests.post(target, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    print(response.status_code)
                    print(json.dumps(response.json(), indent=4))
                    exit("Done")
                else:
                    print("Got non 200 response code on checkout, retrying")
                    print(json.dumps(response.json(), indent=4))
                    retry += 1
                    if retry > 15: exit()
                    if retry % 4 == 0 and config['anyDatacenter']:
                        print(f"Switching Region to {datacenterToRegion(availableDataCenter)} and datacenter to {availableDataCenter}")
                        planConfig['datacenter'] = availableDataCenter
                        planConfig['region'] = datacenterToRegion(availableDataCenter)
                        break
            except Exception as e:
                print(f"Unable to submit order got '{e}' as error")
                retry += 1
                if retry > 15: exit()
            time.sleep(2)
        else:
            time.sleep(1)