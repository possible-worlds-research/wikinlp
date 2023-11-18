#!/usr/bin/python3

import requests
import re
import inspect, os
from os.path import join, exists
import pickle
import requests
from pathlib import Path


class WikiCatProcessor:

    def __init__(self,lang=None):
        self.lang = lang
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.path = os.path.dirname(os.path.abspath(filename))
        self.URL = "https://"+self.lang+".wikipedia.org/w/api.php"

    def get_categories(self):
        processed_dir = join(os.getcwd(),join('data',self.lang))
        Path(processed_dir).mkdir(exist_ok=True, parents=True)

        print("\n---> WikiCategories: downloading category list")
        S = requests.Session()

        PARAMS = {
            "action": "query",
            "format": "json",
            "list": "allcategories",
            "acmin": 200,
            "aclimit": 500
        }

        f = open(join(processed_dir,"wiki_categories.txt"),'w')

        for i in range(100):
            R = S.get(url=self.URL, params=PARAMS)
            DATA = R.json()

            CATEGORIES = DATA["query"]["allcategories"]

            for cat in CATEGORIES:
                cat_name = cat["*"]
                f.write(cat_name+'\n')
            
            if "continue" in DATA:
                PARAMS["acfrom"] = DATA["continue"]["accontinue"]
            else:
                break

        f.close()

    def get_category_pages(self, categories):
        processed_dir = join(os.getcwd(),join('data',self.lang))
        Path(processed_dir).mkdir(exist_ok=True, parents=True)

        print("\n---> WikiCategories: downloading pages for selected categories")
        S = requests.Session()

        for cat in categories:
            cat_dir = join(processed_dir,"categories/"+cat.replace(' ','_'))
            Path(cat_dir).mkdir(exist_ok=True, parents=True)
            title_file = open(join(cat_dir,"titles.txt"),'w')

            PARAMS = {
                "action": "query",
                "list": "categorymembers",
                "format": "json",
                "cmtitle": "Category:"+cat,
                "cmlimit": "100"
            }

            for i in range(5):
                R = S.get(url=self.URL, params=PARAMS)
                DATA = R.json()

                PAGES = DATA["query"]["categorymembers"]

                for page in PAGES:
                    title = page["title"]
                    ID = str(page["pageid"])
                    if title[:9] != "Category:":
                        title_file.write(ID+' '+title+'\n')
         
                if "continue" in DATA:
                    PARAMS["cmcontinue"] = DATA["continue"]["cmcontinue"]
                else:
                    break

            title_file.close()

    def get_page_content(self, categories):
        def read_titles(filename):
            IDs = []
            titles = []
            f = open(filename,'r')
            for l in f:
                l.rstrip('\n')
                IDs.append(l.split()[0])
                titles.append(' '.join(l.split()[1:]))
            return IDs,titles

        processed_dir = join(os.getcwd(),join('data',self.lang))
        Path(processed_dir).mkdir(exist_ok=True, parents=True)

        print("\n---> WikiCategories: downloading content of pages for selected categories")
        S = requests.Session()

        for cat in categories:
            print("\t>> Processing category",cat)
            cat_dir = join(processed_dir,"categories/"+cat.replace(' ','_'))
            Path(cat_dir).mkdir(exist_ok=True, parents=True)
            title_file = join(cat_dir,"titles.txt")
            IDs, titles = read_titles(title_file)

            content_file = open(join(cat_dir,"linear.txt"),'w')

            for i in range(len(titles)):
                PARAMS = {
                    "action": "query",
                    "prop": "extracts",
                    "format": "json",
                    "explaintext": True,
                    "redirects": True,
                    "titles": titles[i]
                }

                R = S.get(url=self.URL, params=PARAMS)
                DATA = R.json()

                PAGES = DATA["query"]["pages"]

                for page in PAGES:
                    extract = PAGES[page]["extract"]
                    content_file.write("<doc url=\"https://"+self.lang+".wikipedia.org/wiki/?curid="+IDs[i]+"\" id=\""+IDs[i]+"\" title=\""+titles[i]+"\">\n")
                    content_file.write(extract+'\n')
                    content_file.write("</doc>\n\n")

            content_file.close()
