#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Kyoto cabinet util.
#

import pickle

def gen_db(cursor):
    """ Returns a generator of items from a kyoto cabinet database.
    
    Return tuples with:
    - name of the entry
    - object stored for the entry. 
    
    Args:
        cursor (kyotocabinet.cursor): The cursor of the db.

    Yields:
        tuple (str, obj): A generator of tuples.

    """
    cursor.jump()
            
    while True:
        rec = cursor.get(True)
        if not rec: 
            break

        yield rec[0], pickle.loads(rec[1])
