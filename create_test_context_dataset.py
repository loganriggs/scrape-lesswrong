import numpy as np
import json
import matplotlib.pyplot as plt
from dateutil import parser

with open('scrapes/test_6990_lesswrong_scrape.json') as json_file:
    data = json.load(json_file)
    data = data[0:2200]
    #print(data)

def recursive_comment_incrementer(comment, number_of_comments):
    for comment in comment['comments']:
        number_of_comments +=1
        number_of_comments = recursive_comment_incrementer(comment, number_of_comments)
    return number_of_comments

def get_number_of_comments(post):
    number_of_comments = 0
    number_of_comments = recursive_comment_incrementer(post, number_of_comments)
    return number_of_comments

def formatted_text(post, format="post"):
    if format == "post":
        return "{} {} {} {}".format(post["title"], post["author"], post["score"], post["text"])
    elif format == "comment":
        return "{} {} {}".format(post["author"], post["score"], post["text"])


def conditional_format_recursion(comment, training_list, current_train_text):
    if comment["comments"]:
        for sub_comment in comment["comments"]:
            comment_text = formatted_text(sub_comment, format="comment")
            training_list = conditional_format_recursion(sub_comment, training_list, current_train_text + [comment_text])
            #Remove all instances of <endcontext> token, then add new one
            if "<|endofcontext|>" in current_train_text:
                current_train_text.remove("<|endofcontext|>")
            current_train_text.append("<|endofcontext|>")
    else: #Leaf node, return what you got
        if current_train_text[-1] == "<|endofcontext|>":
            current_train_text.pop()
        training_list.append("\n".join(current_train_text))
    return training_list

def conditional_format(post):
    post_text = formatted_text(post, format="post")
    if post["comments"]:
        return conditional_format_recursion(post, [], [post_text])
    else: #No comments, return what you got
        return [post_text]

def combine_all_comments(data):
    for x in range (1,len(data)):
        data[0]["comments"] = data[0]["comments"] + data[x]["comments"]
    return data


data = combine_all_comments(data)
json_text = {"data": [text_block for text_block in conditional_format(data[0])]}
with open("scrapes/context_test.json", 'w') as f:
    json.dump(json_text, f, indent=4)
# i = 0
# for post in data:
#     i +=1
#     if (i>10):
#         break
#     format = conditional_format(post)
#     # print("Next Post....")
#     for x in range(len(format)):
#         # print("\n --- doc ", x, " ---")
#         print(format[x])
