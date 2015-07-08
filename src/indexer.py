#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Searches information in a collection of feeds.
#

import os, shutil
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, NUMERIC, TEXT, KEYWORD
from whoosh.qparser import QueryParser
from collector import Collector, Collector, Feed, Item

from settings import INDEX_DIR

import logging
if __name__ == "__main__":
    format_str = "%(asctime)s %(levelname)s %(funcName)s: %(message)s"
    logging.basicConfig(format=format_str, level=logging.DEBUG)

SCHEMA = Schema(
    # item attributes
    item_id=NUMERIC(stored=True),
    title=TEXT(stored=True), \
    webpage_url=TEXT(stored=True), \
    text=TEXT, \
    published=TEXT(stored=True), \
    abstract=TEXT(stored=True), \
    language=TEXT(stored=True), \
    # feed attribute
    tag=KEYWORD(stored=True), \
    predite=KEYWORD(stored=True))

class Indexer:
    """ Searches information in a collection of feeds.

    A field of an RSS item can be stored or just indexed. 
    When stored, the field is returned with the results.

    Attributes:
        collector (Collector): A Collector instance.

    """
    def __init__(self, collector):
        """ Initializes the class by preparing the index object.

        Args:
            collector (Collector): A Collector instance.

        """
        self.collector = collector

        if not os.path.exists(INDEX_DIR):
            os.makedirs(INDEX_DIR)
            # create a new index
            self.ix = create_in(INDEX_DIR, SCHEMA)
            logging.info("create index directory at %s" % INDEX_DIR)
        else:
            # open last index 
            self.ix = open_dir(INDEX_DIR)

    def add_feed(self, name):
        """ Indexing an RSS feed by adding all items to the index.
        
        Args:
            name (str): Name of the feed.

        """
        logging.debug('index feed "%s"' % name)
        with self.ix.writer() as w:
            for item_id, item in self.collector.get_items(name):
                logging.debug('add item "%s" to the index.' % item.title)
                w.add_document(
                    item_id=item_id,
                    title=item.title,
                    webpage_url=item.webpage_url,
                    text=item.webpage_text,
                    published=item.published_date,
                    abstract=item.abstract,
                    language=item.language,
                    tag=hasattr(item, "tag") and unicode(item.tag) or u"",
                    predite=u"")

    def add_feeds(self):
        """ Indexing all RSS feeds by adding all items to the index.
        
        """
        for name, _ in self.collector.get_feeds():
            self.add_feed(name)

    def rm_feed(self, field, keyword, print_search=True):
        """ Deletes any documents matching the query.

        The results are printed on the screen.

        Args:
            field (str): The RSS item field to search.
            keyword (str): The keyword used for the query.
            print_search (boolean, optional): Enable to print the search.

        """
        query = self.__query(field, keyword)

        if print_search:
            self.search_feeds(field, keyword, query)

        with self.ix.writer() as w:
            nb_deleted = w.delete_by_query(query)

            if nb_deleted:
                logging.info('%s item%s deleted' % \
                        (nb_deleted, (nb_deleted>1) and "s" or ""))

            else:
                logging.info('Nothing deleted.')

    def search_feeds(self, field, keyword, query=None):
        """ Searching the index with a specific keyword and field.

        The results are printed on the screen.

        Args:
            field (str): The RSS item field to search.
            keyword (str): The keyword used for the query.
            keyword (str): The keyword used for the query.
            query (whoosh.query.query, optional): The query object.

        """
        query = query or self.__query(field, keyword)

        with self.ix.searcher() as s:
            results = s.search(query)
            self.__print_result(results)

    def __query(self, field, keyword):
        """ Prepares a query with a specific keyword and field.

        Args:
            field (str): The RSS item field to search.
            keyword (str): The keyword used for the query.

        Returns:
            whoosh.query.query: The query object.

        """
        qp = QueryParser(field, self.ix.schema)
        return qp.parse(keyword)

    def __print_result(self, results):
        """ Prints result of the search.
        
        Args:
            item_dict (list of str): A list of RSS items.

        """
        s = ( 
        "title       : %s\n"
        "published   : %s\n"
        "abstract    : %s\n"
        "id          : %s\n"
        "webpage url : %s\n"
        "language    : %s\n"
        "tag         : %s\n"
        "predite     : %s")

        if not results:
            print("No result.")
            return

        for result in results:
            print(s % ( 
                result['title'], result['published'],
                result['abstract'], result['item_id'],
                result['webpage_url'], result['language'],
                result['tag'], result['predite'])).encode("utf-8", "remplace")
            print("-----------")

        l = len(results)
        print("About %s result%s." % \
               (l, (l>1) and "s" or ""))

    def prompt(self):
        """ A simple prompt for the search.

        """
        s = "Enter a query (ACTION FIELD KEYWORD):"
        while True:
            try:
                query = raw_input(s).split(" ")
                if query > 0 and query[0] == "exit": 
                    return
                if query >= 3:
                    query_str = " ".join(query[2:])
                    if query[0] == "search":
                        self.search_feeds(query[1], query_str)
                    elif query[0] == "remove":
                        self.rm_feed(query[1], query_str)
            except Exception as er:
                logging.debug(er)

###########################################################################
# Indexer Example
###########################################################################

if __name__ == "__main__":
    def reset():
        try:
            shutil.rmtree(INDEX_DIR)
        except Exception:
            pass

    from collector import Collector, Feed, Item
    from classifier import Classifier, CleanTextUtil, WordInfo, Vector, VectorItem
    from manager import Manager
    import random

    ## uncomment this line to reset the index dir
    #reset() 

    c = Collector()
    indexer = Indexer(c)

    ## populate the indexer with feeds
    # Download feeds first 
    manager = Manager(c, Classifier(CleanTextUtil("english")))
    manager.add_feeds()

    #
    # Next, index feeds
    indexer.add_feeds()
    ##

    # print to help for the search
    def print_random_feed_items_test():
        feeds = Manager.get_feeds_info()
        name, _,_,_, = random.choice(feeds)
        c.print_items(name)

    print_random_feed_items_test()

    ##  active interactive prompt
    #   the syntax is ACTION FIELD QUERY
    #   ACTION method are:
    #   - search
    #   - remove
    #   FIELD are:
    #   - title
    #   - published
    #   - abstract
    #   - id   
    #   - webpage_url
    #   - text
    #   - language
    #   - tag
    #   - predite
    #   QUERY is a string with two quote
    #   example:
    #   > search title "Contre-choc pétrolier"
    #   > remove title "Contre-choc pétrolier"
    #   > search title "Contre-choc pétrolier"
    #   > search title "deluge"
    ##  write "exit" and press enter to exit
    indexer.prompt()
    ##

    ## exemple of query

    #indexer.search_feeds("title", "ump")
    #indexer.search_feeds("title", "ps")
    #indexer.search_feeds("abstract", "victoire")
    #indexer.search_feeds("language", "french")
    #indexer.search_feeds("url", "lemonde.fr")
    #indexer.search_feeds("text", "Suisses")
    ##

