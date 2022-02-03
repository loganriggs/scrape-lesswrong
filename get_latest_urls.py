import time
import requests
from bs4 import BeautifulSoup
import re
# from datetime import datetime
import datetime
import dateutil.parser as dparser

def url_to_soup(url):
    r = requests.get(url)
    html = r.content.decode('utf-8')
    return BeautifulSoup(html, 'html.parser')

def add_20_to_url(url):
    current_post_amount = re.findall(r'\d+', url)[0]
    url = url.replace(current_post_amount, str(int(current_post_amount) + 20))
    return url

def subtract_one_day(date):
    new_date = dparser.parse(date) - datetime.timedelta(1)
    return new_date.strftime("%Y-%m-%d")

def subtract_days(url):
    #find the first date
    both_dates = re.findall(r'\d+-\d+-\d+', url)
    #subtract day
    first_date = both_dates[0]
    new_date = subtract_one_day(first_date)
    #first replace the oldest date w/ one day before
    url = url.replace(first_date, new_date)
    #Then 2nd w/ first (equivalent to one day before 2nd)
    url = url.replace(both_dates[1], both_dates[0])
    return url

def find_post_title_root(prefix):
    if prefix == "ea":
        return soup.findAll(class_='PostsTitle-root')
    else: #LW
        return soup.findAll(class_='post-title-link')

def get_href(linkParent, prefix):
    if prefix == "ea":
        return linkParent.a.get('href')
    else:  # LW
        return linkParent.get('href')


file_prefix = "ea"
# file_prefix = "lw"

today = datetime.datetime.today().strftime("%b_%d_%Y")
with open("urls/links_"+file_prefix+".txt") as previous_file:
    latest_url = previous_file.readline().rstrip()
f = open("urls/"+today + "_links_"+file_prefix+".txt", "w")

if file_prefix == "ea":
    today_year_month_day = datetime.datetime.today().strftime("%Y-%m-%d")
    initial_url = "https://forum.effectivealtruism.org/allPosts?after="+subtract_one_day(today_year_month_day)+"&before="+today_year_month_day+"&limit=100"
else: #LW
    initial_url = "https://www.greaterwrong.com/index?view=all&offset=0"
iterations = 0
found_latest_url = False
while not found_latest_url:
    iterations +=1
    if(iterations % 100 == 0):
        print("Currently: ", iterations)
    try:
        soup = url_to_soup(initial_url)
        posts = find_post_title_root(file_prefix)
        for linkParent in posts:
            link = get_href(linkParent, file_prefix)
            if link == latest_url:
                found_latest_url = True
                break
            f.write(link+"\n")
        if file_prefix == "ea":
            initial_url = subtract_days(initial_url)
        else: #LW
            initial_url = add_20_to_url(initial_url)
        time.sleep(1)
    except Exception as e:
        print(e)
        print("iterations: ", iterations)
        print("total files ~= ", iterations*20)
        break
f.close()