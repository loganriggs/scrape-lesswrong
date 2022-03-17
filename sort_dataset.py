import numpy as np
import json
import matplotlib.pyplot as plt

with open('scrapes/2022-02-17_lesswrong_scrape.json') as json_file:
    data = json.load(json_file)
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
        return "{} {} {} {}".format(post["post_title"], post["author"], post["score"], post["text"])
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


# for post in data:
#     format = conditional_format(post)
#     print("Next Post....")
#     for x in range(len(format)):
#         print("\n --- doc ", x, " ---")
#         print(format[x])



# cross_posts = [post for post in data if ("crossposted" in post["text"].lower() or "linkpost" in post["text"].lower() or "crosspost" in post["post_title"].lower() or "linkpost" in post["post_title"].lower())]
# authors = [cp["author"] for cp in cross_posts]
# uniq, counts = np.unique(authors, return_counts=True)

def get_url_of_dup(dup_string):
    print("=================================================================")
    print(dup_string)
    return [[post["url"], post["date"] ]for post in data if dup_string.lower() in post["text"].lower() or dup_string.lower() in post["post_title"].lower()]

def get_id_from_data(id, data):
    return [post for post in data if post["id"] == id][0]

st_post = get_id_from_data("CeZXDmp8Z363XaM6b", data)