# WikiLoader

This module lets you download and preprocess Wikipedia in some language of your choice. Please check the language code for your Wikipedia: it is the prefix to your Wikipedia url. For instance, The English Wikipedia is at *https://en.wikipedia.org/* so its language code is *en*. The Hindi Wikipedia is at *https://hi.wikipedia.org/*, so its language code is *hi*.


Here is an example usage, which loads and processes the Occitan Wikipedia:

```
from wikitrain.wikiloader import WikiLoader

wikiloader = WikiLoader('oc')
wikiloader.mk_wiki_data()
```

NB: remember that large Wikipedias like English can take several hours to be downloaded and processed, depending on your Internet connection!
