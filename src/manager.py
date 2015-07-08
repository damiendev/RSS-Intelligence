#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Manages the Collector and the Classifier.
#

from collections import Counter

from collector import Collector, Feed, Item
from classifier import Classifier, CleanTextUtil, WordInfo, Vector, VectorItem

from settings import URLS_FILE

import logging
if __name__ == "__main__":
    format_str = "%(asctime)s %(levelname)s %(funcName)s: %(message)s"
    logging.basicConfig(format=format_str, level=logging.DEBUG)

class Manager():
    """ Manages the Collector and the Classifier.
    
    Attributes:
        collector (Collector): Instance of the Collector.
        classifier (Classifier): Instance of the Classifier.

    """
    def __init__(self, collector, classifier):
        """ Sets the feed manager and the classifier.

        Args:
            collector (Collector): Instance of the Collector.
            classifier (Classifier): Instance of the Classifier.

        """
        self.collector = collector
        self.classifier = classifier

    def add_feeds(self):
        """ Populates the feed manager with some feeds.

        Name, url and tag are extracted from the file at "$URLS_FILE".

        """
        for name, url, tag, _ in self.get_feeds_info():
            self.collector.add_feed(name, url, tag) 

    def add_texts_vectors(self):
        """ Populates the classifier with texts and vectors.

        Information is extracted from the feed manager.

        """
        for name, feed in self.collector.get_feeds():
            text = [text for _, text in self.collector.get_text_from_items(name)]
            feed_text = "".join(text)
            self.classifier.add_text(feed_text)
            self.classifier.add_vector(name, feed_text, feed.tag)

            logging.debug('vector added %s %s ' % (name, feed.tag))

        self.classifier.set_idf()
        self.classifier.set_tfidf_norm()

    def add_general_feed(self, name, url):
        """ Adds a general feed to the feed manager with unspecified categories.

        The category is added automatically for each item 
        and the average category in set to the feed.

        Args:
            name (str): Name of the feed.
            url (str): The feed url.

        Returns:
            Feed: The new feed is returned.

        """
        feed = self.collector.add_feed(name, url)

        # get all present vectors name
        v_compares = self.classifier.get_vectors_name()

        tags = []

        for item, text in self.collector.get_text_from_items(name):
            # create a new name for the vector item
            # vector name = feed name + item id
            u_evaluate = "%s_%s" % (name, item.id)

            # add the vector to the classifier
            self.classifier.add_vector(u_evaluate, text) 

            # get category of the item 
            tag_av = self.classifier.eval_category(u_evaluate, v_compares) 
            if not tag_av:
                # remove the vector
                # useless if there is not tag 
                self.classifier.rm_vector(u_evaluate)

                continue

            #TODO do something with the average
            tag, __average__not_used__ = tag_av
            tags.append(tag)

            # update the item with the category
            self.classifier.update_vector_tag(u_evaluate, tag)
            self.collector.update_item_tag(feed.item_db_filename, item.id, tag)

            logging.info("item %s added with category %s" % (u_evaluate, tag)) 

        tag, _ = Counter(tags).most_common(1)[0]
        self.collector.update_feed_tag(name, tag)
        logging.info("set a general category %s for %s" % (tag, name)) 

        return feed

    def remove_feed(self, name):
        """ Removes a vector and a feed.

        The vector is removed from the classifier.
        The feed is removed from the feed manager.

        Args:
            name (str): Name of the feed to removed.

        """
        self.classifier.rm_vector(name) 
        self.collector.rm_feed(name)

    ###########################################################################
    # Getter
    ###########################################################################

    @staticmethod
    def get_feeds_info():
        """ Get information to populate the Collector.

        Each line of the file is a new feed to parse.
    
        File structure: 
        TAG URL LANGUAGE

        File example:
        SANTE http://www.lemonde.fr/sante/rss_full.xml FR
        SPORT http://rss.nytimes.com/services/xml/rss/nyt/Sports.xml EN

        The Feed is represented by a tuple with:
         - name (str): Name of the feed.
         - url (str): Url of the feed.
         - tag (str): The tag attached.
         - language (str): The language of the feed.

        Returns:
            list of tuple: Return a list with feed information.

        """
        infos = []

        with open(URLS_FILE) as f:
            lines = f.readlines()

        for line in lines:
            item = line.split(" ")
            if (item[0].startswith("#") or len(item) < 2):
                continue
            
            # unpack and sort variables 
            tag, name, url, language = item
            infos.append((name, url, tag, language))

        return infos


if __name__ == "__main__":
    manager = Manager(Collector(), Classifier(CleanTextUtil("english")))
    
    ## add feeds and vectors
    manager.add_feeds()
    manager.add_texts_vectors()
    ##

    ## add a general feed (you can change the name and the url)
    name, url = "ccn_edition", "http://rss.cnn.com/rss/edition_us.rss"
    manager.add_general_feed(name, url)
    ##

    ## uncomment to remove the feed
    #manager.remove_feed(name)
    ##

