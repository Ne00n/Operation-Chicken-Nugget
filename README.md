# Operation-Chicken-Nugget

Goal of this Operation is, grabbing a KS1 in Roubaix.<br />
**Don't run this on a VPS, you will get flagged for Fraud**

**Dependencies**<br />

```
pip3 install requests ovh
```

1. Create an Application<br />
https://ca.api.ovh.com/createApp/<br />
https://eu.api.ovh.com/createApp/<br />

2. Put the keys into config.json<br />
Example how config.json should look like by now <br />

```
{
    "endpoint":"ovh-ca",
    "endpointAPI":"ca.api.ovh.com",
    "ovhSubsidiary":"CA",
    "application_key":"xxxxxxxxxx",
    "application_secret":"xxxxxxxxxxxxxxxxxx",
    "dedicated_datacenter":"fr",
    "region":"europe",
    "consumer_key":""
}
```

2. Request the consumerKey with running consumerKey.py and put it into config.json <br />

3. Edit nugget.py if you want to, by default it does no autopay and only in RBX<br />
If you want GRA, uncomment a few lines.<br />

4. Profit! <br />
