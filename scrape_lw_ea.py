import random
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import time
from datetime import datetime

def combine_text(name, karma, text):
    # text = text.replace("&nbsp;", "")
    #Add an extra space at the end for when it's appended to the context
    return "username: {0} karma: {1} {2} ".format(name, karma, text)

def recursive_comment(comment, context, comment_context_array):
    parent_comment = comment.contents[0]
    try:
        username = parent_comment.select_one('.UsersNameDisplay-userName').text.strip()
        karma = parent_comment.select_one('.OverallVoteAxis-voteScore').text.strip()
        text = clean_paragraph_of_newlines(parent_comment.select_one('.CommentBody-commentStyling'))
    except AttributeError: #Deleted Comment, just jump out of function
        return comment_context_array

    full_comment = combine_text(username, karma, text)
    comment_context_array = np.append(comment_context_array, [[context, full_comment]], 0)

    # recursively apply to subcomments
    #contents[0] is original comment
    #contents[1] is list of all sub-comments, plus a parentscroll at 0-index, so skip that.
    try:
        for sub_comment_parent in comment.contents[1].contents[1:]:
            #find new comment
            # new_comment = sub_comment_parent.select('div[class*="comments-node"]')
            new_comment = sub_comment_parent.contents[0]
            comment_context_array = recursive_comment(new_comment, context + full_comment, comment_context_array)
    except: #then it's a leaf-comment, keep moving
        pass
    return comment_context_array

def clean_paragraph_of_newlines(paragraph):
    #Get rid of excess newlines, but must first encode actual newlines (double \n), bulleted lists, and blockquotes
    paragraph = paragraph.text.replace("\n\n", "&newline")
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
file_prefix = "ea"
# file_prefix = "lw"

if file_prefix == "ea":
    url_link_prefix = "https://forum.effectivealtruism.org"
else: #lesswrong
    url_link_prefix = "https://www.lesswrong.com"
today = datetime.today().strftime("%b_%d_%Y")
comment_context_array = np.empty(shape=(0,2), dtype=object)

with open("links_"+file_prefix+".txt", "r") as file:
    count = 0
    for url_link in file:
        try:
            time.sleep(1)
            count+=1
            if (count % 100 == 0):
                print("url = ", count)
            url_link = url_link_prefix + url_link.rstrip('\n')
            r = requests.get(url_link)
            html = r.content.decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            #encode italics, bold, quotes, etc as text
            encode_html_as_text(soup)

            #Grab post data
            name = soup.select_one('.UsersNameDisplay-userName').text.strip()
            karma = soup.findAll(class_='Typography-root Typography-headline PostsVote-voteScore')[0].text.strip()
            post_content_list = [clean_paragraph_of_newlines(paragraph) for paragraph in soup.select_one('.PostsPage-postContent')]
            post_content = ''.join(post_content_list)
            post = combine_text(name, karma, post_content)

            #Numpy object to save text in format [context,post/comment]
            context = ""
            comment_context_array = np.append(comment_context_array, [[context, post]], 0)
            context += post

            #Grab comments recursively
            comments = soup.select('div[class*="comments-node CommentFrame-commentsNodeRoot comments-node-root"]')
            for comment in comments:
                comment_context_array = recursive_comment(comment, context, comment_context_array)
        except:
            print("Likely missing post at url: ", url_link)

np.save("scrapes/"+today + "_"+file_prefix+"_scrape", comment_context_array)