import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timezone
import statistics
import numpy as np

relicPageURL = "https://warframe.fandom.com/wiki/Void_Relic/ByRelic"
page = requests.get(relicPageURL)
soup = BeautifulSoup(page.content, "html.parser")
relicTable = soup.find("tbody").find_all("tr")
del relicTable[0]

# The list of all items that can be opened in all relics
listOfDrops = set()

# The list of relics and its drops
# attributes: "name" : string, "common-drops" : list, "uncommon-drops" : list, "rare-drops" : list
relicList = []

# List of errors
errors = []

# populate relicList and listOfDrops
for relic in list(relicTable):
    relicRow = relic.find_all("td")
    relicName = relicRow[0].get_text() + relicRow[1].find("a").get_text()
    relicName = relicName.replace("\n", " ")
    commonDrops = []
    uncommonDrops = []
    rareDrops = []
    for li in relicRow[2].ul.find_all("li"):
        commonDrops.append(li.a.string)
        listOfDrops.add(li.a.string)
    for li in relicRow[3].ul.find_all("li"):
        uncommonDrops.append(li.a.string)
        listOfDrops.add(li.a.string)
    for li in relicRow[4].ul.find_all("li"):
        rareDrops.append(li.a.string)
        listOfDrops.add(li.a.string)
    relicList.append({
        "name" : relicName,
        "common-drops" : commonDrops,
        "uncommon-drops" : uncommonDrops,
        "rare-drops" : rareDrops,
        "recent-prices" : []
    })



wfmAPI = "https://api.warframe.market/v1/items/"
wfmDateFormat = "%Y-%m-%dT%H:%M:%S.%f%z"
dateNow = datetime.now(tz=timezone.utc)

# changes a string into warframe market URL format ex: axi_s4
def formatName(name):
    if any(s in name for s in ("Neuroptics", "Systems", "Chassis")):
        name = name.replace(" Blueprint", "")
    return name.lower().replace(" ", "_")


offlineThreshhold = 24 * 3600
# determine if an items price should be added to recent prices based on offlineThresshold (hours x 3600 seconds)
def isRecentSellOrder(item):
    lastSeenDate = datetime.strptime(item["user"]["last_seen"], wfmDateFormat)
    if (dateNow - lastSeenDate).total_seconds() > offlineThreshhold: 
        return False
    else: return True

# returns a list of all recent order prices from warframe.market
def getSellOrderPrices(itemName, type="item"):
    orderPrices = {"online-prices":[], "offline-prices":[]}
    apiPath = wfmAPI + formatName(itemName)
    if type == "relic":
        apiPath += "_relic"
    apiPath += "/orders"
    response = requests.get(apiPath)
    if response.status_code != 200:
        errors.append(type + ": " + itemName + " not returned by warframe market.")
        return orderPrices
    orders = response.json()["payload"]["orders"]
    for order in orders:
        if order["order_type"] == "buy":
            continue
        if order["region"] != "en":
            continue
        if order["user"]["status"] == "ingame":
            orderPrices["online-prices"].append(order["platinum"])
            continue
        if isRecentSellOrder(order):
            orderPrices["offline-prices"].append(order["platinum"])
    return orderPrices


# returns a median based on the k lowest prices
def getPriceLow(prices):
    k = 5
    if len(prices) < 0: return 0
    prices.sort()
    print(prices[:k])
    return statistics.median(prices[:k])


# add all prices within the offlineThreshhol to relic recent-prices attribute
# for relic in relicList[slice(1)]:
#     relic["recent-prices"] = getSellOrderPrices(relic["name"], "relic")

for commonItem in relicList[0]["common-drops"]:
    print(commonItem + " prices: ")
    itemPrices = getSellOrderPrices(commonItem)
    if len(itemPrices["online-prices"]) > 0:
        print(getPriceLow(itemPrices["online-prices"]))
    if len(itemPrices["offline-prices"]) > 0:
        print(getPriceLow(itemPrices["offline-prices"]))



testLoops = 5
# for item in listOfDrops:

for error in errors:
    print(error)