import inspect, os
import re
import bz2
import sys
from glob import glob
import shutil
from pathlib import Path
from os.path import join, exists
from datetime import datetime
import sentencepiece as spm

class SPMTrainer:

    def __init__(self,lang=None, vocab_size=None, model_path=None):
        self.lang = lang
        self.vocab_size = vocab_size
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.path = os.path.dirname(os.path.abspath(filename))
        if model_path == None:
            self.model_path = ""
        else:
            self.model_path = model_path
        self.train_path = ""

    def mk_wiki_training_data(self):
        print("\n--- TrainSPM: Make training corpus (5M words) ---")
        processed_dir = join(os.getcwd(),join('spm',self.lang))
        Path(processed_dir).mkdir(exist_ok=True, parents=True)

        data_dir = processed_dir.replace('spm','data')
        try:
            txt_path = glob(join(data_dir,f"{self.lang}wiki-latest-pages-articles1.xml*.raw.*txt"))[0]
        except:
            txt_path = glob(join(data_dir,f"{self.lang}wiki-latest-pages-articles.xml*.raw.*txt"))[0]
        
        spm_train_path = txt_path.replace('raw','5M')
        out_file = open(spm_train_path,'w')
        self.train_path = spm_train_path

        f = open(txt_path,'r')

        word_count = 0
        for l in f:
            if "</doc" in l:
                out_file.write(l)
                if word_count > 5000000: #5M words only
                    break
            else:
                out_file.write(l)
                word_count+=len(l.split()) #Very rough, will include markup. But doesn't matter.

        out_file.write("</mediawiki>")
        print("\tWord count in training file:",word_count)
        f.close()
        out_file.close()


    def train_sentencepiece(self, data_path=None):
        if data_path == None:
            self.mk_wiki_training_data()
        else:
            self.train_path = data_path
        print(f"\n--- TrainSPM: Training sentencepiece on corpus {data_path} ---")
        date = datetime.today().strftime('%Y-%m-%d')
        if str(self.vocab_size)[-3:] == '000':
            vocab_size_str = str(self.vocab_size)[:-3]+'k'
        else:
            vocab_size_str = str(self.vocab_size)
        txt_path_filename = self.lang+'wiki.'+vocab_size_str+'.'+date
        spm.SentencePieceTrainer.train(input=self.train_path, model_prefix=join('spm',self.lang,txt_path_filename), vocab_size=self.vocab_size, minloglevel=2, normalization_rule_name='nmt_nfkc_cf')
        print("\nAll done!! Your sentence piece model is at spm/"+self.lang+"/"+txt_path_filename+"...")

    def apply_sentencepiece(self):
        data_dir = join(os.getcwd(),join('data',self.lang))
        spm_dir = join(os.getcwd(),join('spm',self.lang))

        if self.model_path == '':
            print("You did not initialise your model with an existing model path. Try again.")
            return 0

        m = re.search('k\.([^\.]*)\.',self.model_path.split('/')[-1])
        model_date = m.group(1)

        sp = spm.SentencePieceProcessor()
        sp.load(self.model_path)
        print("\n--- Applying sentencepiece to corpus ---")
        start_doc=""
        doc=""
        txt_paths = glob(join(data_dir,'*.raw.*.txt'))
        for txt_path in txt_paths:
            print("\tApplying spm model to",txt_path)
            spm_filename = txt_path.replace('.txt','.'+model_date+'.sp')
            spf = open(spm_filename,'w')

            f = open(txt_path,'r')
            for l in f:
                if '<doc' in l:
                    start_doc = l
                elif '</doc' in l:
                    spmdoc = ' '.join([wp for wp in sp.encode_as_pieces(doc)])+'\n'
                    #Write spf file
                    spf.write(start_doc)
                    spf.write(spmdoc)
                    spf.write(l)
                    doc = ""
                else:
                    if len(l) > 0:
                        doc+=l
            f.close()
        print("\n All done!! Your sentencepieced corpus is at",data_dir,".")

