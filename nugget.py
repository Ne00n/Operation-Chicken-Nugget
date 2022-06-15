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

endpoint,headers = "https://ca.api.ovh.com/",{'Content-Type': 'application/json'}
# creating a new cart
cart = client.post("/order/cart", ovhSubsidiary="CA", _need_auth=False)
print(cart.get("cartId"))
#assign new cart to current user
client.post("/order/cart/{0}/assign".format(cart.get("cartId")))
#put ks1 into cart
#result = client.post(f'/order/cart/{cart.get("cartId")}/eco',{"duration":"P1M","planCode":"22sk010","pricingMode":"default","quantity":1})
#apparently this shit sends malformed json whatever baguette
payload={'duration':'P1M','planCode':'22sk010','pricingMode':'default','quantity':1}
response = requests.post(f'{endpoint}1.0/order/cart/{cart.get("cartId")}/eco', headers=headers, data=json.dumps(payload))
print(response.status_code)
print(json.dumps(response.json(), indent=4))
#getting current cart
response = requests.get(f'{endpoint}1.0/order/cart/{cart.get("cartId")}')
print(response.status_code)
print(json.dumps(response.json(), indent=4))
#modify item for checkout
itemID = response.json()['items'][0]
print(itemID)
#set region
payload={'label':'region','value':'europe'}
response = requests.post(f'{endpoint}1.0/order/cart/{cart.get("cartId")}/item/{itemID}/configuration', headers=headers, data=json.dumps(payload))
print(response.status_code)
print(json.dumps(response.json(), indent=4))
#set datacenter
payload={'label':'dedicated_datacenter','value':'fr'}
response = requests.post(f'{endpoint}1.0/order/cart/{cart.get("cartId")}/item/{itemID}/configuration', headers=headers, data=json.dumps(payload))
print(response.status_code)
print(json.dumps(response.json(), indent=4))
#set os
payload={'label':'dedicated_os','value':'none_64.en'}
response = requests.post(f'{endpoint}1.0/order/cart/{cart.get("cartId")}/item/{itemID}/configuration', headers=headers, data=json.dumps(payload))
print(response.status_code)
print(json.dumps(response.json(), indent=4))