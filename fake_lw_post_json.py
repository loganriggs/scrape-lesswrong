import json
json_post_and_comments = []

def new_post(id):
    return {
        "id": id,
        "post_title": "title-"+id,
        "author": "author-" + id,
        "date": "date-" + id,
        "score": "karma-" + id,
        "omega_karma": "omega_karma-" + id,
        "votes": "post_votes-" + id,
        "tags": "tags-"  + id,
        "url": "url-" + id,
        "text": "post_content-"+  id,
        "source": "source-" + id,  # "lesswrong" or "ea" atm
        "comments": []
    }

def new_comment(id):
    return {
        "id": id,
        "author": "author-" + id,
        "date": "date-" + id,
        "score": "karma-" + id,
        "omega_karma": "omega_karma-" + id,
        "votes": "post_votes-" + id,
        "url": "url-" + id,
        "text": "post_content-"+  id,
        "comments": []
    }

for x in ["1"]:
    json_post_and_comments.append(new_post(x))
for x in ["A", "B", "C"]:
    for post in json_post_and_comments:
        post["comments"].append(new_comment(x))
for x in ["i", "ii", "iii"]:
    for post in json_post_and_comments:
        for comment in post["comments"]:
            comment["comments"].append(new_comment(x))
json_post_and_comments.append(new_post("No_comment_post"))

with open("scrapes/fake_scrape.json", 'w') as f:
    json.dump(json_post_and_comments, f, indent=4)
