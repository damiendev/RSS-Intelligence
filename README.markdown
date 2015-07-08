RSS-Intelligence
=========

RSS-Intelligence is a project for collecting, classifying and indexing RSS feeds.


Collector
-------

The first class proposes methods for adding, updating and removing RSS feeds.
A feed is identified by his name, and he has an url and a simple tag.

```python
>>> name = "lemonde.fr"
>>> url = "http://www.lemonde.fr/sante/rss_full.xml"
>>> tag = "SANTE"
>>> collector = Collector()
>>> collector.add_feed(name,tag,url)
True
>>> collector.update_feed(name)
False
>>> collector.print_items(name)
    title       : Travailler en horaires décalés accélère le vieillissement cognitif
    published   : Tue, 04 Nov 2014 02:19:30 GMT
    ...
>>> collector.rm_feed(name)
True
```

When a feed is added, all of its items are downloaded and stored. The data structure is maintained with only relevant attributes like the language and the abstract of the item.  


#### Structure of a feed

| Attribute                         | Description                          |
| :---------------------------------| :------------------------------------|
| name (str)                        | Name of the feed                     |
| item_db_filename (str)            | Name of the linked database of items |
| url (str)                         | Url of the feed server               |
| tag (str)                         | Tag chosen                           |
| etag (unicode)                    | Unique tag provided by the feed server|
| modified (str)                    | Date provided by the feed server      |
        

####  Structure of an item


| Attribute                         | Description                          |
| :---------------------------------|:-------------------------------------|
| id (int)                          | Id of the item.                  |
| title (unicode)                   | Title of the item.               	   |
| webpage url (unicode)             | Url of the linked web page.          |
| webpage text (str)                | Text extracted from the web page.    |
| published date (unicode)          | Date of the publication.             |
| abstract (unicode)                | Abstract about the item.             |
| language (str)                    | Language of the item.                |
| tag (str)                         | Category/Tag of the item.            |


Classifier
----------

The classifier contains useful methods for comparing texts.
Text are added to a dictionary in order to create a corpus of words.
After that, we can add vectors of text and calculate the cosine similarity between vectors.

```python
>>> c = CleanTextUtil("french")
>>> classifier = Classifier(c)
>>> s1 = u"J'ai : voiture, maison, camion, chanson"
>>> s2 = u"Il est impossible de venir en voiture"
>>> s3 = u"il prend la voiture, pour sa maison, avec un camion en chanson"
>>> s4 = u"Il manque du pain et du chocolat, je vais au magasin"

# add text to the dictionary 
>>> classifier.add_text(s1)
>>> classifier.add_text(s2)
>>> classifier.add_text(s3)
>>> classifier.add_text(s4)

# add the inverse document frequency (idf) for each word
>>> classifier.set_idf()
# add the term frequency–inverse document frequency (tfidf) norm
>>> classifier.set_tfidf_norm()

# add vectors of text
>>> classifier.add_vector("vecteur_1", s1)
>>> classifier.add_vector("vecteur_2", s2)

# get the cosine similarity of the angle between two vectors
>>> classifier.cosine_sim("vecteur_1", "vecteur_2")
cosine_sim vecteur_1 vecteur_2 0.03
```

Manager
---------- 

The manager class manages the collector and the classifier.
We can populate the database with some feeds.
Each item of a feed is added with the category (tag) like sport or business of the feed.

With the cosine similarity, we can add a  new feed and automatically found the tags of his items.

```python
manager = Manager(Collector(), Classifier(CleanTextUtil("english")))

# fill the database with feeds and vectors
manager.add_feeds()
manager.add_texts_vectors()

# add a general feed without tags
name, url = "ccn_edition", "http://rss.cnn.com/rss/edition_us.rss"
manager.add_general_feed(name, url)
```

Indexer
----------

With the Indexer we can search information in a collection of feeds.
The feeds are added from the collector and stored with the Whoosh library.

```python
c = Collector()
indexer = Indexer(c)

# fill the indexer with feeds
manager = Manager(c, Classifier(CleanTextUtil("french")))
manager.add_feeds()
indexer.add_feeds()

# print random items
feeds = Manager.get_feeds_info()
name,_,_,_, = random.choice(feeds)
c.print_items(name)

# do some researchs
indexer.search_feeds("title", "ump")
indexer.search_feeds("title", "ps")
indexer.search_feeds("abstract", "victoire")
indexer.search_feeds("language", "french")
indexer.search_feeds("url", "lemonde.fr")
indexer.search_feeds("text", "Suisses")

# launch the prompt
indexer.prompt()
```


#### Simple prompt
An interactive prompt proposes queries with the field of items of feeds.

The syntax is:  ACTION FIELD QUERY.
```bash
ACTION: "search" or "remove".
FIELD: "title", "published", "abstract", "id", "webpage_url", "text", "language", "tag", "predite".
QUERY: a simple string.
```

##### Example:

```bash
(linux_env) $  python src/indexer.py
Enter a query (ACTION FIELD KEYWORD):search title Museum
title       : Pegasus, a Tugboat and Floating Museum, Hits Rough Waters
published   : Fri, 03 Jul 2015 21:00:05 GMT
abstract    : Pamela Hepburn, the captain of the Pegasus, said she hoped to have the boat operating this summer, but its operators no longer have the money to maintain it.
id          : 6251228271491271676
webpage url : http://rss.nytimes.com/c/34625/f/640316/s/47d27353/sc/31/l/0L0Snytimes0N0C20A150C0A70C0A40Cnyregion0Cpegasus0Ea0Etugboat0Eand0Emuseum0Emay0Edisappear0Efrom0Enew0Eyorks0Ewaterways0Bhtml0Dpartner0Frss0Gemc0Frss/story01.htm
language    : english
tag         : 
predite     : 
-----------
title       : Museum tackles its moth problem by turning males gay
published   : Wed, 17 Jun 2015 00:01:00 GMT
abstract    : The Natural History Museum has turned to gender warfare to combat legions of moths that were munching their way through...
id          : 9135035375853241822
webpage url : http://www.thetimes.co.uk/tto/science/article4471869.ece
language    : english
tag         : 
predite     : 
-----------
About 2 results.
```


Getting Started
-----------------
#### 1- Install Python 2.7 and Kyoto-Cabinet

#### 2- Prepare the python virtual environment  
 Launch install.sh
```bash
$ ./install.sh
```
The script:
 - creates a virtual environment;
 - downloads python modules.

#### 3- Add a list of stop words
Download stop words with the command below or use the provided "nltk_data" directory.
```python
>>> nltk.download()
``` 

The resource can be stored in:
```bash
- /$HOME/
- /usr/share/
- /usr/local/share/
- /usr/lib/
- /usr/local/lib/
```

for example you can move the directory to your home:
```bash
$ mv nltk_data $HOME 
```
After installation
-----------------

#### 1- Activate the virtual environment

To begin using the virtual environment, it needs to be activated.

```bash
$ source linux_env/bin/activate
```
If you are done working in the virtual environment for the moment, you can desactivate it.
```bash
$ deactivate
```

#### 2- Launch python scripts
```bash
(linux_env)$ python src/classifier.py
(linux_env)$ python src/collector.py
(linux_env)$ python src/indexer.py
(linux_env)$ python src/manager.py
(linux_env)$ python src/test.py
```

Testing
-----------------

The test script offer options to test each class with the python unit testing framework.

```bash
usage: src/test.py [OPTIONS]

OPTIONS: 
        --all    Test all classes of the project.

        --Collector       Test the Collector class.
        --Feed            Test the Feed class.
        --Item            Test the Item class.
        --CleanTextUtil   Test the CleanTextUtil class.
        --WordInfo        Test the WordInfo class.
        --Vector          Test the Vector class.
        --VectorItem      Test the VectorItem class.
        --Classifier      Test the Classifier class.
        --Manager         Test the Manager class.
        --Indexer         Test the Indexer class.
```


Project Structure
-----------------

```
.
├── install.sh
├── LICENSE.txt
├── nltk_data
│   └── corpora
├── README.markdown
├── resources
│   └── urls.txt
└── src
    ├── classifier.py
    ├── collector.py
    ├── indexer.py
    ├── kyotocabinetopt.py
    ├── manager.py
    ├── settings.py
    └── test.py
```

The resources/urls.txt file contains a list of sample RSS feeds.
A work directory (work_dir) is created when the python scripts are used. 
During the installation, the directory "linux_env" will be added.



Maintainers
-----------------
 - Damien Roualen <[damien.roualen@gmail.com](mailto:damien.roualen@gmail.com)>

