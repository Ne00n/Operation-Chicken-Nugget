import requests, json, ovh

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
#set region
payload={'label':'region','value':'europe'}
response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/item/{itemID}/configuration', headers=headers, data=json.dumps(payload))
if response.status_code == 200:
    print("Set Region")
else:
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    exit()
#set datacenter
payload={'label':'dedicated_datacenter','value':'fr'}
response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/item/{itemID}/configuration', headers=headers, data=json.dumps(payload))
if response.status_code == 200:
    print("Set Datacenter")
else:
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    exit()
#set os
payload={'label':'dedicated_os','value':'none_64.en'}
response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/item/{itemID}/configuration', headers=headers, data=json.dumps(payload))
if response.status_code == 200:
    print("Set OS")
else:
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    exit()
#set bandwidth
payload={'itemId':itemID,'duration':'P1M','planCode':'bandwidth-100-included-ks','pricingMode':'default','quantity':1}
response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/eco/options', headers=headers, data=json.dumps(payload))
if response.status_code == 200:
    print("Set Bandwidth")
else:
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    exit()
#set disk
payload={'itemId':itemID,'duration':'P1M','planCode':'noraid-1x1000sa-sk010','pricingMode':'default','quantity':1}
response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/eco/options', headers=headers, data=json.dumps(payload))
if response.status_code == 200:
    print("Set Disk")
else:
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    exit()
#set memory
payload={'itemId':itemID,'duration':'P1M','planCode':'ram-4g-sk010','pricingMode':'default','quantity':1}
response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/eco/options', headers=headers, data=json.dumps(payload))
if response.status_code == 200:
    print("Set Memory")
else:
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    exit()
print("Package ready, waiting for stock")
#wait for stock
#todo
#lets checkout boooyaaa
payload={'autoPayWithPreferredPaymentMethod':False,'waiveRetractationPeriod':False}
print(json.dumps(headers, indent=4))
response = requests.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/checkout', headers=headers, data=json.dumps(payload))
print(response.status_code)
print(json.dumps(response.json(), indent=4))


client.post(f'https://{endpoint}/1.0/order/cart/{cart.get("cartId")}/checkout', **payload, ovhSubsidiary="CA", _need_auth=True)