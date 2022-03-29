from __future__ import print_function

import numpy as np
import json
import matplotlib.pyplot as plt
from dateutil import parser
from sys import getsizeof, stderr
from itertools import chain
from collections import deque
import ftfy
try:
    from reprlib import repr
except ImportError:
    pass

# filename = 'scrapes/test_6990_lesswrong_scrape.json'
filename = 'arxiv/arxiv_dict_updated.json'
with open(filename) as json_file:
    data = json.load(json_file)
    #print(data)

keys = [k for k,v in data.items()]
ten_values = [data[k] for k in keys[:10]]
one = ten_values[0]
print(ftfy.fix_text(one["abstract"]))

for k,v in data.items():
    data[k]["abstract"] = data[k]["abstract"].replace("\n", " ")

#Abstract needs a .replace("\n", " ")

def total_size(o, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                   }
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:       # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)

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


# i = 0
# for post in data:
#     i +=1
#     if (i>10):
#         break
#     format = conditional_format(post)
#     print("Next Post....")
#     for x in range(len(format)):
#         print("\n --- doc ", x, " ---")
#         print(format[x])

def get_url_of_dup(dup_string):
    return [[post["url"], post["date"] ]for post in data if dup_string.lower() in post["text"].lower() or dup_string.lower() in post["post_title"].lower()]

def get_id_from_data(id, data):
    return [post for post in data if post["id"] == id][0]

def convert_to_date(time_string):
    date = parser.parse(time_string)
    return date.weekday()*24 + date.hour

def plot_hourly(data, format = "top", n = 20):
    hours = np.arange(24*7)
    time_by_score = [[int(convert_to_date(post["date"])), float(post["score"].replace("−", "-"))] for post in data]
    hourly_time_score = [[] for _ in hours]
    for hour, score in time_by_score:
        hourly_time_score[hour].append(score)
    del time_by_score
    reduced_time =[np.concatenate((hourly_time_score[i*3], hourly_time_score[i*3+1],hourly_time_score[i*3+2])) for i in range(24*7//3)]
    hourly_time_score = reduced_time
    hours = np.arange(24*7//3)
    plt.clf()
    if format == "std":
        avg = np.array([np.average(row) for row in hourly_time_score])
        std_dev = np.array([np.std(row) for row in hourly_time_score])
        plt.fill_between(hours, avg-std_dev, avg+std_dev,
            alpha=0.5, edgecolor='#CC4F1B', facecolor='#FF9848')
    elif format == "top":
        hourly_time_score = [get_top_n_percent(n, row) for row in hourly_time_score]
        avg = np.array([np.average(row) for row in hourly_time_score])
        max = np.array([np.max(row) for row in hourly_time_score])
        min = np.array([np.min(row) for row in hourly_time_score])
        plt.fill_between(hours, min, max,
                         alpha=0.5, edgecolor='#CC4F1B', facecolor='#FF9848')
    plt.plot(hours, avg, 'k', color='#CC4F1B')
    plt.xticks(24/3*np.arange(7), ["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"])
    plt.title(f"Karma Over Time Top {n}%")
    plt.show()

def get_top_n_percent(n, array):
    five_percent = round(len(array) * 0.01*n)
    return sorted(array, reverse=True)[:five_percent]
