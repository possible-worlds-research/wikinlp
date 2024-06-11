import inspect, os
import re
import bz2
import sys
from glob import glob
import shutil
from pathlib import Path
import numpy as np
from os.path import join, exists
import fasttext
from scipy.spatial.distance import cdist

fasttext.FastText.eprint = lambda x: None

class DSTrainer:

    def __init__(self, lang=None, spm_model_path=None):
        self.lang = lang
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.path = os.path.dirname(os.path.abspath(filename))
        self.model_path = ""
        self.train_path = ""
        if spm_model_path == None:
            self.spm_model_path = ""
        else:
            self.spm_model_path = spm_model_path

    def mk_wiki_training_data(self, corpus_size):
        print("\n--- TrainDS: Process corpus for training ---")
        processed_dir = join(os.getcwd(),join('ds',self.lang))
        Path(processed_dir).mkdir(exist_ok=True, parents=True)

        print(self.spm_model_path)
        m = re.search('k\.([^\.]*)\.',self.spm_model_path.split('/')[-1])
        model_date = m.group(1)
        data_dir = processed_dir.replace('/ds/','/data/')
        txt_paths = glob(join(data_dir,f"{self.lang}wiki-latest-pages-articles*.raw.{model_date}.sp"))

        ds_train_path = txt_paths[0].replace('raw','full')
        out_file = open(ds_train_path,'w')
        self.train_path = ds_train_path

        num_tokens = 0
        for txt_path in txt_paths:
            f = open(txt_path,'r')

            for l in f:
                if "<doc" in l or "</doc" in l:
                    continue
                elif num_tokens >= corpus_size:
                    break
                else:
                    out_file.write(l)
                    num_tokens+=len(l.split())
            f.close()

        print("\tData processed and ready for training. Corpus size:",num_tokens,".")
        out_file.close()


    def train_fasttext(self, corpus_size=10000000, data_path=None):
        if data_path == None:
            self.mk_wiki_training_data(corpus_size)
        else:
            self.train_path = data_path
        
        print("\n--- TrainDS: Training fasttext on corpus ---")
        sp_path_filename = self.train_path.split('/')[-1]
        processed_dir = join(os.getcwd(),join('ds',self.lang))
        if str(corpus_size)[-6:] == '000000':
            corpus_size_str = str(corpus_size)[:-6]+'m'
        else:
            corpus_size_str = str(corpus_size)
        self.model_path = join(processed_dir,self.spm_model_path.split('/')[-1].replace('.model','.cs'+corpus_size_str+'.ft'))

        model = fasttext.train_unsupervised(self.train_path, model='skipgram')
        model.save_model(self.model_path)

        print("\nAll done!! Your fasttext model is at",self.model_path,".")


    def compute_nns(self, top_words=100, k=10, model_path=None):
        if model_path == None:
            model = fasttext.load_model(self.model_path)
        else:
            model = fasttext.load_model(model_path)

        print("\n--- TrainDS: Computing cosine matrix for top",top_words,"words in space ---")
        m = model.get_output_matrix()[:top_words,:]
        vocab = model.words[:top_words]
        cosines = 1 - cdist(m, m, metric="cosine")

        nns = {}
        for i in range(len(vocab)):
            word = vocab[i]
            ns = []
            target_cosines = cosines[i]
            best_n = np.argpartition(target_cosines, -k)[-k:]

            for ind in best_n:
                if ind != word:
                    ns.append(vocab[ind])
            nns[word] = ns

        return nns


    def compute_word_nns(self, word=None, k=10, model_path=None):
        if model_path == None:
            model = fasttext.load_model(self.model_path)
        else:
            model = fasttext.load_model(model_path)

        m = model.get_output_matrix()
        words = model.words
        target = model.get_word_id(word)
        ns = []
        cos = []

        if target != -1:
            n = max(10000,target)
            m = m[:n,:]
            cosines = 1 - cdist(m, m, metric="cosine")

            target_cosines = cosines[target]
            best_n = np.argpartition(target_cosines, -k)[-k:]

            for ind in best_n:
                if words[ind] != word:
                    ns.append(words[ind])
                    cos.append(target_cosines[ind])

        return ns, cos
