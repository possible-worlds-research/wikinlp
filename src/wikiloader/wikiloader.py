import re
import bz2
import pickle
import requests
import inspect, os
from pathlib import Path
from os.path import join, exists
from nltk.tokenize import word_tokenize
from wikiextractor.WikiExtractor import process_wiki


class WikiLoader:

    def __init__(self,lang=None):
        self.lang = lang
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.path = os.path.dirname(os.path.abspath(filename))

    def mk_wiki_data(self, n_dump_files = None, doctags=True, tokenize=False, lower=True, sections=None):
        processed_dir = join(os.getcwd(),join('data',self.lang))
        Path(processed_dir).mkdir(exist_ok=True, parents=True)

        link_file = self.get_wiki_links()
        wiki_paths = self.read_wiki_links()
        linear_filenames = []

        if not n_dump_files:
            n = len(wiki_paths)
        else:
            n = min(n_dump_files, len(wiki_paths))

        for i in range(n):
            wiki_path = wiki_paths[i]
            print("\n---> WikiLoader: downloading ", wiki_path, "(dump file",i+1,")")
            bz2_file = join(processed_dir,wiki_path.split('/')[-1])
            if exists(bz2_file):
                print("     File already exists. Skipping download.")
            else:
                with open (join(processed_dir,bz2_file), "wb") as f:
                    f.write(requests.get(wiki_path).content)

            self.extract_xml(bz2_file)
            self.get_categories(bz2_file)
            cat_file = bz2_file.replace('bz2','cats.pkl')
            lf = self.mk_linear(bz2_file, cat_file, doctags=doctags, tokenize=tokenize, lower=lower, sections=sections)
            linear_filenames.append(lf)
        return linear_filenames

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

        if len(match) > 1:
            for i in range(1, len(match)): #Ordering list
                r = re.compile(".*articles"+str(i)+"\.xml.*")
                urls = list(filter(r.match,match))
                for url in urls:
                    outf.write("https://dumps.wikimedia.org/"+self.lang+"wiki/latest/"+url+"\n")
        else:
            outf.write("https://dumps.wikimedia.org/"+self.lang+"wiki/latest/"+match[0]+"\n")
            
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

    def mk_linear(self, bz2_file, cat_file, doctags=True, tokenize=False, lower=False, sections=None):
        print("\n---> WikiLoader: Generating linear version of corpus ---")

        xml_file = bz2_file.replace('bz2','xml')
        tmp_linear_file = bz2_file.replace('bz2','raw.tmp')
        process_wiki(dumpfile=xml_file,outfile=tmp_linear_file)

        all_categories = pickle.load(open(cat_file,'rb'))
        tmpf = open(tmp_linear_file,'r')
        suffix = 'txt'
        if tokenize:
            suffix = 'tok.'+suffix
        if lower:
            suffix = 'low.'+suffix
        if doctags:
            suffix = 'doc.'+suffix
        if sections:
            suffix = sections[0].lower()+'.'+suffix
        linear_filename = tmp_linear_file.replace('tmp',suffix)
        linear_file = open(linear_filename,'w')
        doc = ''
        startline = ''
        for l in tmpf:
            m1 = re.search('^\s*==',l)
            m2 = re.search('^\s*##',l)
            if (m1 or m2) and not doctags:
                continue
            if '<doc' in l:
                m = re.search('.*title="([^"]*)">',l)
                title = m.group(1)
                categories = all_categories[title] 
                cs = ' categories="'+'|'.join([c for c in categories])+'"'
                startline = l.replace('>',cs+'>\n')
            elif '</doc' in l: 
                if sections:
                    doc = self.extract_sections(doc,sections)
                if doc == '':
                    continue
                if doctags:
                    linear_file.write(startline)
                if tokenize:
                    tmp = ""
                    for l in doc.split('\n'):
                        if l != '':
                            tmp+= ' '.join(word_tokenize(l))+'\n'
                    doc = tmp
                if lower:
                    doc = doc.lower()
                linear_file.write(doc)
                doc = ''
            else:
                doc+=l+'\n'
        linear_file.close()
        tmpf.close()
        os.remove(tmp_linear_file)
        os.remove(xml_file)
        print("\n---> WikiLoader: your preprocessed corpus is at", linear_filename)
        return linear_filename


