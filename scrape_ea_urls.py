import datetime
import time
import requests
from bs4 import BeautifulSoup
import re
import dateutil.parser as dparser

def url_to_soup(url):
    r = requests.get(url)
    html = r.content.decode('utf-8')
    return BeautifulSoup(html, 'html.parser')

def subtract_day(date):
    new_date = dparser.parse(date) - datetime.timedelta(1)
    return new_date.strftime("%Y-%m-%d")

def subtract_days(url):
    #find the first date
    both_dates = re.findall(r'\d+-\d+-\d+', url)
    #subtract day
    first_date = both_dates[0]
    new_date = subtract_day(first_date)
    #first replace the oldest date w/ one day before
    url = url.replace(first_date, new_date)
    #Then 2nd w/ first (equivalent to one day before 2nd)
    url = url.replace(both_dates[1], both_dates[0])
    return url

f = open("urls/links_ea.txt", "w")
url = "https://forum.effectivealtruism.org/allPosts?after=2022-01-08&before=2022-01-09&limit=100"
iterations = 0
while True:
    iterations +=1
    if(iterations % 100 == 0):
        print("Currently: ", iterations)
    try:
        soup = url_to_soup(url)
        posts = soup.findAll(class_='PostsTitle-root')
        for linkParent in posts:
            link = linkParent.a.get('href')
            f.write(link+"\n")
        url = subtract_days(url)
        time.sleep(1)
    except Exception as e:
        print(e)
        print("iterations: ", iterations)
        print("total files ~= ", iterations*20)
        break
f.close()

