import inspect, os
from os.path import join, exists
import re
import bz2
import pickle
import requests
#import subprocess
from pathlib import Path
from wikiextractor.WikiExtractor import process_wiki


class WikiLoader:

    def __init__(self,lang=None):
        self.lang = lang
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.path = os.path.dirname(os.path.abspath(filename))

    def mk_wiki_data(self):
        processed_dir = join(os.getcwd(),join('data',self.lang))
        Path(processed_dir).mkdir(exist_ok=True, parents=True)

        link_file = self.get_wiki_links()
        wiki_paths = self.read_wiki_links()

        for wiki_path in wiki_paths:
            print("\n---> WikiLoader: downloading ", wiki_path)
            bz2_file = join(processed_dir,wiki_path.split('/')[-1])
            if exists(bz2_file):
                print("     File already exists. Skipping download.")
            else:
                #subprocess.run(["wget",wiki_path, "-P",processed_dir])
                with open (join(processed_dir,bz2_file), "wb") as f:
                    f.write(requests.get(wiki_path).content)

            self.extract_xml(bz2_file)
            self.get_categories(bz2_file)
            cat_file = bz2_file.replace('bz2','cats.pkl')
            self.mk_linear(bz2_file,cat_file)

    def bz2_uncompress(self, filepath):
        print("     Uncompressing downloaded bz2:",filepath,"---")
        newfilepath = filepath.replace(".bz2","")
        with open(newfilepath, 'wb') as new_file, bz2.BZ2File(filepath, 'rb') as file:
            for data in iter(lambda : file.read(100 * 1024), b''):
                new_file.write(data)
        return newfilepath

    def read_wiki_links(self):
        with open("./wiki_dump_links/"+self.lang+"_wiki_dump_links.txt") as f:
            return f.read().splitlines()

    def get_wiki_links(self):
        print("\n---> WikiLoader: Getting wiki links for download.")
        html = requests.get(url = 'https://dumps.wikimedia.org/'+self.lang+'wiki/latest/').text
        match = re.findall(self.lang+'wiki-latest-pages-articles[0-9]*\.xml-p[0-9]*p[0-9]*\.bz2', html)
        if len(match) == 0:
            match = re.findall(self.lang+'wiki-latest-pages-articles.xml.bz2', html) #For wikis with only one dump file.
        match = list(set(match))

        Path("./wiki_dump_links").mkdir(exist_ok=True, parents=True)
        filename = "./wiki_dump_links/"+self.lang+"_wiki_dump_links.txt"
        outf = open(filename,'w')
        for url in match:
            outf.write("https://dumps.wikimedia.org/"+self.lang+"wiki/latest/"+url+"\n")
        outf.close()
        print("     Finished!")
        return filename

    def get_categories(self, bz2_file):
        print("\n---> WikiLoader: Get categories from corpus ---")
        xml_file = bz2_file.replace('bz2','xml')
        all_categories = {}

        #Read file with translations of 'category'
        cattransl = ""
        for l in open(join(self.path,"./static/wiki_markup_info.txt")):
            l = l.rstrip('\n')
            fields = l.split()
            if fields[0] == self.lang:
                cattransl = fields[1]
                break

        title = ""
        f=open(xml_file,'r')
        for l in f:
            l.rstrip('\n')
            if "<title" in l:
                m = re.search('<title>([^<]*)<',l)
                title = m.group(1)
                all_categories[title] = []
            if '[['+cattransl+':' in l:
                m = re.search('\[\['+cattransl+':([^\]]*)\]\]',l)
                if m:
                    cat = m.group(1)
                    all_categories[title].append(cat)
        pklf = bz2_file.replace('bz2','cats.pkl')
        with open(pklf, 'wb') as f:
            pickle.dump(all_categories,f)


    def extract_xml(self, bz2_file):
        print("\n---> WikiLoader: Extracting XML version of corpus.")

        out_file = open(bz2_file.replace('bz2','xml'),'w')
        uncompressed = self.bz2_uncompress(bz2_file)
        #os.remove(bz2_file)
        f=open(uncompressed,'r')

        word_count = 0
        content = ""
        for l in f:
            if "</page" in l:
                out_file.write(l)
                content = ""
            else:
                out_file.write(l)
                word_count+=len(l.split()) #Very rough, will include markup. But doesn't matter.

        out_file.write("</mediawiki>")
        print("     Word count:",word_count)
        f.close()
        os.remove(uncompressed)
        out_file.close()


    def mk_linear(self, bz2_file, cat_file):
        print("\n---> WikiLoader: Generating linear version of corpus ---")

        xml_file = bz2_file.replace('bz2','xml')
        tmp_linear_file = bz2_file.replace('bz2','raw.tmp')
        process_wiki(xml_file,tmp_linear_file)

        all_categories = pickle.load(open(cat_file,'rb'))
        tmpf = open(tmp_linear_file,'r')
        linear_filename = tmp_linear_file.replace('tmp','txt')
        linear_file = open(linear_filename,'w')
        for l in tmpf:
            if '<doc' in l:
                m = re.search('.*title="([^"]*)">',l)
                title = m.group(1)
                categories = all_categories[title] 
                cs = ' categories="'+'|'.join([c for c in categories])+'"'
                linear_file.write(l.replace('>',cs+'>'))
            else:
                linear_file.write(l.lower())
        linear_file.close()
        tmpf.close()
        os.remove(tmp_linear_file)
        os.remove(xml_file)



