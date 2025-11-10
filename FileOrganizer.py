import os
import shutil
import re

os.chdir(r"C:\Users\Sarita Kumari\Downloads")
#Include the path of destination folder that needs to be organised

#Check current path using the given command
# os.getcwd()
#checking existing directories using the given command
# os.listdir()

extensions={
    "audio":[".aif",".cdf",".mid",".midi",".mp3",".mpa",".ogg",".wav",".wma",".wpl"],
    
    "images":[".jpeg",".jpg",".jpe",".jif",".jfif",".jfi",".png",".webp",".ico",".tiff",".tif",".gif",
              ".psd",".raw",".arw",".cr2",".nrw",".k25",".bmp",".dib",".ind",".indd",".indt",".heif",
              ".heic",".jp2",".j2k",".jpx",".jpm",".mj2",".svg",".svgz",".ai",".eps"],
       
    "text":[".doc",".docx",".odt",".pdf",".rtf",".tex",".txt",".wpd"],
    
    "video":[".mp4",".3g2",".3gp",".flv",".h264",".m4v",".mkv",".mov",".mp4",".mpg",".mpeg",".rm",".swf",".vob",".wmv"],
    
    "presentation":[".ppt",".pptx",".key",".pps",".odp"],
    
    "spreadsheet":[".ods",".xls",".xlsm",".xlsx"],
    
    "compressed":[".zip",".7z",".arz",".deb",".pkg",".rar",".rpm",".tar.gz",".z"],
    
    
#     Commenting out extension:
    
#     "database":[".csv",".dat",".db",".dbf",".log",".mdb",".sav",".sql",".tar",".xml"],
    
#     "email":[".email",".eml",".emlx",".msg",".oft",".ost",".pst",".vcf"],
    
#     "disc":[".bin",".iso",".dmg",".toast",".vcd"],
    
#     "web-related":[".htm",".html",".php",".js",".sp",".aspx",".cfm",".css",".part",".rss",".xhtml"],
    
#     "program-files":[".c",".cpp",".java",".sh",".py",".ipynb",".swift",".vb",".class",".cs",".cgi",".pl"],
    
#     "executable":[".exe",".apk",".bat",".bin",".com",".gadgets",".jar",".msi",".py",".wsf"],
    
#     "font":[".fnt",".fon",".otf",".ttf"],
    
#     "system-files":[".bak",".cab",".cfg",".cpl",".cur",".dll",".dmp",".drv",".icns",".ini",".lnk",".msi",".sys",".tmp"],
    
}
    


#Some extensions are common to more than one category. For example files like ".cgi",".pl",".py" can be categorised in more than
# one type.

# Creating folders
for i in extensions:
    if os.path.isdir(i)!=True:
        os.mkdir(os.path.join(parent,i))
        print(i + " folder created")
    else:
        print(i+ " folder already exists.")


for file in os.listdir():
    for i in extensions:
        for t in extensions[i]:
            s=t+r"$"
            if re.search(s,file):
                shutil.move(file,i)
                break