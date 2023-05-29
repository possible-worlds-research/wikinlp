"""Process a whole Wikipedia dump with the fruit fly

Usage:
  run.py --lang=<language_code>
  run.py (-h | --help)
  run.py --version

Options:
  --lang=<language code>         The language of the Wikipedia to process.
  -h --help                      Show this screen.
  --version                      Show version.

"""

from docopt import docopt
from glob import glob
from random import shuffle
import joblib

from codecarbon import EmissionsTracker
from spm.spm_train_on_wiki import mk_spm
from datasets.get_wiki_data import mk_wiki_data
from fly.train_models import train_umap, hack_umap_model, run_pca, hack_pca_model, train_birch, train_fly
from fly.apply_models import apply_dimensionality_reduction, apply_fly
from fly.label_clusters import generate_cluster_labels


def get_training_data(train_spf_path):

    def get_n_docs(input_file_path, output_file, n):
        article_count = 0
        article = ""
        input_file = open(input_file_path)
        for l in input_file:
            if "</doc" in l:
                article+=l
                output_file.write(article)
                article = ""
                article_count+=1
                if article_count == n:
                    break
            else:
                article+=l
        input_file.close()
        return article_count

    print("--- Gathering training data from sample of dump files ---")
    required_article_count = 50000
    train_spf = open(train_spf_path,'w')

    '''Get first dump file, which usually contains 'core' articles.'''
    dump_split = True
    try:
        first_sp_file = glob(f"./datasets/data/{lang}/{lang}wiki-latest-pages-articles1.*sp")[0]
    except:
        first_sp_file = f"./datasets/data/{lang}/{lang}wiki-latest-pages-articles.xml.sp"
        dump_split = False
    c = get_n_docs(first_sp_file, train_spf, 30000) #Up to 30,000 articles from first dump file
    print(">>> Gathered",c,"articles from ",first_sp_file)

    '''Get sample from other dump files, to get correct data distribution.'''
    required_article_count-=c
    if dump_split:
        spfs = glob(f"./datasets/data/{lang}/{lang}wiki-latest-pages-articles*sp")
        shuffle(spfs)
        for i in range(4):
            c = int(required_article_count / 4)
            get_n_docs(spfs[i], train_spf, c) #Articles from other dump files
            print(">>> Gathered", c,"articles from ",spfs[i])
    train_spf.close()
    print(">>> Finished building the training corpus ---")



if __name__ == '__main__':
    args = docopt(__doc__, version='Get Wikipedia in fruit fly vectors, ver 0.1')
    lang = args['--lang']
    #tracker = EmissionsTracker(output_dir="./emission_tracking", project_name="Multilingual Fly")
    #tracker.start()

    mk_spm(lang)
    mk_wiki_data(lang)
    train_path = f"./datasets/data/{lang}/{lang}wiki-latest-pages-articles.train.sp"
    get_training_data(train_path)

    input_m, umap_m, best_logprob_power, best_top_words = train_umap(lang, train_path)
    #input_m, pca_m, best_logprob_power, best_top_words = run_pca(lang, train_path)
    print("LOG: BEST LOG POWER - ",best_logprob_power, "BEST TOP WORDS:", best_top_words)
    hacked_m = hack_umap_model(lang, train_path, best_logprob_power, best_top_words, input_m, umap_m)
    #hacked_m = hack_pca_model(lang, train_path, best_logprob_power, best_top_words, input_m, pca_m)
    brm, labels = train_birch(lang, hacked_m)
    generate_cluster_labels(lang, train_path, labels, best_logprob_power, best_top_words)
    
    apply_dimensionality_reduction(lang, brm, best_logprob_power, best_top_words)

    train_fly(lang, train_path, 32)
    apply_fly(lang, best_logprob_power, best_top_words)

    #tracker.stop()

