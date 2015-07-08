#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Collects feeds and save them 
# to the kyoto cabinet database.
#

import pickle
import kyotocabinet as kc
import kyotocabinetutil as kc_util

from boilerpipe.extract import Extractor
from guess_language.guess_language import guessLanguage

import random, string, os, time
import BeautifulSoup
import feedparser

from settings import WORK_DIR, ACTIVE_ACTICLE_EXTRACTOR, \
        FEEDS_DB_FILENAME, DEFAULT_LANGUAGE_CODE

import logging
if __name__ == "__main__":
    format_str = "%(asctime)s %(levelname)s %(funcName)s: %(message)s"
    logging.basicConfig(format=format_str, level=logging.DEBUG)

class Collector:
    """ Add, update, remove and print feeds.

    Examples:
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

    Attributes:
        feeds_db (kyotocabinet.DB): The database of feeds.

    """
    feed_status_ok = [200, 301, 302]

    def __init__(self):
        """ Opens or creates the feeds database.

        """
        self.feeds_db = kc.DB()
        self.feeds_db.open(FEEDS_DB_FILENAME,
                           kc.DB.OWRITER | kc.DB.OCREATE)

    def add_feed(self, name, url, tag=None):
        """ Adds a new feed to the database.
        
        The feed is not added if the feed/name already exists.

        Args:
            name (str): Name of the feed.
            url (str): The feed url.
            tag (str, optional): The tag chosen. 

        Returns:
            Feed: The new feed added.

        """
        if self.has_feed(name):
            logging.info('the feed "%s" already exists' % name)
            return

        try:
            logging.debug("start parsing !")
            feed_parsed = feedparser.parse(url)

            if feed_parsed.status not in self.feed_status_ok:
                logging.error("error status %s for \n(%s)" % \
                             (feed_parsed.status, url))
                return

        except AttributeError as er: 
            # feed_parsed.status can be null 
            # if there is an error with the url
            feed_parsed = None
            if not hasattr(feed_parsed, "status"):
                logging.error("error with the url: %s" % url)
            else:
                logging.error(er)
            return
        except Exception as er:
            logging.error(er)
            return

        # generate a new random feed file name for the database of items
        random_letters = ''.join(random.choice(string.ascii_letters) for _ in range(5))
        file_name = "%s/%s_%s.kct" % (WORK_DIR, name, random_letters)
            
        try:
            items_db = kc.DB() # open or create the Feed database
            items_db.open(file_name, kc.DB.OWRITER | kc.DB.OCREATE)

            # parse each entry by creating a new Item object 
            for entry in reversed(feed_parsed["entries"]):
                item = Item(entry)
                items_db.add(item.id, pickle.dumps(item))
                logging.debug('add item "%s"' % item.title)

        except Exception as er:
            logging.error("error while adding items for %s" % name)
            logging.debug("data keys => %s" % feed_parsed.keys())
            logging.debug("feed keys => %s" % feed_parsed['feed'].keys())
            logging.debug(er)

            items_db.close()

            try: 
                # remove the item database
                os.remove(file_name)
            except OSError as er:
                logging.error("remove db file after an error")
                logging.debug(er)
                 
            return

        items_db.close()

        feed = Feed(name, file_name, url, tag,
                    etag=feed_parsed.get('etag', None), 
                    modified=feed_parsed.get('modified', None))

        self.feeds_db.add(name, pickle.dumps(feed))
        logging.info("feed %s added", name)

        return feed 
        
    def update_feed(self, name):
        """ Updates a feed by adding new items to the actual collection.
        
        Args:
            name (str): Name of the feed.
        
        Returns:
            boolean: True if new items has been added with the update.

        """
        feed = self.get_feed(name)

        try:
            feed_parsed = feedparser.parse(feed.url,
                                           etag=feed.etag, 
                                           modified=feed.modified)

            if feed_parsed.status == 304:
                logging.info('nothing to do, the feed "%s" is up to date' % name)
                return False

        except AttributeError:
            # feed can be None with get_feed() and that is ok
            if feed: 
                # feedparser.parse() can return None too
                logging.error("error with the url: %s" % feed.url)
            return False;
        
        updated=False
        
        try:
            items_db = kc.DB()
            items_db.open(feed.item_db_filename, kc.DB.OWRITER)
            
            for entry in reversed(feed_parsed["entries"]):
                item_id = Item.get_id(entry)

                # add a new item if the id doesn't exists
                if not items_db.get(item_id):
                    updated = True
                    item = Item(entry)
                    self.items_db.append(item)
                    logging.info('add a new item : "%s"' % item.title)

        except Exception as err:
            logging.error(err)

        finally:
            items_db.close()

        return updated

    def rm_feed(self, name):
        """ Removes a feed with his name.

        The feed is removed from the feed and the item database.
        
        Args:
            name (str): Name of the feed.

        Returns:
            boolean: True if the item has been removed.

        """
        feed = self.get_feed(name)
        
        # remove the item database
        try:
            os.remove(feed.item_db_filename)

        except AttributeError as er:   
            # feed can be None with get_feed()
            if feed:
                logging.error(er)
            return False
        except OSError as er:
            # print the error and quit if the file exists
            if os.path.isfile(feed.item_db_filename):
                logging.error(er)
                return False
            logging.debug(er)

        # remove the feed from the feeds database 
        self.feeds_db.remove(name)
        logging.info("feed %s removed", name)

        return True

    def update_feed_tag(self, name, tag):
        """ Updates the category/tag of a feed.

        Args:
            name (str): Name of the feed.
            tag (str): Category/tag of the feed.

        """
        feed = self.get_feed(name)
        feed.tag = tag
        self.feeds_db.replace(name, pickle.dumps(feed))

    def update_item_tag(self, item_db_filename, item_id, tag):
        """ Updates the category/tag of an item.

        Args:
            item_db_filename (str): Name of the items database.
            item_id (int): Id of the item to update.
            tag (str): Category/tag of the item.

        Returns:
            Item: The updated item is returned.

        """
        try:
            items_db = kc.DB()
            items_db.open(item_db_filename, kc.DB.OWRITER)

            item = pickle.loads(items_db.get(item_id))
            item.tag = tag

            items_db.replace(item_id, pickle.dumps(item)) 
        except Exception as er:
            logging.error(er)
        finally:
            items_db.close()

        return item

    def has_feed(self, name):
        """ Returns true or false if the feed exists.

        Args:
            name (str): Name of the feed.

        """
        return bool(self.feeds_db.get(name))

    ###########################################################################
    # Print 
    ###########################################################################

    def print_feed(self, name):
        """ Prints feed information.

        Args:
            name (str): Name of the feed.

        """
        print("Feed %s:" % name)
        print(self.get_feed(name))

    def print_feeds(self):
        """ Prints all feeds information.

        """
        print("Feeds:")
        for _, feed in self.get_feeds():
            print(feed)
            print("")

    def print_items(self, name):
        """ Prints items of a specific feed.

        Args:
            name (str): Name of the feed.

        """
        print("Items of %s:" % name)
        for _, item in self.get_items(name):
            print(item)
            print("")

    ###########################################################################
    # Getter
    ###########################################################################

    def get_text_from_items(self, name):
        """ Returns a generator of texts from items.

        The title, abstract and webpage text are extracted.

        Args:
            name (str): Name of the feed.

        Yields:
            tuple (Item, str): A generator of tuples.

        """
        for _, item in self.get_items(name):
            text = item.title+" "
            text += item.abstract+" "
            text += item.webpage_text+" "
            yield item, unicode(text)

    def get_feed(self, name):
        """ Retrieves a feed from his name.

        The feed object is retrieve from the feeds database.

        Args:
            name (str): Name of the feed.

        Returns:
            Feed: a feed object.

        """
        pickle_feed = self.feeds_db.get(name)
        try:
            return pickle.loads(pickle_feed)

        except TypeError:
            logging.info('the feed with the name "%s" doesn\'t exists' % name)
            return None

    def get_feeds(self):
        """ Returns feeds with the generator.

        Yields:
            tuple (str, Feed): A generator of tuple (feed name, feed obj).

        """
        try:
            for feed in kc_util.gen_db(self.feeds_db.cursor()):
                yield feed

        except Exception as er:
            logging.error(er)

    def get_items(self, name):
        """ Returns feed's items with the generator.
        
        Args:
            name (str): Name of the feed.

        Yields:
            tuple (str, Item): A generator of tuple (item id, item obj).

        """
        feed = self.get_feed(name)

        try:
            items_db = kc.DB()
            items_db.open(feed.item_db_filename, kc.DB.OREADER)

            for item in kc_util.gen_db(items_db.cursor()):
                yield item

        except AttributeError as er:   
            # feed can be None
            if feed:
                logging.error(er)

        except Exception as er:
            logging.error(er)
            
        finally:
            items_db.close()

    
class Feed:
    """ A feed contains all information about a specific feed.  
    
    The purpose of this class is to be stored in a main database of feeds.
    A feed is linked to a database of items, with the item database filename.
    
    A feed has a tag which can be science, business, sport...
    
    Also, this class contains information about the feed server:
     - the state of the server with the field 'etag' and 'modified'.
     - the url of the feed server.

    Attributes:
        name (str): Name of the feed.
        item_db_filename (str): Name of the linked database of items.
        url (str): Url of the feed server.
        tag (str): Tag chosen.
        etag (unicode): Unique tag provided by the feed server.
        modified (str): Date provided by the feed server.
    
    """
    def __init__(self, name, item_db_filename, url, tag, etag=None, modified=None):
        """ Set information about items and the state of the feed server.

        Args:
            name (str): Name of the feed.
            item_db_filename (str): Name of the linked database of items.
            url (str): Url of the feed server.
            tag (str): Tag chosen.
            etag (unicode, optional): Unique tag provided by the feed server, defaults to None.
            modified (str, optional): Date provided by the feed server, defaults to None.

        """
        self.name = name
        self.item_db_filename = item_db_filename
        self.url = url
        self.tag = tag
        self.etag = etag
        self.modified = modified

    def __str__(self):
        return (
            "item db file: %s\n"
            "url         : %s\n"
            "tag         : %s\n"
            "etag        : %s\n"
            "modified    : %s" % (
                self.item_db_filename,
                self.url, self.tag,
                self.etag or "",
                self.modified or ""))


class Item:
    """ An Item encapsulate information about a specific feed item.

    Attributes:
        id (int): The id of the item.
        title (unicode): Title of the item.
        webpage_url (unicode): Url of the linked web page.
        webpage_text (str): Text extracted from the web page.
        published_date (unicode): Date of the publication.
        abstract (unicode): Abstract about the item.
        language (str): Language of the item.
        tag (str): Category/Tag of the item.

    The tag is not set from the contrustor but with the method "update_item_tag".

    """
    language_code = {"fr": u"french", "en":u"english"}
    
    def __init__(self, item_data):
        """ Populates variables by parsing a provided dictionary.

        Args:
            item_data (feedparser.FeedParserDict): A dictionary full of item information.

        """
        abstract = BeautifulSoup.BeautifulSoup(item_data["summary"]).text
        language = guessLanguage(abstract) or item_data["title_detail"]["language"] 
        
        try:
            self.language = self.language_code[language]
        except KeyError:
            self.language = self.language_code[DEFAULT_LANGUAGE_CODE]
            logging.warning('language code "%s" not in the list: %s.' %
                          (language, ", ".join(self.language_code)))
            logging.warning('the abstract was: %s' % abstract)
            logging.warning('continue with the default language "%s"' % self.language)
                
        self.webpage_url = item_data["link"]
        self.published_date = item_data["published"]
        self.title = item_data["title"]
        self.abstract = abstract

        # hash from the title and the feed url
        self.id = Item.get_id(item_data)
        
        self.webpage_text = u""
        if ACTIVE_ACTICLE_EXTRACTOR:
            try:
                # extract the text of the linked web page. 
                extractor = Extractor(extractor='ArticleExtractor', url=self.webpage_url)
                self.webpage_text = extractor.getText()
            except Exception as er:
                logging.warning("can't extract the article")
                logging.warning('url was "%s"'%self.webpage_url)
                logging.debug(er)
    
    def __str__(self):
        s = (
        "title       : %s\n"
        "published   : %s\n"
        "abstract    : %s\n"
        "id          : %s\n"
        "webpage url : %s\n"
        "webpage txt : %s\n"
        "language    : %s" % (
                self.title, self.published_date,
                self.abstract, self.id, 
                self.webpage_url, 
                self.webpage_text[:200]+"...",
                self.language))

        if hasattr(self, "tag"):
            s += "\ncategorie   : %s" % self.tag

        return s.encode("utf-8", "remplace")
    
    @staticmethod
    def get_id(item_data):
        """ Generates an id by hashing the title and the feed url.
        
        Example of id: 6409141534996688640 (always unsigned)

        Args:
            item_data (feedparser.FeedParserDict): A dictionary full of item information.
            
        Returns:
            int: the hash.

        """
        return abs(hash(item_data["title"]+item_data["title_detail"]["base"]))

        
###########################################################################
# Collector Example
###########################################################################

if __name__ == "__main__":
    from manager import Manager
    feeds = Manager.get_feeds_info()
    collector = Collector()
    
    def add_feeds_test():
        logging.info("add feeds")
        for name, url, tag, _ in feeds:
            collector.add_feed(name, url, tag)
            
    def update_feeds_test():
        logging.info("update feeds")
        for name, _,_,_ in feeds:
            collector.update_feed(name)

    def rm_feeds_test():
        logging.info("remove feeds")
        for name, _,_,_ in feeds:
            collector.rm_feed(name)
            
    def print_random_feed_items_test():
        logging.info("print random feed")
        name, _,_,_, = random.choice(feeds)
        collector.print_feed(name)
        # just for the display
        time.sleep(5) 
        print("")
        collector.print_items(name)

    ##
    # uncomment this lines to test the collector
    ##
    rm_feeds_test()
    #time.sleep(10) # just for the display
    add_feeds_test()
    time.sleep(10)
    #update_feeds_test()
    #time.sleep(10)
    print_random_feed_items_test()
    rm_feeds_test()
    ##

