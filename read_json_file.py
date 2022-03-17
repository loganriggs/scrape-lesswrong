import json
filename = "scrapes/2022-02-17_lesswrong_scrape.json"
with open(filename, "r") as f:
    scrape = json.load(f)
print(scrape[0]["content"])