# WikiNLP

This package lets you download and preprocess Wikipedia in some language of your choice. You don't have to worry about finding the latest snapshot, downloading it, figuring out how to extract plain text. All is done automatically. Additionally, the package offers options for training basic NLP tools on your Wikipedia snapshot. At the moment, the following are offered:

* converting (part of) a Wikipedia snapshot into a plain text corpus;
* making a plain text corpus out of specific Wikipedia categories;
* training a tokenizer model with the external SentencePiece package;
* training a distributional semantic space over the SentencePiece vocabulary.

Please check the language code for your Wikipedia: it is the prefix to your Wikipedia url. For instance, The English Wikipedia is at *https://en.wikipedia.org/* so its language code is *en*. The Hindi Wikipedia is at *https://hi.wikipedia.org/*, so its language code is *hi*.

**Warning:** For people who are new to Wikipedia processing... anything you do on English, and generally on large snaphots, will take time. So make yourself a cup of tea before you start.

**Credits:** This package includes a modified version of the excellent [wikiextractor](https://github.com/attardi/wikiextractor) code. It also builds on various existing NLP tools, most notably [NLTK](https://www.nltk.org/), [SentencePiece](https://github.com/google/sentencepiece) and [FastText](https://github.com/facebookresearch/fastText).


## Installation

We recommend installing this package in a virtual environment. If you do not have virtualenv installed, you can get it in the following way: 

```
sudo apt update
sudo apt install python3-setuptools
sudo apt install python3-pip
sudo apt install python3-virtualenv
```

Then, create a directory for WikiNLP, make your virtual environment and install the package:

```
mkdir wikinlp
cd wikinlp
virtualenv env && source env/bin/activate
pip install git+https://github.com/possible-worlds-research/wikinlp.git
```


## Loading a Wikipedia snapshot

Wikipedia dumps can be very large and take several hours to be downloaded and processed. So WikiNLP allows you to set a limit on the number of files you download. Download happens in order, from snapshot file number 1 up.

Here is an example usage, which loads and processes two files from the English Wikipedia dump:

```
from wikinlp.downloader import Downloader

lang = 'en'

print("Running WikiNLP downloader")
wikinlp = Downloader(lang)
wikinlp.mk_wiki_data(2)

```

By default, the resulting corpus shows documents between *<doc></doc>* tags. The opening *<doc>* tag contains additional information: the title of the page, its url, and the categories it belongs to.

You have further options to preprocess your corpus as you are extracting it. You can choose to 1) tokenize (using the [nltk](https://www.nltk.org/) package); 2) lowercase; 3) leave out document boundaries; 4) only extract particular sections of the Wikipedia documents. For instance, to extract the same corpus as above tokenized and lowercased, with no document boundaries, we would write the following:

```
from wikinlp.downloader import Downloader

lang = 'en'

print("Running WikiNLP downloader")
wikinlp = Downloader(lang)
wikinlp.mk_wiki_data(2, tokenize=True, lower=True, doctags=False)

```

We will show an example of section filtering in the next section.


## Category processing

This module relies on the Wikipedia API. The first thing you may want to do when playing with categories is to get the list of all categories for a language. You can do this as follows.


```
from wikinlp.categories import CatProcessor

lang = 'en'

catprocessor = CatProcessor(lang)
catprocessor.get_categories()
```

You will find a category list saved in *data/en/wiki_categories.txt*. By default, CatProcessor extracts a list of categories containing between 20 and 500 documents. You can change the min and max values when calling the function *get_categories*:

```
from wikinlp.categories import CatProcessor

lang = 'en'

catprocessor = CatProcessor(lang)
catprocessor.get_categories(mincount=5, maxcount=100)
```


Now, let's assume you have found a couple of categories you are interested in and wish to create a corpus out of those. You would retrieve the pages contained in those categories and then the plain text for each of those pages:

```
categories = ["Australian women novelists", "Australian women painters"]
catprocessor.get_category_pages(categories)
catprocessor.get_page_content(categories)
```

You should now find two new directories in your *data/en/categories/* folder, named after the two categories in your list. Each directory should contain a *linear...* file, which is your plain text corpus for that category, as well as a *titles.txt* file containing the titles of the pages in your corpus.

NB: by default, CatProcessor takes a little nap after processing each category. This is meant to ensure that we don't overload the Wikipedia API. If you are just downloading a couple of categories, you can reduce the sleeping time:

```
catprocessor.get_page_content(categories, sleep_between_cats=1)
```

You can even select particular sections of Wikipedia pages rather than extracting the whole document:

```
categories = ["Action novels"]
catprocessor.get_category_pages(categories)
catprocessor.get_page_content(categories, sections=['Plot','Plot summary'])
```

Note that the *sections* argument takes a list of section titles. It usually takes some trial and error to find out all the possible ways that Wikipedia contributors may have entitled a particular section type. All of them can be inserted in the sections list.

Finally, it is also possible to get the external links for particular categories. Here is a minimal example retrieving the external links from simple Wikipedia for the category '1908 books':

```
from wikinlp.categories import CatProcessor

lang = 'simple'
catprocessor = CatProcessor(lang)
catprocessor.get_page_extlinks(['1908 books'])
```


## Training a wordpiece tokenizer

We have already seen that you can apply standard tokenization to your corpus while extracting it. Alternatively, you can train a wordpiece tokenizer on the Wiki data you have downloaded, using the [SentencePiece package](https://github.com/google/sentencepiece). WikiNLP will automatically make a 5M corpus out of your data and train on it. Wordpiece tokenizers split your data into a fixed number of so-called *wordpieces*, which may correspond to entire words or subword units. While the process is not morphologically motivated, it has the advantage of being applicable to any language you choose, regardless of its morphological complexity. It also means you end up with a fixed-size vocabulary. Because of these advantages, wordpiece tokenizers are frequently used in modern machine learning applications. 

```
from wikinlp.trainspm import SPMTrainer

lang = 'en'

print("Running TrainSPM")
trainspm = SPMTrainer(lang,8000) #vocab of 8000 subwords
trainspm.train_sentencepiece()
```

Your SentencePiece model and vocabulary are then stored in the *spm* directory of your installation. You can apply them to any new text. For instance, assuming a string *doc* containing the text to be tokenized, you can do:

```
import sentencepiece as spm

model_path = './spm/en/enwiki.8k.2023-11-17.model' #the path of your pretrained model
doc = "This is a test sentence."

sp = spm.SentencePieceProcessor()
sp.load(model_path)
spmdoc = ' '.join([wp for wp in sp.encode_as_pieces(doc)])+'\n'
print(spmdoc)

```


## Training a word vector model for the SentencePiece vocabulary

Once you have a preprocessed Wiki dump and a SentencePiece model trained on that dump, you can compute a word vector space for each word piece in your model and perform similarity computations over that space. The WikiNLP module uses [FastText](https://github.com/facebookresearch/fastText) by default for the vector space construction. Here is some example code, which first loads a previously trained SentencePiece model, applies it to the wiki data that was originally downloaded, and uses the tokenized corpus to train a vector space.

```
from wikinlp.trainds import DSTrainer
from wikinlp.trainspm import SPMTrainer

lang = 'en'
vocab_size = 8000
spm_model_path= './spm/en/enwiki.8k.2023-11-17.model'

print("Generating SPM corpus")
trainspm = SPMTrainer(lang,vocab_size,spm_model_path)
trainspm.apply_sentencepiece()

print("Running FastText")
trainds = DSTrainer(lang, spm_model_path)
trainds.train_fasttext(corpus_size=100000000)
nns = trainds.compute_nns(top_words=100)
for word,ns in nns.items():
    print(word,':',' '.join(ns))
```

In case you have previously trained the vector space and simply want to retrieve the nearest neighbours, you can load the trained model this way:

```
trainds = DSTrainer(lang)
trainds.model_path = "./ds/en/enwiki.8k.2023-11-17.cs100m.ft"
nns = trainds.compute_nns(top_words=10000)
for word,ns in nns.items():
    print(word,':',' '.join(ns))
```


