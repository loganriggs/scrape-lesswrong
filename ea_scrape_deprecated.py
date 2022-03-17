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
    parent_comment = comment.contents[0]
    try:
        # Selenium find tooltip
        url = parent_comment.select_one('.CommentsItemDate-root.CommentsItemDate-date').a.get("href")
        # data = driver.find_element_by_xpath('//a[@href="'+url+'"]/span')
        # hov = ActionChains(driver).move_to_element(data)
        # hov.perform()
        # data_in_the_bubble = driver.find_element_by_xpath("//*[@class='LWTooltip-tooltip']")
        # date = data_in_the_bubble.get_attribute("innerHTML")

        commentID_location = url.find("?commentId=") + len("?commentId=")
        id = url[commentID_location:]
        username = parent_comment.select_one('.UsersNameDisplay-userName').text.strip()
        karma = parent_comment.select_one('.OverallVoteAxis-voteScore').text.strip()
        text = clean_paragraph_of_newlines(parent_comment.select_one('.CommentBody-commentStyling').text.strip())
    except AttributeError: #Deleted Comment, just return None
        return None

    json_comment = {
        "id": id,
        "author": username,
        "score": karma,
        "url": url,
        # "date": date,
        "content": text,
        "sub_comments": []
    }

    # recursively apply to subcomments
    #contents[0] is original comment
    #contents[1] is list of all sub-comments, plus a parentscroll at 0-index, so skip that.
    try:
        for sub_comment_parent in comment.contents[1].contents[1:]:
            #find new comment
            new_comment = sub_comment_parent.contents[0]
            json_subcomment = recursive_comment(new_comment)
            if json_subcomment: #Not None
                json_comment["sub_comments"].append(json_subcomment)
    except: #then it's a leaf-comment, keep moving
        pass
    return json_comment

def clean_paragraph_of_newlines(paragraph):
    #Get rid of excess newlines, but must first encode actual newlines (double \n), bulleted lists, and blockquotes
    paragraph = paragraph.replace("\n\n", "&newline")
    paragraph = paragraph.replace("\n -", "&bull")
    paragraph = paragraph.replace("\n", " ")
    paragraph = paragraph.replace("&bull","\n -")
    paragraph = paragraph.replace("&newline", "\n")
    paragraph = paragraph.replace("&endblockquote", " \n")
    return paragraph

def encode_html_as_text(soup):
    #Convert different tags into text we would want GPT to learn
    for li in soup.select("li"):
        li.insert(0, " \n - ")
    for blockquote in soup.select("blockquote"):
        blockquote.insert(len(blockquote), "&endblockquote ")
        blockquote.insert(0, '> ')
    for italics in soup.select("em"):
        italics.insert(len(italics), "_")
        italics.insert(0, "_")
    for italics in soup.select("i"):
        italics.insert(len(italics), "_")
        italics.insert(0, "_")
    for paragraphs in soup.select("p"):
        paragraphs.insert(len(paragraphs), "\n\n")
    for ordered_list in soup.select("ol"):
        ordered_list.insert(len(ordered_list), "\n\n")
    for headings in soup.select("h1"):
        headings.insert(len(headings), " ")
        headings.insert(0, " ")
    for headings in soup.select("h2"):
        headings.insert(len(headings), " ")
        headings.insert(0, " ")
    for headings in soup.select("h3"):
        headings.insert(len(headings), " ")
        headings.insert(0, " ")
    for bold in soup.select("b"):
        bold.insert(len(bold), "__")
        bold.insert(0, "__")
    for bold in soup.select("strong"):
        bold.insert(len(bold), "__")
        bold.insert(0, "__")
    return #insert is in-place, no need to return soup

#Initialization and Configuration
# file_prefix = "effective_altruism_forum" #
file_prefix = "lesswrong"

if file_prefix == "effective_altruism_forum":
    url_link_prefix = "https://forum.effectivealtruism.org"
else: #lesswrong
    url_link_prefix = "https://www.lesswrong.com"
today = datetime.today().strftime("%Y-%m-%d")
json_post_and_comments = []
# driver = webdriver.Firefox()
url_date = "2022-02-03"
url_filename = "urls_"+file_prefix+"/"+url_date+"_links_"+file_prefix+".txt"
with open(url_filename, "r") as file:
    current_post_iter = 0
    for url_link in file:
        try:
            url_link = url_link_prefix + url_link.rstrip('\n')
            # driver.get(url_link)
            r = requests.get(url_link)
            time.sleep(1)
            if ((current_post_iter+1) % 10 == 0):
                print("url = ", current_post_iter)
                break
            html = r.content.decode('utf-8')
            soup = BeautifulSoup(cleanHtml(html), 'html.parser')
            #encode italics, bold, quotes, etc as text
            encode_html_as_text(soup)

            #Grab post data
            post_title = soup.select_one('.PostsPageTitle-link').text.strip()
            date = soup.select_one('.PostsPageDate-date').text.strip()
            author = soup.select_one('.UsersNameDisplay-userName').text.strip()
            karma = soup.findAll(class_='Typography-root Typography-headline PostsVote-voteScore')[0].text.strip()
            post_content_list = [clean_paragraph_of_newlines(paragraph.text.strip()) for paragraph in soup.select_one('.PostsPage-postContent')]
            post_content = ''.join(post_content_list)

            #json object to save text in format
            json_post_and_comments.append({
                "id": url_link.split('/')[4],
                "post_title": post_title,
                "author": author,
                "date": date,
                "score": karma,
                "url": url_link,
                "content": post_content,
                "source": file_prefix, # "lesswrong" or "ea" atm
                "comments": []
            })

            #check for alignment forum
            AF_preface = "Crossposted from the AI Alignment Forum. May contain more technical jargon than usual."
            if AF_preface in post_content:
                json_post_and_comments[current_post_iter]["source"] = "alignment forum"
                json_post_and_comments[current_post_iter]["content"].replace(AF_preface, "")

            #Grab comments recursively
            comments = soup.select('div[class*="comments-node CommentFrame-commentsNodeRoot comments-node-root"]')
            for comment in comments:
                json_comment = recursive_comment(comment)
                if json_comment: #not None
                    json_post_and_comments[current_post_iter]["comments"].append(json_comment)
            current_post_iter+=1
        except:
            print("Likely missing post at url: ", url_link)

with open("scrapes/"+today + "_"+file_prefix+"_scrape.json", 'w') as f:
    json.dump(json_post_and_comments, f, indent=4)