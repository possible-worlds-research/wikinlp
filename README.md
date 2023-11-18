# WikiLoader

This package lets you download and preprocess Wikipedia in some language of your choice. You don't have to worry about finding the latest snapshot, downloading it, figuring out how to extract plain text. All is done automatically. Additionally, the package offers options for training basic NLP tools on your Wikipedia snapshot. At the moment, the following are offered:

* converting (part of) a Wikipedia snapshot into a plain text corpus;
* making a plain text corpus out of specific Wikipedia categories;
* training a tokenizer model with the external SentencePiece package;
* training a distributional semantic space over the SentencePiece vocabulary.

Please check the language code for your Wikipedia: it is the prefix to your Wikipedia url. For instance, The English Wikipedia is at *https://en.wikipedia.org/* so its language code is *en*. The Hindi Wikipedia is at *https://hi.wikipedia.org/*, so its language code is *hi*.

**Warning:** For people who are new to Wikipedia processing... anything you do on English, and generally on large snaphots, will take time. So make yourself a cup of tea before you start.

**Credits:** This package includes a modified version of the excellent [wikiextractor](https://github.com/attardi/wikiextractor) code. It also builds on various existing NLP tools, most notably [SentencePiece](https://github.com/google/sentencepiece) and [FastText](https://github.com/facebookresearch/fastText).


## Installation

We recommend installing this package in a virtual environment. If you do not have virtualenv installed, you can get it in the following way: 

```
sudo apt update
sudo apt install python3-setuptools
sudo apt install python3-pip
sudo apt install python3-virtualenv
```

Then, create a directory for wikiloader, make your virtual environment and install the package:

```
mkdir wikiloader
cd wikiloader
virtualenv env && source env/bin/activate
pip install git+https://github.com/possible-worlds-xyz/wikiloader.git
```


## Loading a Wikipedia snapshot

Wikipedia dumps can be very large and take several hours to be downloaded and processed. So WikiLoader allows you to set a limit on the number of files you download. Download happens in order, from snapshot file number 1 up.

Here is an example usage, which loads and processes two files from the English Wikipedia dump:

```
from wikiloader.wikiloader import WikiLoader

lang = 'en'

print("Running WikiLoader")
wikiloader = WikiLoader(lang)
wikiloader.mk_wiki_data(2)

```

## Category processing

This module relies on the Wikipedia API. The first thing you may want to do when playing with categories is to get the list of all categories for a language. You can do this as follows.


```
from wikicategories.wikicategories import WikiCatProcessor

lang = 'en'

catprocessor = WikiCatProcessor(lang)
catprocessor.get_categories()
```

You will find a category list saved in *data/en/wiki_categories.txt*.

Now, let's assume you have found a couple of categories you are interested in and wish to create a corpus out of those. You would retrieve the pages contained in those categories and then the plain text for each of those pages:

```
categories = ["Australian women novelists", "Australian women painters"]
catprocessor.get_category_pages(categories)
catprocessor.get_page_content(categories)
```

You should now find two new directories in your *data/en/categories/* folder, named after the two categories in your list. Each directory should contain a *linear.txt* file, which is your plain text corpus for that category, as well as a *titles.txt* file containing the titles of the pages in your corpus.


## Training a wordpiece tokenizer

You can train a wordpiece tokenizer on the Wiki data you have downloaded, using the [SentencePiece package](https://github.com/google/sentencepiece). WikiLoader will automatically make a 5M corpus out of your data and train on it.

```
from trainspm.trainspm import TrainSPM

lang = 'en'

print("Running TrainSPM")
trainspm = TrainSPM(lang,8000)
trainspm.train_sentencepiece()
```

In case you would like to train SentencePiece on a specific file of your choice, you can provide its path:

```
from trainspm.trainspm import TrainSPM

lang = 'en'

print("Running TrainSPM")
trainspm.train_sentencepiece(data_path='data/en/enwiki-latest-pages-articles1.xml-p1p41242.raw.txt')
```


## Training a word vector model for the SentencePiece vocabulary

Once you have a preprocessed Wiki dump and a SentencePiece model trained on that dump, you can compute a word vector space for each word piece in your model and perform similarity computations over that space. The WikiLoader module uses [FastText](https://github.com/facebookresearch/fastText) by default for the vector space construction. Here is some example code, which first loads a previously trained SentencePiece model, applies it to the wiki data that was originally downloaded, and uses the tokenized corpus to train a vector space.

```
from trainds.trainds import TrainDS
from trainspm.trainspm import TrainSPM

lang = 'en'

print("Generating SPM corpus")
trainspm = TrainSPM(lang,8000) #Size of your vocabulary file
trainspm.model_path='./spm/en/enwiki.8k.2023-11-17.model'
trainspm.apply_sentencepiece()

print("Running FastText")
trainds = TrainDS(lang)
trainds.train_fasttext(corpus_size=100000000)
nns = trainds.compute_nns(top_words=100)
for word,ns in nns.items():
    print(word,':',' '.join(ns))
```

In case you have previously trained the vector space and simply want to retrieve the nearest neighbours, you can load the trained model this way:

```
trainds = TrainDS(lang)
trainds.model_path = "./ds/en/enwiki-latest-pages-articles.xml.full.ft"
nns = trainds.compute_nns(top_words=10000)
for word,ns in nns.items():
    print(word,':',' '.join(ns))
```


