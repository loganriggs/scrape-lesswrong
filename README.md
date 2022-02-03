# Scrape LessWrong & EA Forum

[Link for the latest scrapes](https://drive.google.com/drive/folders/1QotTTsCBDP2II6R2xV12rPNbhJk7b3yY?usp=sharing) in a .npy file. You can use numpy.load(filename) to read it in, though note that the lw_scrape is 3 GB and will take up that much RAM when loading in.

## get_latest_urls.py
Will grab the latest urls for both lw & ea (change the variable file_prefix)
```
file_prefix = ea #or lw
```
Also change the previous file url to the most up-to-date file. This is used to know when we've caught up urls
```
with open("urls/links_"+file_prefix+".txt") as previous_file:
```
(A better solution will grab the latest file automatically from the urls folder)
## scrape_lw_ea.py 
Scrapes the posts/comments from whatever url_file you want. Change 
```
with open("links_"+file_prefix+".txt", "r") as file:
```
(where a better solution will be a variable to put in the date of the latest file you want)

If you recieve an error of "Likely missing post at url: ..."  then you can click the url to see if it indeed available. ~1/100 were missing due to deleted posts or the code not accepting meetup posts. If much more than that amount appears, then the LW/EA team may have changed a class name and the code needs to be updated.
