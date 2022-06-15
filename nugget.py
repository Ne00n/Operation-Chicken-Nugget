import requests, hashlib, json, time, ovh
from random import randint

with open('config.json') as f:
    config = json.load(f)

# Instantiate. Visit https://api.ovh.com/createToken/?GET=/me
# to get your credentials
client = ovh.Client(
    endpoint=config['endpoint'],
    application_key=config['application_key'],
    application_secret=config['application_secret'],
    consumer_key=config['consumer_key'],
)

# Print nice welcome message
print("Welcome", client.get('/me')['firstname'])

endpoint = "ca.api.ovh.com"
headers = {'Accept': 'application/json','X-Ovh-Application':config['application_key'],'X-Ovh-Consumer':config['consumer_key'],
'Content-Type':'application/json;charset=utf-8','Host':endpoint}
print("Preparing Package")
#getting current time
response = requests.get(f'https://{endpoint}/1.0/auth/time', headers=headers)
if response.status_code == 200:
    print("Getting Time")
else:
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    exit()
timeDelta = int(response.text) - int(time.time())
#run for 8 days
for day in range(4):
    print(f'Day {day}')
    # creating a new cart
    cart = client.post("/order/cart", ovhSubsidiary="CA", _need_auth=False)
    #assign new cart to current user
    client.post("/order/cart/{0}/assign".format(cart.get("cartId")))
    #put ks1 into cart
    #result = client.post(f'/order/cart/{cart.get("cartId")}/eco',{"duration":"P1M","planCode":"22sk010","pricingMode":"default","quantity":1})
    #apparently this shit sends malformed json whatever baguette
    payload={'duration':'P1M','planCode':'22sk010','pricingMode':'default','quantity':1}
    response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/eco', headers=headers, data=json.dumps(payload))
    #getting current cart
    response = requests.get(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}')
    if response.status_code != 200:
        print(response.status_code)
        print(json.dumps(response.json(), indent=4))
        exit()
    #modify item for checkout
    itemID = response.json()['items'][0]
    print(f'Getting current cart {cart.get("cartId")}')
    #set configurations
    configurations = [{'label':'region','value':'europe'},{'label':'dedicated_datacenter','value':'fr'},{'label':'dedicated_os','value':'none_64.en'}]
    for entry in configurations:
        response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/item/{itemID}/configuration', headers=headers, data=json.dumps(entry))
        if response.status_code == 200:
            print(f"Setting {entry}")
        else:
            print(response.status_code)
            print(json.dumps(response.json(), indent=4))
            exit()
    #set options
    options = [{'itemId':itemID,'duration':'P1M','planCode':'bandwidth-100-included-ks','pricingMode':'default','quantity':1},
            {'itemId':itemID,'duration':'P1M','planCode':'noraid-1x1000sa-sk010','pricingMode':'default','quantity':1},
            {'itemId':itemID,'duration':'P1M','planCode':'ram-4g-sk010','pricingMode':'default','quantity':1}
    ]
    for option in options:
        response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/eco/options', headers=headers, data=json.dumps(option))
        if response.status_code == 200:
            print(f"Setting {option}")
        else:
            print(response.status_code)
            print(json.dumps(response.json(), indent=4))
            exit()
    print("Package ready, waiting for stock")
    #the order expires in about 3 days, we create a new one after 2 days
    for check in range(17280):
        print(f"Run {check+1}")
        #wait for stock
        response = requests.get('https://us.ovh.com/engine/apiv6/dedicated/server/datacenter/availabilities?excludeDatacenters=false&planCode=22sk010&server=22sk010')
        if response.status_code == 200:
            stock = response.json()
            score = 0
            for datacenter in stock[0]['datacenters']:
                if datacenter['datacenter'] == "rbx":
                    print(f'RBX {datacenter["availability"]}')
                    if datacenter['availability'] != "unavailable": score+1
                if datacenter['datacenter'] == "gra":
                    print(f'GRA {datacenter["availability"]}')
                    if datacenter['availability'] == "unavailable": score+1
        else:
            time.sleep(randint(5,10))
            continue
        #lets checkout boooyaaa
        if score == 2:
            #autopay should be set to true if you want automatic delivery, otherwise it will just generate a invoice
            #best guess, load your ovh account, don't use CC, will add delay
            payload={'autoPayWithPreferredPaymentMethod':False,'waiveRetractationPeriod':False}
            #prepare sig
            target = f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/checkout'
            now = str(int(time.time()) + timeDelta)
            signature = hashlib.sha1()
            signature.update("+".join([config['application_secret'], config['consumer_key'],'POST', target, json.dumps(payload), now]).encode('utf-8'))
            headers['X-Ovh-Signature'] = "$1$" + signature.hexdigest()
            headers['X-Ovh-Timestamp'] = now
            response = requests.post(target, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                print(response.status_code)
                print(json.dumps(response.json(), indent=4))
                exit("Done")
            else:
                print("Got non 200 response code on checkout, retrying")
                continue
        time.sleep(10)