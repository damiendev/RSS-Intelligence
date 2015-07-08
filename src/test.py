#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Tests the classes with the Python unit testing framework.
#

import unittest
import os, glob, shutil

import settings
from collector import Collector, Feed, Item
from classifier import CleanTextUtil, WordInfo, Vector, VectorItem, Classifier
from manager import Manager
import indexer as ind

import kyotocabinetutil as kc_util
import feedparser

from settings import WORK_DIR
def rm_data_dir():
    try:
        for f in glob.glob("%s/*" % WORK_DIR):
            if os.path.isfile(f):
                os.remove(f)
            else:
                shutil.rmtree(f)
    except Exception as er:
        print(er)

###########################################################################
# Collector Test 
###########################################################################

class TestCollector(unittest.TestCase):
    """ Tests the Collector class.

    """
    def setUp(self):
        self.co = Collector()
        self.feed_info = Manager.get_feeds_info()

    def tearDown(self):
        rm_data_dir()

    def test_add_feed(self):
        """ Tests add_feed.

        Add feeds with "add_feed":
         1- Test if the feeds has been added.
         2- Test if the feeds exists in the database.

        Try adding a feed already added: 
         3- Test if the feed has not been added.

        """
        for name, url, tag, _ in self.feed_info:
            feed = self.co.add_feed(name, url, tag)
            self.assertIsNotNone(feed) # 1
            self.assertTrue(self.co.has_feed(name)) # 2

        name, url, tag = self.feed_info[0][:3]
        feed = self.co.add_feed(name, url, tag)
        self.assertIsNone(feed) # 3

    def test_update_feed(self):
        """ Tests update_feed.

        Add feeds.

        Try updating feed with "update_feed":
         1- Test if the feed doesn't need to be updated.

        #TODO
        Find a way to update a feed in the test.

        """
        for name, url, tag, _ in self.feed_info:
            self.co.add_feed(name, url, tag)

            updated = self.co.update_feed(name)
            self.assertFalse(updated) # 1

    def test_rm_feed(self):
        """ Tests rm_feed.

        Add feeds:
         1- Test if the feeds exists first.

        Remove feeds with "rm_feed".
         2- Test if the feeds has been removed.

        """
        for name, url, tag, _ in self.feed_info:
            self.co.add_feed(name, url, tag)

            self.assertTrue(self.co.has_feed(name)) # 1
            self.co.rm_feed(name)
            self.assertFalse(self.co.has_feed(name)) # 2

    def test_update_item_tag(self):
        """ Tests update_item_tag.

        Add a feed:
         1- Test if an item has not the tag attribute.

        Add a category with "update_item_tag".
         2- Test if the item updated is the same with the id.
         3- Test if the item updated has the tag attribute. 
         4- Test if the item updated has the correct category.

        """
        category = "SPORT"

        name, url, tag = self.feed_info[0][:3]
        feed = self.co.add_feed(name, url, tag)
        item_id, item = self.co.get_items(name).next()
        self.assertFalse(hasattr(item, "tag")) # 1

        self.co.update_item_tag(feed.item_db_filename, item_id, category)
        item_id_updated, item_updated = self.co.get_items(name).next()

        self.assertEquals(item_id, item_id_updated) # 2
        self.assertTrue(hasattr(item_updated, "tag")) # 3
        self.assertEquals(item_updated.tag, category) # 4

    def test_has_feed(self):
        """ Tests has_feed.

        Verify with "has_feed" if the feed exists.
         1- The feed doesn't exists.

        Add a feed.

        Verify with "has_feed" if the feed exists.
         2- The feed exists.

        """
        name, url, tag = self.feed_info[0][:3]

        self.assertFalse(self.co.has_feed(name)) # 1
        self.co.add_feed(name, url, tag)
        self.assertTrue(self.co.has_feed(name)) # 2

    def test_print_feed(self):
        """ Tests print_feed.

        Add a feed.
        Print the feed.

        """
        name, url, tag = self.feed_info[0][:3]
        self.co.add_feed(name, url, tag)

        self.co.print_feed(name)

    def test_print_feeds(self):
        """ Tests print_feeds.

        Add feeds.
        print feeds.

        """
        for name, url, tag, _ in self.feed_info:
            self.co.add_feed(name, url, tag)

        self.co.print_feeds()

    def test_print_items(self):
        """ Tests print_items.

        Add a feed.
        Print items.

        """
        name, url, tag = self.feed_info[0][:3]
        self.co.add_feed(name, url, tag)

        self.co.print_items(name)

    def test_get_text_from_items(self):
        """ Tests get_text_from_items.

        Add a feed.

        For each item with "get_text_from_items" verify if: 
         1- the title is in the text.
         2- the abstract is in the text.
         3- the webpage text is in the text.

        """
        name, url, tag = self.feed_info[0][:3]
        self.co.add_feed(name, url, tag)

        for item, text in self.co.get_text_from_items(name):
            self.assertIn(item.title, text) # 1
            self.assertIn(item.abstract, text) # 2
            self.assertIn(item.webpage_text, text) # 3

    def test_get_feed(self):
        """ Tests get_feed.

        1,2- Test if get_feed retrieves the correct feed by comparing name. 
        3- Test if get_feed retrieve None for an unknown feed.

        """
        name_1, url, tag, _ = self.feed_info[0]
        feed_1_added = self.co.add_feed(name_1, url, tag)
        name_2, url, tag, _ = self.feed_info[1]
        feed_2_added = self.co.add_feed(name_2, url, tag)

        feed_1_get = self.co.get_feed(name_1)
        self.assertEquals(feed_1_get.name, feed_1_added.name) # 1

        feed_2_get = self.co.get_feed(name_2)
        self.assertNotEquals(feed_2_get.name, feed_1_added.name) # 2

        unknown_feed = self.co.get_feed("unknown feed")
        self.assertIsNone(unknown_feed) # 3

    def test_get_feeds(self):
        """ Tests get_feeds.

        Add feeds.

        Get feeds and:
         1- Comparing feed name from the data base with original feeds.
         2- Comparing feed name from feeds with original feeds.
         3- Verify if feeds name from the db are equals to feeds obj name attribute. 
             (1, 2 is not enough for that because the order is not preserved)

        """
        feeds_name = []
        for name, url, tag, _ in self.feed_info:
            self.co.add_feed(name, url, tag)
            feeds_name.append(name)

        feeds_name = set(feeds_name)
        feeds_name_1 = set([name for name, _ in self.co.get_feeds()])
        self.assertEquals(feeds_name, feeds_name_1) # 1

        feeds_name_2 = set([feed.name for _, feed in self.co.get_feeds()])
        self.assertEquals(feeds_name, feeds_name_2) # 2

        for name, feed in self.co.get_feeds():
            self.assertEquals(name, feed.name) # 3

    def test_get_items(self):
        """ Tests get_items.
        
        Add a feed.

        Get the first item:
         1- Verify if the item is not None.

        Get all items:
         2- Verify if the id from the db are equals to the item id attribute.

        """
        name, url, tag, _ = self.feed_info[0]
        feed = self.co.add_feed(name, url, tag)

        item_id, item = self.co.get_items(name).next()
        self.assertIsNotNone(item) # 1

        for item_id, item in self.co.get_items(name):
            self.assertEquals(item_id, str(item.id)) # 2


class TestFeed(unittest.TestCase):
    """ Tests the Feed class.

    """
    def setUp(self):
        feed_info = Manager.get_feeds_info()
        self.name, self.url, self.tag, _ = feed_info[0]

    def tearDown(self):
        rm_data_dir()

    def test___init__(self):
        """ Tests the constructor.

        Create a new Feed instance.
         1- Verify if there is an instance.

        """
        feed = Feed(self.name, "lemonde_sante_ZhxYv.kct", self.url, self.tag,
                    etag="128732871823", 
                    modified="2014-12-06 13:25:12,432")

        self.assertIsNotNone(feed) # 1

    def test___str__(self):
        """ Tests the print method.

        Create a new feed.
        Print the feed.

        """
        feed = Feed(self.name, "lemonde_sante_ZhxYv.kct", self.url, self.tag,
                    etag="128732871823", 
                    modified="2014-12-06 13:25:12,432")

        print(feed)


class TestItem(unittest.TestCase):
    """ Tests the Item class.

    """
    def setUp(self):
        feed_info = Manager.get_feeds_info()
        _, url, _, _ = feed_info[0]
        feed_parsed = feedparser.parse(url)

        self.item_entry = feed_parsed["entries"][0]

    def tearDown(self):
        rm_data_dir()

    def test___init__(self):
        """ Tests the constructor.

        Create a new Item instance.
         1- Verify if there is an instance.

        """
        item = Item(self.item_entry)
        self.assertIsNotNone(item) # 1

    def test___str__(self):
        """ Tests the print method.

        Create a new item.
        Print the item.

        """
        item = Item(self.item_entry)
        print (item)

    def test_get_id(self):
        """ Tests get_id.

        Get id:
         1- Verify in the id is an integer.
         2- Compare two id for the same data.

        """
        item_data = {"title":"lemonde", 
                "title_detail": {"base":"www.lemonde.fr"}}
        item_id = Item.get_id(item_data)

        self.assertIsInstance(item_id, int) # 1

        item_id_ = Item.get_id(item_data)
        self.assertEquals(item_id, item_id_) # 2


###########################################################################
# Classifier Test 
###########################################################################

class TestCleanTextUtil(unittest.TestCase):
    """ Tests the CleanTextUtil class.

    """
    def setUp(self):
        self.ctu = CleanTextUtil("french")
        self.words = [u"Nous", u"allions", u"à", u"la", u"plage"]

    def tearDown(self):
        rm_data_dir()

    def test_stem_words(self):
        """ Tests stem_words.   

        1- Verify is the result is correct.
        from [u"Nous", u"allions", u"à", u"la", u"plage"]
        to [u"Nous", u"allion", u"à", u"la", u"plag"]

        """
        wanted = [u"Nous", u"allion", u"à", u"la", u"plag"]

        get = self.ctu.stem_words(self.words)
        self.assertEquals(get, wanted) # 1

    def test_rm_stop_words(self):
        """ Tests rm_stop_words.

        1- Verify is the result is correct.
        from [u"Nous", u"allions", u"à", u"la", u"plage"]
        to [u"allions", u"plage"]

        """
        wanted = [u"allions", u"plage"]

        get = self.ctu.rm_stop_words(self.words)
        self.assertEquals(get, wanted) # 1

    def test_clean_text(self):
        """ Tests clean_text.

        1- Verify is the result is correct.
        from "Nous allions à la plage"
        to ["allion", "plag"]

        """
        wanted = ["allion", "plag"]

        get = self.ctu.clean_text(" ".join(self.words))
        self.assertEquals(get, wanted) # 1

class TestWordInfo(unittest.TestCase):
    """ Tests the WordInfo class.

    """
    def test___init__(self):
        """ Tests the constructor.

        Create a new WordInfo instance.
         1- Verify if there is an instance.
         2- Verify if the number is equals to 1.
         3- Verify if the idf is equals to 0.0.

        """
        wi = WordInfo("foo", "5")

        self.assertIsNotNone(wi) # 1
        self.assertEquals(wi.number, 1) # 2 
        self.assertEquals(wi.idf, 0.0) # 3

    def test___str__(self):
        """ Tests the print method.

        Create a new word info.
        Print the word info.

        """
        wi = WordInfo("plage", "1")
        print(wi)

class TestVector(unittest.TestCase):
    """ Tests the Vector class.

    """
    def test___init__(self):
        """ Test the constructor.

        Create a new Vector instance.
         1- Verify if there is an instance.

        """
        v = Vector([], "BUSINESS")
        self.assertIsNotNone(v) # 1

class TestVectorItem(unittest.TestCase):
    """ Tests the VectorItem class.

    """
    def setUp(self):
        text = u"Comment Google classe les pages Internet"

        c = Classifier(CleanTextUtil("french"))
        c.add_text(text)

        self.dictionary_db = c.dictionary_db
        self.vi = VectorItem("googl", "1")

    def tearDown(self):
        rm_data_dir()

    def test_printer(self):
        """ Tests printer.

        Create a new vector item with a word of the text.
        print the vector.

        """
        print(self.vi.printer(self.dictionary_db))

    def test_word_info(self):
        """ Tests word_info.

        Create a new vector item with a word of the text.
        Call word_info with the dictionary db:
         1- Verify the result object is a WordInfo object.  

        """
        word_info = self.vi.word_info(self.dictionary_db)
        self.assertIsInstance(word_info, WordInfo) # 1

class TestClassifier(unittest.TestCase):
    """ Tests the Classifier class.

    """
    def setUp(self):
        self.c = Classifier(CleanTextUtil("french"))

    def tearDown(self):
        rm_data_dir()

    def test_add_text(self):
        """ Tests add_text.

        Add a text to the classifier:
         1- Verify if the number of text equals 1.
         2- Verify if the text added is equals to words wanted.

        """
        flux1_text = (
            u"Comment Google classe les pages Internet "
            u"Bientôt une sphère pour remplacer souris et écrans tactiles ? "
            u"Le clip kitsch du couple présidentiel chinois"
        )

        flux1_text_wanted = [
            "bient", "chinois", "class", "clip", "comment", "coupl", 
            "cran", "googl", "internet", "kitsch", "le", "pag", "pr", 
            "re", "remplac", "sidentiel", "sour", "sph", "tactil"
        ]

        self.c.add_text(flux1_text)

        self.assertEquals(int(self.c.classifier_state_db.get("text_nb")), 1) # 1

        words = [word for word, _ in kc_util.gen_db(self.c.dictionary_db.cursor())]
        self.assertEquals(words, flux1_text_wanted) # 2

    def test_set_idf(self):
        """ Tests set_idf.

        Add two texts:
         1- Verify idf equals 0.0

        Add idf:
         2- Verify idf not equals 0.0

        """
        self.c.add_text("foo")
        self.c.add_text("bar") # important for idf

        _, word_info = kc_util.gen_db(self.c.dictionary_db.cursor()).next()
        self.assertEquals(word_info.idf, 0.0) # 1

        self.c.set_idf()

        _, word_info = kc_util.gen_db(self.c.dictionary_db.cursor()).next()
        self.assertNotEquals(word_info.idf, 0.0) # 2

    def test_set_idf_tfidf_norm(self):
        """ Tests set_idf_tfidf_norm.

        Add two texts:
         1- Verify idf equals 0.0
         2- Verify idf norm equals '0.0'

        Update idf:
         2- Verify idf not equals 0.0
         3- Verify idf norm not equals '0.0'

        """
        text, vector_1 = "foo", "foo_1"
        self.c.add_text(text)
        self.c.add_text("bar") # important for idf

        _, word_info = kc_util.gen_db(self.c.dictionary_db.cursor()).next()
        self.assertEquals(word_info.idf, 0.0) # 1

        self.c.add_vector(vector_1, text) 

        norm = self.c.vectors_norm_db.get(vector_1)
        self.assertEquals(norm, '0.0') # 2

        self.c.set_idf()

        _, word_info = kc_util.gen_db(self.c.dictionary_db.cursor()).next()
        self.assertNotEquals(word_info.idf, 0.0) # 3

        self.c.set_tfidf_norm()

        norm = self.c.vectors_norm_db.get(vector_1)
        self.assertNotEquals(norm, '0.0') # 4

    def test_add_vector(self):
        """ Tests add_vector.

        Add a text.

        1- Check if there is not a vector.  

        Add a vector:
         2- Check if there is a vector.

        """
        text, vector_1 = "foo", "foo_1"
        self.c.add_text(text)

        vector = self.c.get_vector(vector_1)
        self.assertIsNone(vector) # 1

        self.c.add_vector(vector_1, text) 

        vector = self.c.get_vector(vector_1)
        self.assertIsInstance(vector, Vector) # 2

    def test_rm_vector(self):
        """ Tests rm_vector.

        Add a text.
        Add a vector:
         1- Check if the vector exists.
        Remove the vector:
         2- Check if the vector doesn't exist anymore.

        """
        text, vector_1 = "foo", "foo_1"
        self.c.add_text(text)
        self.c.add_vector(vector_1, text) 

        vector = self.c.get_vector(vector_1)
        self.assertIsNotNone(vector) # 1

        self.c.rm_vector(vector_1)

        vector = self.c.get_vector(vector_1)
        self.assertIsNone(vector) # 2

    def test_get_vector(self):
        """ Tests get_vector.

        Add a text.
        Add a vector.
         1- Check if the vector exists with "get_vector".

        Get an unknown vector.
         2- Check if the vector is None.

        """
        text, vector_1 = "foo", "foo_1"

        self.c.add_text(text)
        self.c.add_vector(vector_1, text) 

        vector = self.c.get_vector(vector_1)
        self.assertIsNotNone(vector) # 1

        vector = self.c.get_vector("unknown vector")
        self.assertIsNone(vector) # 2

    def test_get_vectors(self):
        """ Tests get_vectors.

        Add two texts.
        Add two vectors.

        With get_vectors:
         1- Verify names equals by comparing names.
         2- Verify object equals by comparing tags.

        """
        text_1, vector_1, tag_1 = "foo", "foo_1", "SPORT" 
        text_2, vector_2, tag_2 = "bar", "bar_1", "BUSINESS"

        self.c.add_text(text_1)
        self.c.add_text(text_2)

        self.c.add_vector(vector_1, text_1, tag_1) 
        self.c.add_vector(vector_2, text_2, tag_2) 

        names = [name for name, _ in self.c.get_vectors()] 
        self.assertEquals(set(names), set(self.c.get_vectors_name())) # 1

        tags = [vector.tag for _, vector in self.c.get_vectors()] 
        self.assertEquals(set([tag_1, tag_2]), set(tags)) # 2

    def test_get_vectors_name(self):
        """ Tests get_vectors_name.

        Add two texts.
        Add two vectors.
        Get vectors names:
         1- Verify names equals.

        """
        text_1, vector_1 = "foo", "foo_1"
        text_2, vector_2 = "bar", "bar_1"

        self.c.add_text(text_1)
        self.c.add_text(text_2)

        self.c.add_vector(vector_1, text_1) 
        self.c.add_vector(vector_2, text_2) 

        names = self.c.get_vectors_name()
        self.assertEquals(set([vector_1,vector_2]), set(names)) # 1

    def test_idf(self):
#TODO
        """ Test .

        """
        pass

    def test_tf_idf(self):
        """ Test .

        """
        pass

    def test_vector_tfidf_norm(self):
        """ Test .

        """
        pass

    def test_scalar_product(self):
        """ Test .

        """
        pass

    def test_cosine_sim(self):
        """ Test .

        """
        pass

    def test_kNN(self):
        """ Test .

        """
        pass

    def test_get_category(self):
        """ Test .

        """
        pass

    def test_print_words_structure(self):
        """ Test .

        """
        pass

    def test_print_vector(self):
        """ Test .

        """
        pass

    def test_print_vectors(self):
        """ Test .

        """
        pass

###########################################################################
# Manager Test 
###########################################################################

class TestManager(unittest.TestCase):
    """ Tests the Manager class.

    """
    def setUp(self):
        self.co = Collector()
        self.c = Classifier(CleanTextUtil("french"))
        self.m = Manager(self.co, self.c)
        self.feeds_info = Manager.get_feeds_info()

    def tearDown(self):
        rm_data_dir()

    def test_add_feeds(self):
        """ Tests add_feeds.

        Add feeds.

        For each item with get_feeds_info:
         1- Check if the feed has been added.

        """
        self.m.add_feeds()

        for name, _, _, _ in self.feeds_info:
            self.assertTrue(self.co.has_feed(name)) # 1

    def test_add_texts_vectors(self):
        """ Tests add_texts_vectors.

        Add feeds.
        Add texts vectors:
         1- Check if the dictionary is not empty.
         2- Check if the number of text equals to feeds info.

        """
        self.m.add_feeds()
        self.m.add_texts_vectors()

        self.assertNotEquals(len(self.c.dictionary_db), 0) # 1

        size = len([_ for _, _, _, _ in self.feeds_info])
        self.assertEquals(int(self.c.classifier_state_db.get("text_nb")), size) # 2

    def test_add_general_feed(self):
#TODO
        """ Test .

        """
        pass

    def test_remove_feed(self):
        """ Tests remove_feed .

        Add feeds.
        Add texts vectors:
         1- Check if a feed exists.
         2- Check if a vector exists.

        Remove a feed.
         3- Check if the feed has been removed.
         4- Check if the vector doesn't exist anymore.

        """
        name = self.feeds_info[0][0]
        self.m.add_feeds()
        self.m.add_texts_vectors()

        self.assertTrue(self.co.has_feed(name)) # 1
        self.assertIsNotNone(self.c.get_vector(name)) # 2

        self.m.remove_feed(name)

        self.assertFalse(self.co.has_feed(name)) # 3
        self.assertIsNone(self.c.get_vector(name)) # 4

    def test_get_feeds_info(self):
#TODO
        """ Test .

        """
        pass

###########################################################################
# Indexer Test 
###########################################################################

class TestIndexer(unittest.TestCase):
    """ Tests the indexer class.

    """
    def setUp(self):
        self.co = Collector()
        self.indexer = ind.Indexer(self.co)

    def tearDown(self):
        rm_data_dir()

    def test_add_feed(self):
        """ Tests add_feed. 

        Add a feed to the collector.
        Add a feed to the indexer.

        For each item added:
         1- Check if the webpage url exists in the indexer. 

        """
        name, url, tag, _ = Manager.get_feeds_info()[0]
        self.co.add_feed(name, url, tag)
        self.indexer.add_feed(name)

        for _, item in self.co.get_items(name):
            query = self.indexer._Indexer__query("webpage_url", item.webpage_url)

            with self.indexer.ix.searcher() as s:
                self.assertGreater(len(s.search(query)), 0)

    def test_add_feeds(self):
        """ Tests add_feeds.

        Add feeds to the collector.
        Add feeds to the indexer.

        For each feed added, get the first item:
          1- Check if the webpage url exists in the indexer. 

        """
        for name, url, tag, _ in Manager.get_feeds_info():
            self.co.add_feed(name, url, tag)

        self.indexer.add_feeds()

        for name, _ in self.co.get_feeds():
            _, item = self.co.get_items(name).next()
            query = self.indexer._Indexer__query("webpage_url", item.webpage_url)

            with self.indexer.ix.searcher() as s:
                self.assertEquals(len(s.search(query)), 1)

    def test_rm_feed(self):
        """ Tests rm_feed.

        Add a feed to the collector.
        Add a feed to the indexer.

        Get the first item:
          1- Check if the webpage url exists in the indexer. 

        Remove the feed with the query
          2- Check if the same query retrieves no result.

        """
        name, url, tag, _ = Manager.get_feeds_info()[0]
        self.co.add_feed(name, url, tag)
        self.indexer.add_feed(name)
        _, item = self.co.get_items(name).next()

        field = "webpage_url"
        keyword = item.webpage_url
        
        query = self.indexer._Indexer__query(field, keyword)

        with self.indexer.ix.searcher() as s:
            self.assertEquals(len(s.search(query)), 1) # 1

        self.indexer.rm_feed(field, keyword, print_search=False)

        with self.indexer.ix.searcher() as s:
            self.assertEquals(len(s.search(query)), 0) # 2

    def test_search_feeds(self):
        """ Tests search_feeds.

        Add a feed to the collector.
        Add a feed to the indexer.

        1- Search feeds.
        2- Search feeds by setting a query.
        Result is visual and must be the same.

        """
        name, url, tag, _ = Manager.get_feeds_info()[0]
        self.co.add_feed(name, url, tag)
        self.indexer.add_feed(name)
        _, item = self.co.get_items(name).next()

        field = "webpage_url"
        keyword = item.webpage_url

        self.indexer.search_feeds(field, keyword) # 1

        query = self.indexer._Indexer__query(field, keyword)
        self.indexer.search_feeds(field, keyword, query) # 2

    def test___query(self):
        """ Tests __query.

        Add feeds to the collector.
        Add feeds to the indexer.

        Build a query:
          1- Check if the webpage url exists in the indexer. 

        """
        name, url, tag, _ = Manager.get_feeds_info()[0]
        self.co.add_feed(name, url, tag)
        self.indexer.add_feed(name)
        _, item = self.co.get_items(name).next()

        field = "webpage_url"
        keyword = item.webpage_url

        query = self.indexer._Indexer__query(field, keyword)
        with self.indexer.ix.searcher() as s:
            self.assertEquals(len(s.search(query)), 1) # 1

    def test___print_result(self):
        """ Tests __print_result.

        1- Print a result on the screen.
        2- Print no result on the screen.

        """
        results = [{
    "title":u"Les sodas accéléreraient le vieillissement de l'ADN et des cellules",
    "published":u"Wed Apr 23 9:38:43 CEST 2014",
    "abstract":u"Selon une étude américaine, la consommation de boissons gazeuses sucrées accélérerait le vieillissement de l'ADN et des cellules. Ce qui pourrait avoir des conséquences sur le développement de certaines maladies",
    "item_id":u"2141636843256855236",
    "webpage_url":u"http://www.bfmtv.com/societe/les-sodas-responsables-d-un-vieillissement-accelere-de-l-adn-et-des-cellules-840847.html",
    "language":"french",
    "tag":u"SPORT",
    "predite":u""}]

        self.indexer._Indexer__print_result(results) # 1
        self.indexer._Indexer__print_result([]) # 2

    def test_prompt(self):
        """ Tests the prompt.

        Simulate the "exit" input and quit.

        """
        def mock_raw_input_exit(s):
            return "exit"

        ind.raw_input = mock_raw_input_exit
        indexer = ind.Indexer(self.co)
        indexer.prompt()


class Colors:
    pink = '\033[95m'
    blue = '\033[94m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    endc = '\033[0m'

OPT_ALL = "all  "
OPTS = ["Collector", \
        "Feed", \
        "Item", \
        "CleanTextUtil", \
        "WordInfo", \
        "Vector", \
        "VectorItem", \
        "Classifier", \
        "Manager", \
        "Indexer"]

OPT_ALL_COMMENT = "Test all classes of the project."
OPTS_COMMENT = "Test the %s class."

def usage():
    print('\nusage: %s [%sOPTIONS%s]\n' % \
            (av[0], Colors.green, Colors.endc))
    print('%sOPTIONS: %s' % (Colors.green, Colors.endc))

    p = '%s\t--%s%s  %30s'
    print(p % (Colors.red, OPT_ALL, Colors.endc, OPT_ALL_COMMENT))
    print('')
    for opt in OPTS:
        print(p % (Colors.red, opt, Colors.endc, OPTS_COMMENT % opt))
    print('')

def run_all():
    for opt in OPTS:
        instance = eval("Test%s"%opt)
        c = unittest.TestLoader().loadTestsFromTestCase(instance)
        d = unittest.TextTestRunner(verbosity=2).run(c)
        if d.failures or d.errors:
            break

if __name__ == "__main__":
    import sys, getopt
    av = sys.argv

    try:
        opts, args = getopt.getopt(av[1:], "", [OPT_ALL]+OPTS)

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("--%s"%OPT_ALL):
            run_all()
        else:
            instance = eval("Test%s"%opt[2:])
            c = unittest.TestLoader().loadTestsFromTestCase(instance)
            unittest.TextTestRunner(verbosity=2).run(c)

    if not opts:
        usage()

    #suite = unittest.TestSuite()
    #suite.addTest( TestCollector('test_add_feed') )
    #unittest.TestSuite([suite])
    #unittest.TextTestRunner().run(suite)

    #collector = unittest.TestLoader().loadTestsFromTestCase(TestCollector)
    #unittest.TextTestRunner(verbosity=2).run(collector)

    #feed = unittest.TestLoader().loadTestsFromTestCase(TestFeed)
    #unittest.TextTestRunner(verbosity=2).run(feed)

    #item = unittest.TestLoader().loadTestsFromTestCase(TestItem)
    #unittest.TextTestRunner(verbosity=2).run(item)

    #ctu = unittest.TestLoader().loadTestsFromTestCase(TestCleanTextUtil)
    #unittest.TextTestRunner(verbosity=2).run(ctu)

    #wi = unittest.TestLoader().loadTestsFromTestCase(TestWordInfo)
    #unittest.TextTestRunner(verbosity=2).run(wi)

    #vi = unittest.TestLoader().loadTestsFromTestCase(TestVectorItem)
    #unittest.TextTestRunner(verbosity=2).run(vi)

    #c = unittest.TestLoader().loadTestsFromTestCase(TestClassifier)
    #unittest.TextTestRunner(verbosity=2).run(c)

    #manager = unittest.TestLoader().loadTestsFromTestCase(TestManager)
    #unittest.TextTestRunner(verbosity=2).run(manager)

    #indexer = unittest.TestLoader().loadTestsFromTestCase(TestIndexer)
    #unittest.TextTestRunner(verbosity=2).run(indexer)
