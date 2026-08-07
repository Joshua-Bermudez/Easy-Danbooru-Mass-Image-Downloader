# Easy-Danbooru-Mass-Image-Downloader

Need to download lots of images in danbooru with specific tags? this script will help you automate that process just by doing simple things!






# HOW TO RUN
just bash this to your folder's terminal: 

python danbooru_downloader.py


# TO CHANGE THE FILE FORMAT:

replace the ALLOWED_EXTENSIONS in line 21, ex: from {"mp4","gif"} you can turn it to {"jpg,"png"}

# TO CHANGE THE TAGS

replace the --tags in 122 to the danbooru tags you're looking for
for example: default=["genshin_impact", "absurdres"] you can turn it to default=["apex_legends", "animification"]

# CHANGE DOWNLOAD LIMIT

replace the default=25 in line 125 to how many you want to download

# CHANGE CONTENT RATING

replace the default="general" to the choices you have in line 127. 
for example: from  default="general" to  default="sensitive"

# COMING SOON!
UI for each contents for easier use
