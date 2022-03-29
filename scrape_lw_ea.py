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
import os
import math

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

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
    # res = re.sub(r'http\S+', 'ʬ', res)
    return res

def combine_text(name, karma, text):
    # text = text.replace("&nbsp;", "")
    #Add an extra space at the end for when it's appended to the context
    return "username: {0} karma: {1} {2} ".format(name, karma, text)

def latest_url_file_name(url_dir = "urls_lesswrong"):
    url_filenames = sorted(os.listdir(url_dir), reverse=True) #Do reverse to get latest date first
    return url_filenames[0]

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
                # print("deleted comment at: ", url, " w/ subcomment", sub_comment_parent)
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
    # for a in soup.select('a'):
    #     a.insert(len(a), " ʬ")
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


def urls_to_json_scrape(file_prefix):
    if file_prefix == "effective_altruism_forum":
        url_link_prefix = "https://forum.effectivealtruism.org"
    else: #lesswrong
        url_link_prefix_public_facing = "https://www.lesswrong.com"
        url_link_prefix = "https://www.greaterwrong.com"
    today = datetime.today().strftime("%Y-%m-%d")
    json_post_and_comments = []

    url_filename_suffix = latest_url_file_name(f"urls_{file_prefix}")
    #Run files in unprocessed if they exist (may contain problem files)
    unprocessed_urls = os.listdir(f"unprocessed_urls_{file_prefix}")
    if unprocessed_urls: #if not empty
        url_filename_list = unprocessed_urls
    else: #Create files to process
        url_filename = f"urls_{file_prefix}/{url_filename_suffix}"
        with open(url_filename, "r") as file:
            #Split into separate files for every 1000 urls
            lines = file.read().splitlines()
            list_of_url_by_1000 = list(chunks(lines, 1000))
            for index, urls_1000 in enumerate(list_of_url_by_1000):
                with open(f"unprocessed_urls_{file_prefix}/{index}_{url_filename_suffix}", "w") as url_1000_file:
                    url_1000_file.writelines("\n".join(urls_1000))
        url_filename_list = os.listdir(f"unprocessed_urls_{file_prefix}")

    # url_date = "2022-02-16"
    # url_filename = "urls_"+file_prefix+"/"+url_date+"_links_"+file_prefix+".txt"
    current_post_iter = 0
    for url_filename in url_filename_list:
        with open(f"unprocessed_urls_{file_prefix}/{url_filename}", "r") as file:
            for url_link in file:
                #Show current iter post
                if (current_post_iter % 50 == 0):
                    print("current posts: ", current_post_iter)

                full_url_link = url_link_prefix + url_link.rstrip('\n')
                r = requests.get(full_url_link)
                time.sleep(1)

                html = r.content.decode('utf-8')
                soup = BeautifulSoup(cleanHtml(html), 'html.parser')
                #encode italics, bold, quotes, etc as text
                encode_html_as_text(soup)

                try: #Check if missing url
                    post_title = add_consistent_newlines(soup.select_one('.post-title').text.strip()[2:]) #Skip post_title Header_1
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
                    "title": post_title,
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
                            # print("deleted comment at: ", full_url_link, " w/ ", comment)
                            continue
                        try:
                            json_comment = recursive_comment(comment)
                            json_post_and_comments[current_post_iter]["comments"].append(json_comment)
                        except:
                            pass
                #Update current post iter since we've actually added 1 post to the json
                current_post_iter+=1
        #Dump each filename into processed folder
        with open(f"processed_urls_{file_prefix}/{url_filename}", "w") as f:
            json.dump(json_post_and_comments, f, indent=4)
        #remove url from unprocessed folder
        os.remove(f"unprocessed_urls_{file_prefix}/{url_filename}")
    return url_filename_suffix[:-4]

def combine_json_files(filename, file_prefix="lesswrong"):
    #Combine
    #Read in each filename
    processed_filenames = os.listdir(f"processed_urls_{file_prefix}") #Does listdir give relative address?
    for json_filename in processed_filenames:
        with open(f"processed_urls_{file_prefix}/{json_filename}", "r") as json_file:
            json_list = json.load(json_file)
    #Save it in scrapes
    json_filename = "scrapes/"+filename+".json"
    with open(json_filename, "w") as f:
        json.dump(json_list, f, indent=4)

if __name__ == "__main__":
    # Initialization and Configuration
    # file_prefix = "effective_altruism_forum" #
    file_prefix = "lesswrong"
    # latest_file_name = urls_to_json_scrape(file_prefix)
    latest_file_name = "2022-03-21_lesswrong_scrape"
    combine_json_files(latest_file_name, file_prefix)