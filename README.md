# WikiLoader

This module lets you download and preprocess Wikipedia in some language of your choice. Additionally, it offers options for training basic NLP tools on your Wikipedia snapshot. At the moment, the following are offered:

* training a SentencePiece model;
* training a distributional semantic space;

Please check the language code for your Wikipedia: it is the prefix to your Wikipedia url. For instance, The English Wikipedia is at *https://en.wikipedia.org/* so its language code is *en*. The Hindi Wikipedia is at *https://hi.wikipedia.org/*, so its language code is *hi*.


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

## Training a SentencePiece model

You can train a SentencePiece model on the Wiki data you have downloaded. WikiLoader will automatically make a 5M corpus out of your data and train on it.

```
from trainspm.trainspm import TrainSPM

lang = 'en'

print("Running TrainSPM")
trainspm = TrainSPM(lang)
trainspm.train_sentencepiece()
```

In case you would like to train SentencePiece on a specific file of your choice, you can provide its path:

```
from trainspm.trainspm import TrainSPM

lang = 'en'

print("Running TrainSPM")
trainspm.train_sentencepiece(data_path='data/en/enwiki-latest-pages-articles1.xml-p1p41242.raw.txt')
```
