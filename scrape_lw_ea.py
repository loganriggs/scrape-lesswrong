import random
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import time
from datetime import datetime
import json
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains


def get_tag_list(soup, separator="/"):
    tags_html = soup.find("div", {"id": "tags"})
    tag_list = []
    if tags_html:
        for tag in tags_html:
            tag_list.append(tag.text)
        return separator.join(tag_list)
    else:
        return ""

def cleanHtml(html):
    res = html
    res = re.sub("\u201c", '"', res)
    res = re.sub("\u201d", '"', res)
    return res

def combine_text(name, karma, text):
    # text = text.replace("&nbsp;", "")
    #Add an extra space at the end for when it's appended to the context
    return "username: {0} karma: {1} {2} ".format(name, karma, text)

def recursive_comment(comment):
    url = comment.select_one('.lw2-link').get("href")
    commentID_location = url.find("?commentId=") + len("?commentId=")
    id = url[commentID_location:]
    date = comment.select_one(".date").text.strip()
    date = datetime.strptime(date, '%d %b %Y %H:%M %Z').isoformat()[0:-3]
    username = comment.select_one('.author').text.strip()
    karma_temp = comment.select_one('.karma-value')
    karma_list = karma_temp.text.strip().split(" ")
    karma = karma_list[0]
    votes = karma_temp.get("title").split(" ")[0]
    text = add_consistent_newlines(comment.select_one('.body-text.comment-body').text.strip())

    json_comment = {
        "id": id,
        "author": username,
        "score": karma,
        "omega_karma": "",
        "votes": votes,
        "url": url,
        "date": date,
        "text": text,
        "comments": []
    }

    if len(karma_list) > 2:  # eg. LW: 420 AF: 69, list split by spaces
        json_comment["score"] = karma_list[1]
        json_comment["omega_karma"] = karma_list[3]

    # recursively apply to subcomments
    next_comment = comment.select_one(".comment-thread")
    if(next_comment):
        for sub_comment_parent in next_comment:
            if (len(sub_comment_parent.div.get("class")) > 1):
                print("deleted comment at: ", url, " w/ subcomment", sub_comment_parent)
                continue
            try:
                json_subcomment = recursive_comment(sub_comment_parent)
                json_comment["sub_comments"].append(json_subcomment)
            except:
                pass
    return json_comment

def add_consistent_newlines(paragraph):
    #Add in Consistent Newlines
    paragraph = paragraph.replace("&newline", "\n")
    return paragraph

def encode_html_as_text(soup):
    #Convert different tags into text we would want GPT to learn
    for li in soup.select("li"):
        li.insert(0, "&newline - ")
    for blockquote in soup.select("blockquote"):
        for child in blockquote.children:
            c = child
            if c.name != None:
                break
        try:
            c.insert(0, "> ")
        except: #Has no nested children tags, just insert first
            blockquote.insert(0, "> ")
    for italics in soup.select("em"):
        italics.insert(len(italics), "*")
        italics.insert(0, "*")
    for italics in soup.select("i"):
        italics.insert(len(italics), "*")
        italics.insert(0, "*")
    for paragraphs in soup.select("p"):
        paragraphs.insert(len(paragraphs), "&newline")
    for headings in soup.select("h1"):
        headings.insert(len(headings), "&newline")
        headings.insert(0, "# ")
    for headings in soup.select("h2"):
        headings.insert(len(headings), "&newline")
        headings.insert(0, "## ")
    for headings in soup.select("h3"):
        headings.insert(len(headings), "&newline")
        headings.insert(0, "### ")
    for nav in soup.select("nav"):
        nav.insert(len(nav), "&newline")
    for bold in soup.select("b"):
        bold.insert(len(bold), "**")
        bold.insert(0, "**")
    for bold in soup.select("strong"):
        bold.insert(len(bold), "**")
        bold.insert(0, "**")
    return #insert is in-place, no need to return soup

#Initialization and Configuration
# file_prefix = "effective_altruism_forum" #
file_prefix = "lesswrong"

if file_prefix == "effective_altruism_forum":
    url_link_prefix = "https://forum.effectivealtruism.org"
else: #lesswrong
    url_link_prefix_public_facing = "https://www.lesswrong.com"
    url_link_prefix = "https://www.greaterwrong.com"
today = datetime.today().strftime("%Y-%m-%d")
json_post_and_comments = []
url_date = "2022-02-16"
url_filename = "urls_"+file_prefix+"/"+url_date+"_links_"+file_prefix+".txt"
with open(url_filename, "r") as file:
    current_post_iter = 0
    for url_link in file:
        full_url_link = url_link_prefix + url_link.rstrip('\n')
        r = requests.get(full_url_link)
        time.sleep(1)
        if ((current_post_iter+1) % 51 == 0):
            print("current iter ", current_post_iter)
        html = r.content.decode('utf-8')
        soup = BeautifulSoup(cleanHtml(html), 'html.parser')
        #encode italics, bold, quotes, etc as text
        encode_html_as_text(soup)

        try: #Check if missing url
            post_title = soup.select_one('.post-title').text.strip()
            date = soup.select_one('.date').text.strip()
            date = datetime.strptime(date, '%d %b %Y %H:%M %Z').isoformat()[0:-3]
            author = soup.select_one('.author').text.strip()
            karma_temp = soup.select_one('.karma-value')
            post_votes = karma_temp.get("title").split(" ")[0]
            karma_list = karma_temp.text.split(" ")
            karma = karma_list[0]
            post_content = add_consistent_newlines(soup.select_one('.body-text.post-body').text.strip())
            tags = get_tag_list(soup, "/")
        except: #Event or missing url
            print("Missing url at: ", full_url_link)
            continue

        #json object to save text in format
        json_post_and_comments.append({
            "id": full_url_link.split('/')[4],
            "post_title": post_title,
            "author": author,
            "date": date,
            "score": karma,
            "omega_karma": "",
            "votes": post_votes,
            "tags": tags,
            "url": url_link_prefix_public_facing + url_link.rstrip('\n'),
            "text": post_content,
            "source": file_prefix, # "lesswrong" or "ea" atm
            "comments": []
        })

        #check for alignment forum
        if len(karma_list) > 2: # eg. LW: 420 AF: 69, list split by spaces
            json_post_and_comments[current_post_iter]["source"] = "alignment forum"
            json_post_and_comments[current_post_iter]["score"] = karma_list[1]
            json_post_and_comments[current_post_iter]["omega_karma"] = karma_list[3]
        #Grab comments recursively
        comments = soup.select_one('.comment-thread')
        if comments:
            for comment in comments:
                if (len(comment.div.get("class"))>1):
                    print("deleted comment at: ", full_url_link, " w/ ", comment)
                    continue
                try:
                    json_comment = recursive_comment(comment)
                    json_post_and_comments[current_post_iter]["comments"].append(json_comment)
                except:
                    pass
        current_post_iter+=1

with open("scrapes/"+today + "_"+file_prefix+"_scrape.json", 'w') as f:
    json.dump(json_post_and_comments, f, indent=4)