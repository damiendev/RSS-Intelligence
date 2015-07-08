#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Main settings.
#

import os
def create(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

RESOURCES_DIR = "resources"
WORK_DIR = create("work_dir")

###########################################################################
# Collector 
###########################################################################

# because extracting article is slow 
# sometime, is useful to deactivate this function
ACTIVE_ACTICLE_EXTRACTOR = False

FEEDS_DB_FILENAME = "%s/Feeds.kct"%WORK_DIR
DEFAULT_LANGUAGE_CODE = "fr"

###########################################################################
# Classifier
###########################################################################

DICTIONARY_DB_FILENAME = "%s/Dictionary.kct"%WORK_DIR
VECTOR_DB_FILENAME = "%s/Vectors.kct"%WORK_DIR
VECTORS_NORM_DB_FILENAME = "%s/VectorsNorm.kct"%WORK_DIR
CLASSIFIER_STATE_FILENAME = "%s/ClassifierState.kct"%WORK_DIR

K_ITEM = 5 # size of the k-nearest neighbor
MIN_COS_SINE = 0.1 # min cosine of the neighbor

###########################################################################
# Manager
###########################################################################

URLS_FILE = "%s/urls.txt"%RESOURCES_DIR

###########################################################################
# Indexer 
###########################################################################

INDEX_DIR="%s/index_dir"%WORK_DIR


