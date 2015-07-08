#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Compares texts with the classifier.
#

import pickle
import kyotocabinet as kc
import kyotocabinetutil as kc_util

from Stemmer import Stemmer
from collections import Counter
from math import sqrt, log
from nltk.corpus import stopwords
import time

import re
SPLIT_TEXT = re.compile(r'\w+')

import logging
if __name__ == "__main__":
    format_str = "%(asctime)s %(levelname)s %(funcName)s: %(message)s"
    logging.basicConfig(format=format_str, level=logging.DEBUG)

from settings import DICTIONARY_DB_FILENAME, \
        VECTOR_DB_FILENAME, VECTORS_NORM_DB_FILENAME, \
        CLASSIFIER_STATE_FILENAME, K_ITEM, MIN_COS_SINE

class CleanTextUtil:
    """ Utility for cleaning text by using stop words and stemming.
 
    Examples:
    >>> c = CleanTextUtil("french")
    >>> c.stem_words([u"Nous", u"allions", u"à", u"la", u"plage"])
    [u'Nous', u'allion', u'à', u'la', u'plag']
    >>> c.rm_stop_words([u"Nous", u"allions", u"à", u"la", u"plage"])
    [u'Nous', u'allions', u'plage']
    >>> c.clean_text(u"Nous allions à la plage")
    [u'allion', u'plag']

    Attributes:
        stemmer (Stemmer.Stemmer): The stemmer delegate object.
        stopwords (list of str): A list of stopwords.

    """
    def __init__(self, language):
        """ Initializes attributes with the language provided.

        Args:
            language (str): The language used to stem ('french', 'english').

        """
        self.stemmer = Stemmer(language)
        self.stopwords = stopwords.words(language)
    
    def stem_words(self, words):
        """ Stems a list of words.

        Args:
            words (list of str): A list of words.

        Returns:
            list of str: The list updated with stem words.

        """
        return self.stemmer.stemWords(words)
    
    def rm_stop_words(self, words):
        """ Removes stop words from a list of words.

        Args:
            words (list of str): A list of words.

        Returns:
            list of str: The list minus the stop words.

        """
        return [word for word in words if word.lower() not in self.stopwords]

    def clean_text(self, text):
        """ Cleans a text to optimize search engines. 
        
        Step of the cleaning: 
            1. Transform all characters to lowercase letters.
            2. Find all word with the regular expression "\w+".
            3. Remove stop words with a filter.
            4. Stem the rest of words.

        Args:
            text (str): A text.

        Returns:
            list of str: The list of words transformed.

        """
        words = SPLIT_TEXT.findall(text.lower())
        words = self.rm_stop_words(words)
        words = self.stem_words(words)
        return words


class WordInfo:
    """ A word info object contains information about a word.

    The object is stored in the main dictionary of words.
    The 'number' variable is update with the method Classifier.add_text.
    The 'idf' is set with the method Classifier.add_idf.  

    Attributes:
        word (str): The word as a simple string.
        index (int): The index of the word in the dictionary.
        number (int): The occurrence of the word in a text, defaults is 1.
        idf (float): The inverse document frequency (idf), defaults is 0.0.

    """
    def __init__(self, word, index):
        """ Sets the word and his index.

        Args:
            word (str): The word as a simple string.
            index (int): Index of the word in the dictionary.

        """
        self.word = word
        self.index = index
        self.number = 1
        self.idf = 0.0
        
    def __str__(self):
        return (
               "word      : %s\n"
               "index     : %s\n"
               "number    : %s\n"
               "idf       : %s" % \
           (self.word, self.index, self.number, self.idf))


class Vector:
    """ A vector object representing a vector with items. 

    Attributes:
        items (list of VectorItem): The list of vector items.
        tag (str): The tag of the vector.

    """
    def __init__(self, items, tag):
        """ Initializes all variables of the object.

        Args:
            items (list of VectorItem): The list of vector items.
            tag (str): The tag of the vector.

        """
        self.items = items
        self.tag = tag


class VectorItem:
    """ A vector item object containing word information used for comparisons.

    The object is an item of a list called a vector.

    Attributes:
        word (str): The word as a simple string.
        tf (float): The term frequency (tf) of the word.

    """
    def __init__(self, word, tf):
        """ Initializes all variables of the object.

        Args:
            word (str): The word as a simple string.
            tf (float): The term frequency of the word.

        """
        self.word = word
        self.tf = tf

    def printer(self, dictionary_db):
        """ Prints the object information like __str__ does.

        Args:
            dictionary_db (kyotocabinet.DB): The dictionary database.

        Returns:
            str: The string representation of the object.

        """
        tf = "tf        : %s" % self.tf
        # insert the tf line before the idf
        s = self.word_info(dictionary_db).__str__().split("\n")
        r = s[:3] + [tf] + [s[-1]]
        return "\n".join(r)
    
    def word_info(self, dictionary_db):
        """ Returns a word info object linked to this vector item.

        Args:
            dictionary_db (kyotocabinet.DB): The dictionary database.

        Returns:
            WordInfo: The word info object from the dictionary database.

        """
        return pickle.loads(dictionary_db.get(self.word))


class Classifier:
    """ The class contains useful methods for comparing text.
    
    Step to follow to start:
    - add text to the dictionary (add_text())
    - evaluate the idf (add_idf()) 
    
    Examples:
    >>> c = CleanTextUtil("french")
    >>> classifier = Classifier(c)
    >>> s1 = u"J'ai : voiture, maison, camion, chanson"
    >>> s2 = u"Il est impossible de venir en voiture"
    >>> s3 = u"il prend la voiture, pour sa maison, avec un camion en chanson"
    >>> s4 = u"Il manque du pain et du chocolat, je vais au magasin"
    >>> classifier.add_text(s1)
    >>> classifier.add_text(s2)
    >>> classifier.add_text(s3)
    >>> classifier.add_text(s4)
    >>> classifier.set_idf()
    >>> classifier.set_tfidf_norm()
    
    Step to follow to use vectors and the cosine similarity:
    - add vector with a name an text (add_vector())
    - compare vector for the cosine_sim similarity (cosine_sim())

    Examples:
    >>> classifier.add_vector("vecteur_1", s1)
    >>> classifier.add_vector("vecteur_2", s2)
    >>> classifier.cosine_sim("vecteur_1", "vecteur_2")
    cosine_sim vecteur_1 vecteur_2 0.03

    There are three database using the Kyoto Cabinet module.
    A database is a simple file containing records, each is a pair of a key and a value.
    (http://fallabs.com/kyotocabinet/)

    More about the databases (with key/value):
    - A dictionary containing words information.
     - the key is a word 
     - the value is a WordInfo object serialized.

    - Multiple vectors of text.
     - the key is the name of a vector
     - the value is a serialized list of VectorItem.

    - Multiple vectors norm.
     - the key is the name of a vector.
     - the value is a vector norm as string.

    - State of the classifier.
     - the key is a variable to store.
     - the value is the value of the variable.

    Attributes:
        clean_text_util (CleanTextUtil): The CleanTextUtil object used to transformed words.
        dictionary_db (kyotocabinet.DB): A dictionary containing words information.
        vectors_db (kyotocabinet.DB): Multiple vectors of text.
        vectors_norm_db (kyotocabinet.DB): Multiple vectors norm.
        classifier_state_db (kyotocabinet.DB): State of the classifier.
        word_index (int): Number of words in the dictionary (defaults is the number of words).
    
    """
    def __init__(self, clean_text_util):
        """ Open or create three databases and set the provided cleaner object.
        
        Args:
            clean_text_util (CleanTextUtil): The CleanTextUtil object used to transformed words.

        """
        self.clean_text_util = clean_text_util

        self.dictionary_db = kc.DB()
        self.dictionary_db.open(DICTIONARY_DB_FILENAME, 
                          kc.DB.OWRITER | kc.DB.OCREATE)
        
        self.vectors_db = kc.DB()
        self.vectors_db.open(VECTOR_DB_FILENAME, 
                            kc.DB.OWRITER | kc.DB.OCREATE)
        
        self.vectors_norm_db = kc.DB()
        self.vectors_norm_db.open(VECTORS_NORM_DB_FILENAME, 
                            kc.DB.OWRITER | kc.DB.OCREATE)

        self.classifier_state_db = kc.DB()
        self.classifier_state_db.open(CLASSIFIER_STATE_FILENAME, 
                            kc.DB.OWRITER | kc.DB.OCREATE)

        # set the total number of documents in the corpus
        if not self.classifier_state_db.get("text_nb"): 
            self.classifier_state_db.add("text_nb", "0") 

        # Current number of words in the dictionary
        self.word_index = len(self.dictionary_db)
        
    def add_text(self, text):
        """ Adds a new text to the dictionary.
        
        Args:
            text (str): A text to feed the dictionary.

        """
        words = self.clean_text_util.clean_text(text)
        # remove duplicate word
        words = set(words) 

        # for each word:
        # - if the word already exist in the dictionary we update the occurrence
        # - otherwise we add a new word with his index to the dictionary 
        for word in words:
            word_info_pickle = self.dictionary_db.get(word)
            if word_info_pickle:
                word_info = pickle.loads(word_info_pickle)
                word_info.number += 1
                self.dictionary_db.replace(word, pickle.dumps(word_info))

            else:
                new_word_info = WordInfo(word, self.word_index)
                self.dictionary_db.add(word, pickle.dumps(new_word_info))
                self.word_index += 1
        
        text_nb = int(self.classifier_state_db.get("text_nb"))
        text_nb += 1
        self.classifier_state_db.replace("text_nb", str(text_nb)) 
    
    def set_idf(self):
        """ Updates by adding the inverse document frequency (idf) for each word.

        """
        for word, word_info in kc_util.gen_db(self.dictionary_db.cursor()):
            word_info.idf = self.idf(word_info.number)
            self.dictionary_db.replace(word, pickle.dumps(word_info))

    def set_tfidf_norm(self):
        """ Updates vectors tf-idf norm.
        
        The idf is the inverse document frequency.

        """
        for name, vector in self.get_vectors():
            norm = self.vector_tfidf_norm(vector.items)
            self.vectors_norm_db.replace(name, norm)
 
    def add_vector(self, name, text, tag=None):
        """ Adds a new vector of words to the database.  
        
        Args:
            name (str): The name of the vector.
            text (str): The text of the vector.
            tag (str, optional): The tag/category.
        
        """
        words = self.clean_text_util.clean_text(text)
     
        # max{f(w,d) : w ∈ d)}
        counter = Counter(words)
        _, max_occ = counter.most_common(1)[0] 

        # remove duplicate word
        words = set(words)
        
        items = []
        for word in words:
            pickle_wordinfo = self.dictionary_db.get(word)
            if not pickle_wordinfo:
                continue
            
            word_info = pickle.loads(pickle_wordinfo)

            # tf formula: tf(f,d) = f(f,d)/max{f(w,d) : w ∈ d)} (src Wikipedia)
            tf = counter[word]/float(max_occ)

            # create a new vector item entry
            items.append(VectorItem(word, tf))

        # sort the vector item by the dictionary index
        items.sort(key=lambda x: x.word_info(self.dictionary_db).index)

        # finally, we create a new vector
        vector = Vector(items, tag)
        self.vectors_db.add(name, pickle.dumps(vector))

        # add an empty entry to the norm db
        self.vectors_norm_db.add(name, self.vector_tfidf_norm(items))

    def rm_vector(self, name):
        """ Removes a vector of words from the database.

        Args:
            name (str): The name of the vector.

        """
        logging.debug("Remove vector %s" % name)
        self.vectors_db.remove(name)
        self.vectors_norm_db.remove(name)

    def update_vector_tag(self, u_name, tag):
        """ Updates a vector's tag.

        Args:
            u_name (str): Name of the vector.
            tag (str): Category/tag of the vector.
        
        """
        vector = self.get_vector(u_name)
        vector.tag = tag
        self.vectors_db.replace(u_name, pickle.dumps(vector)) 

    ###########################################################################
    # Getter
    ###########################################################################

    def get_vector(self, u_name):
        """ Gets a vector from his name.

        Args:
            u_name (str): Name of the vector.

        Returns:
            Vector: The vector instance.

        """
        try:
            return pickle.loads(self.vectors_db.get(u_name))
        except TypeError as er:
            logging.debug("%s not exists" % u_name)
            return

    def get_vectors(self):
        """ Returns the vectors.

        Yields:
            tuple (str, Vector): Name of the vector and vector object. 

        """
        return kc_util.gen_db(self.vectors_db.cursor())
    
    def get_vectors_name(self):
        """ Returns vector's names.

        Returns:
            list of str: A list of names.

        """
        vectors_name = []
        for name, feed in self.get_vectors():
            vectors_name.append(name)
        return vectors_name

    ###########################################################################
    # Math
    ###########################################################################

    def idf(self, occ_in_docs):
        """ Returns the inverse document frequency (idf).
        
        The formula is: idf(t, D) = log(N / |{d ∈ D : t ∈ d}|) (src Wikipedia)
        N: total number of documents in the corpus.
        (provided with the variable self.text_nb)
        |{d ∈ D : t ∈ d}: number of documents where t appears.
        (provided with the variable occ_in_docs)

        Args:
            occ_in_docs (int): number of documents where a word appears.

        Returns:
            float: The idf.

        """
        text_nb = int(self.classifier_state_db.get("text_nb"))
        return log(text_nb / float(occ_in_docs))

    def tf_idf(self, vector_item):
        """ Returns the tf-idf of the vector item.

        The formula is: tf-idf = tf * idf.
        The tf is store in the provided vector_item and idf is store in the dictionary.
        Remember that a vector_item contains a word, and this word is also in the dictionary with his idf.
        
        Args:
            vector_item (VectorItem): The vector item to calculate the tf-idf.

        Returns:
            float: The tf-idf evaluated.

        """
        return vector_item.tf * vector_item.word_info(self.dictionary_db).idf
    
    def vector_tfidf_norm(self, u):
        """ Returns the tf-idf norm of the vector.
        
        The formula is: |u| = √(tfidf_1² + ... + tfidf_n²)
        Each tf-idf item of the vector is evaluated.

        Args:
            u (list of VectorItem): The vector to work with.

        Returns:
            float: The tf-idf norm calculated.

        """
        return sqrt(sum( [self.tf_idf(item)**2 for item in u] ))
    
    def scalar_product(self, u, v):
        """ Returns the tf-idf scalar product of two sparse vectors.
        
        The vector should be sorted by his word index according to increasing values of the key (from low to high values).
        The complexity is O(len(u)+len(v)) in the worst case.
        
        Args:
            u (list of VectorItem): The u vector.
            v (list of VectorItem): The v vector.

        Returns:
            float: The tf-idf scalar product.

        """
        sp = 0.0
        n1 = len(u)
        n2 = len(v)
        i = j = 0
        d = self.dictionary_db
        while (i < n1 and j < n2):
            if u[i].word_info(d).index > v[j].word_info(d).index:
                j += 1
            elif v[j].word_info(d).index > u[i].word_info(d).index:
                i += 1
            else:
                sp += self.tf_idf(u[i]) * self.tf_idf(v[j])
                i += 1
                j += 1

        return sp

    def cosine_sim(self, u_name, v_name):
        """ Returns the cosine similarity of the angle between vectors u and v.
        
        The formula is: cosine_sim = u.v / |u||v|.

        Args:
            u_name (str): The u vector name.
            v_name (str): The v vector name.

        Returns:
            float: The cosine_sim calculated.

        """
        u_vector = self.get_vector(u_name)
        v_vector = self.get_vector(v_name)
        u_norm = self.vectors_norm_db.get(u_name)
        v_norm = self.vectors_norm_db.get(v_name)

        numerator = self.scalar_product(u_vector.items, v_vector.items)
        denominator = float(u_norm) * float(v_norm)
        
        try:
            # round the cosine similarity two digits after the decimal point 
            cosine = round(numerator / denominator, 2)
        except ZeroDivisionError:
            logging.error("division by zero for %s and %s !" \
                    % (u_name, v_name))
            cosine = 0
        
        logging.debug("%s %s = %s " \
                % (u_name, v_name, cosine))
        
        return cosine

    def kNN(self, u_eval, v_compares):
        """ returns the k-NN neighbor classification with the cosinus similarity.

        Build a list of tuples with the tag and the cosine similarity.

        Args:
            u_eval (str): The u vector name to evaluate.
            v_compares (list of str): List of vector name to compare.

        Returns:
            list of tuples (tag, sim): A list of K-Nearest neighbors.

        """
        max_sim = [] # [(tag, sim) ... ]

        for v_comp in v_compares:
            cosine_sim = self.cosine_sim(u_eval, v_comp)

            if cosine_sim > MIN_COS_SINE:
                # add vector tag and cos sim: (tag, sim)
                max_sim.append((self.get_vector(v_comp).tag, cosine_sim))

        # sort cosine similarity
        # [('SPORT', 0.2), ('ART', 0.60), ('ART', 0.13)]
        # [('ART', 0.13), ('SPORT', 0.2), ('ART', 0.60)]
        max_sim.sort(key=lambda tag_nb: tag_nb[1]) 

        # return the k-nearest neighbor only
        # [('ART', 0.13), ('SPORT', 0.2), ('ART', 0.60)]
        # if K_ITEM = 2 
        # [('SPORT', 0.2), ('ART', 0.60)]
        return max_sim[-K_ITEM:]

    def eval_category(self, u_eval, v_compares):
        """ Returns the categorie/tag of a vector.

        The category provided can be from a feed item or just a feed.

        This method use de the KNN classification and search the most common tag. 
        After that, the cosinus similarity is evaluated with the average of the tag.

        Args:
            u_eval (str): The u vector name to evaluate.
            v_compares (list of str): List of vector name to compare.

        Returns:
            tuple (tag, average): The tag and the cosinus similarity average.

        """
        # get cosinus sim with k-NN
        # cos_sim_results = [(tag, cos_sim) ... ] 
        cos_sim_results = self.kNN(u_eval, v_compares)

        # found the most common tag
        c = Counter([tag for tag, _ in cos_sim_results])
        try:
            tag, number = c.most_common(1)[0]
        except IndexError: # No result (cos_sim_results is empty)
            logging.error("No results for %s %s" % (u_eval, cos_sim_results))
            return

        # get the cosinus similarity average for the founded tag
        average = 0.0
        for _tag, _number in cos_sim_results:
            if _tag == tag:
                average += _number
        average /= number

        logging.debug("%s common tag %s (nb %s) (av %s)" % \
                (u_eval, tag, number, average))

        return tag, average

    ###########################################################################
    # Print 
    ###########################################################################
            
    def print_words_structure(self):
        """ Prints content of the main dictionary.
        
        """
        print("Dictionary words:")
        for _, word in kc_util.gen_db(self.dictionary_db.cursor()):
            print(word) 
            print("")

    def print_vector(self, name, items=None):
        """ Prints content of a vector.

        Args:
            name (str): Name of the vector.
            items (list of VectorItem, optional): Items to print.

        """
        print("* Vector name: %s" % name)
        for item in items or self.get_vector(name).items:
            print(item.printer(self.dictionary_db))
            print("")

    def print_vectors(self):
        """ Prints content of all vector.
        
        """
        print("Vectors:")
        for name, vector in self.get_vectors():
            self.print_vector(name, vector.items)

###########################################################################
# CleanTextUtil Example
###########################################################################

if __name__ == "__main__":
    ctu = CleanTextUtil("french")
    
    def clean_text_util_example():
        l = [u"Nous", u"allions", u"à", u"la", u"plage"]
        print(ctu.stem_words(l))
        print(ctu.rm_stop_words(l))
        print(ctu.clean_text(u"Nous allions à la plage"))
    
    clean_text_util_example()

###########################################################################
# WordInfo Example
###########################################################################

if __name__ == "__main__":
    wi = WordInfo("damien", "12")
    print(wi)

###########################################################################
# Vector Example
###########################################################################

if __name__ == "__main__":
    vi_1 = VectorItem("damien", "1")
    vi_2 = VectorItem("ludovic", "0.5")
    v = Vector([vi_1,vi_2], "SPORT")

###########################################################################
# VectorItem Example
###########################################################################

if __name__ == "__main__":
    vi = VectorItem("damien", "1")

###########################################################################
# Classifier Example
###########################################################################

if __name__ == "__main__":
    c = CleanTextUtil("french")
    classifier = Classifier(c)

    flux1_text = (
        u"Comment Google classe les pages Internet"
        u"Bientôt une sphère pour remplacer souris et écrans tactiles ?"
        u"Le clip kitsch du couple présidentiel chinois"
    )
        
    flux2_text = (
        u"Les armes de collection d'Alain Delon vendues aux enchères"
        u"L'une des épouses du chef de l'EI arrêtée au Liban"
        u"Danone et PepsiCo dans le collimateur de Moscou"
        u"Onze morts dans de nouvelles intempéries au Maroc"
    )
    
    flux3_text = (
        u"Le Congrès contre la fermeture de Guantanamo"
        u"Netflix annonce la 3e saison de « House of Cards »"
        u"L'OMS revoit le bilan du virus Ebola à la baisse"
        u"Littérature jeunesse : pas moins de pages, mais plus de coloriages"
        u"Ukraine : accord de cessez-le-feu à Lougansk"
    )

    v1, v2, v3 = "vecteur_1", "vecteur_2", "vecteur_3"    

    def add_texts_test(): 
        classifier.add_text(flux1_text)
        classifier.add_text(flux2_text)
        classifier.add_text(flux3_text)

    def add_vectors_test():
        classifier.add_vector(v1, flux1_text)
        classifier.add_vector(v2, flux2_text)
        classifier.add_vector(v3, flux3_text)

    def rm_vector_test():
        classifier.rm_vector(v1)
        classifier.rm_vector(v2)
        classifier.rm_vector(v3)

    def set_idf_all_test():
        classifier.set_idf()
        classifier.set_tfidf_norm()

    def print_words_test():
        classifier.print_words_structure()

    def print_vectors_test():
        classifier.print_vectors()
        
    def print_consine_test():
        a = classifier.cosine_sim(v1, v1)
        b = classifier.cosine_sim(v1, v2)
        c = classifier.cosine_sim(v1, v3)

        logging.info("cosine_sim v1 v1: %s" % a)
        logging.info("cosine_sim v1 v2: %s" % b)
        logging.info("cosine_sim v1 v3: %s" % c)

    ## add texts
    add_texts_test()
    add_vectors_test()
    set_idf_all_test()
    # just for the display
    time.sleep(5)
    print_words_test()
    time.sleep(5)
    print_vectors_test()
    time.sleep(5)
    print_consine_test()
    time.sleep(5) 
    rm_vector_test()
    ##

# see the src/manager.py for more
