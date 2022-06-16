import requests

endpoint = "ca.api.ovh.com"
response = requests.get(f'https://{endpoint}/1.0/order/catalog/public/eco?ovhSubsidiary=WE')
catalog = response.json()
catalogSorted = {}
for plan in catalog['plans']:
    for price in plan['pricings']:
        if "installation" in price['capacities']: continue
        if price['interval'] != 1: continue
        catalogSorted[price['price']] = plan

newlist = dict(sorted(catalogSorted.items(), key=lambda item: item[0]))

#print(catalogSorted)
for price,offer in newlist.items():
    if "product" in offer:
        print(price,offer["invoiceName"])
        for addon in offer['addonFamilies']:
            if addon['mandatory'] != True: continue
            print(addon)
