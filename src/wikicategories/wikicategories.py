#!/usr/bin/python3

import requests
import re
import inspect, os
from os.path import join, exists
import pickle
import requests
from pathlib import Path
from nltk.tokenize import word_tokenize

class WikiCatProcessor:

    def __init__(self,lang=None):
        self.lang = lang
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.path = os.path.dirname(os.path.abspath(filename))
        self.URL = "https://"+self.lang+".wikipedia.org/w/api.php"

    def get_categories(self, mincount=20, maxcount=500):
        processed_dir = join(os.getcwd(),join('data',self.lang))
        Path(processed_dir).mkdir(exist_ok=True, parents=True)

        print("\n---> WikiCategories: downloading category list")
        S = requests.Session()

        PARAMS = {
            "action": "query",
            "format": "json",
            "list": "allcategories",
            "acmin": mincount, #only categories with at least that many instances
            "acmax": maxcount, #only categories with at most that many instances
            "aclimit": 500 #how many categories to return in one go
        }

        cat_file_path = join(processed_dir,"wiki_categories.min."+str(mincount)+".max."+str(maxcount)+".txt")
        f = open(cat_file_path,'w')

        while True: #loop until all categories are returned
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
        print("\n---> WikiCategories: your category list is at", cat_file_path)
        return cat_file_path

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
                "cmlimit": "500" #that many pages per call
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

    def extract_sections(self, docstr, sections):
        tmp = ""
        write = False
        for l in docstr.split('\n'):
            m1 = re.search('^\s*==',l)
            m2 = re.search('^\s*##',l)
            if (m1 or m2) and write:
                write = False
            if write:
                tmp+= ' '.join(word_tokenize(l))+'\n'
            for section in sections:
                m1 = re.search('==\s*'+section+'\s*==',l)
                m2 = re.search('##\s*'+section,l)
                if m1 or m2:
                    write=True
        return tmp


    def get_page_content(self, categories, doctags=True, tokenize=False, lower=False, sections=None):
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

            suffix = 'txt'
            if tokenize:
                suffix = 'tok.'+suffix
            if lower:
                suffix = 'low.'+suffix
            if doctags:
                suffix = 'doc.'+suffix
            if sections:
                suffix = sections[0].lower()+'.'+suffix
           
            output_path = join(cat_dir,"linear."+suffix)
            content_file = open(output_path,'w')

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
                    if sections:
                        extract = self.extract_sections(extract,sections)
                    if extract == '':
                        continue
                    if doctags:
                        content_file.write("<doc url=\"https://"+self.lang+".wikipedia.org/wiki/?curid="+IDs[i]+"\" id=\""+IDs[i]+"\" title=\""+titles[i]+"\">\n")
                    if tokenize:
                        tmp = ""
                        for l in extract.split('\n'):
                            if l != '':
                                tmp+= ' '.join(word_tokenize(l))+'\n'
                        extract = tmp
                    if lower:
                        extract = extract.lower()
                    content_file.write(extract+'\n')
                    if doctags:
                        content_file.write("</doc>\n\n")

            content_file.close()
            print("\n---> WikiCategories: your preprocessed corpus is at", output_path)
