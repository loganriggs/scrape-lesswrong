# Scrape LessWrong & EA Forum

[Link for the latest scrapes](https://drive.google.com/drive/folders/1QotTTsCBDP2II6R2xV12rPNbhJk7b3yY?usp=sharing) in a .npy file. You can use numpy.load(filename) to read it in, though note that the lw_scrape is 3 GB and will take up that much RAM when loading in.

## get_latest_urls.py
Will grab the latest urls for both lw & ea (change the variable file_prefix to switch between the two as shown below)
```
file_prefix = "ea" #or "lw"
```
## scrape_lw_ea.py 
Scrapes the posts/comments from whatever url_file you want. Again change the file_prefix variable to switch between lesswrong and ea forum. 

If you recieve an error of "Likely missing post at url: ..."  then you can click the url to see if it indeed available. ~1/100 were missing due to deleted posts or the code not accepting meetup posts. If much more than that amount appears, then the LW/EA team may have changed a class name and the code needs to be updated.
