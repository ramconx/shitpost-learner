#!/usr/bin/env python3

import json
import os
import pickle
import re
import sys
import urllib.error
import urllib.request

from pymarkovchain import MarkovChain
from random import randint

html_rep = {
    '&amp;' : '&',
    '&quot;' : '"',
    '&#039;' : "'",
    '&gt;' : '>',
    '&lt;' : '<'
}

def sanitize( com ):
    retval = re.sub( r'\<.+\>', '', com )
    
    for sym in html_rep:
        retval = retval.replace( sym, html_rep[sym] )
    
    return retval

def thread_prop( images, board, thread_id ):
    retval = u''
    
    try:
        response = urllib.request.urlopen( 'http://a.4cdn.org/' + board + '/thread/' + str( thread_id ) + '.json' )
    except ( urllib.error.HTTPError ):
        return retval
    
    data = json.loads( response.read().decode('utf-8') )

    for post in data['posts']:
        if 'com' in post:
            sanitized = sanitize( post['com'] )
            retval += u' {}'.format( sanitized )
        
        if 'filename' in post:
            images.append( str( post['tim'] ) + post['ext'] )
    
    return retval

def analyze_board( mc, board ):
    train_string = u''
    images = []

    print( 'Training... (may take a while)' )
    
    response = urllib.request.urlopen( 'http://a.4cdn.org/' + board + '/threads.json' )
    data = json.loads( response.read().decode('utf-8') )

    for page in data:
        for thread in page['threads']:
            train_string += thread_prop( images, board, thread['no'] )

    mc.generateDatabase( train_string )

    # Save database and images so we can load them later without rebuilding
    mc.dumpdb()
    
    with open('./data/{}-images'.format( board ), 'wb') as db_file:
        pickle.dump( images, db_file )

    return images

def load_or_train_board( board ):
    mc_path = './data/{}-data'.format( board )
    images_path = './data/{}-images'.format( board )

    mc = MarkovChain( mc_path )
    
    if not os.path.isfile( mc_path ) or not os.path.isfile( images_path ):
        images = analyze_board( mc, board )
    else:
        with open( images_path, 'rb' ) as images_file:
            images = pickle.load( images_file )

    return mc, images

def shitpost_loop( mc, images, board ):
    read = ''
    image_grab = lambda : 'http://i.4cdn.org/' + board + '/' + images[randint( 0, len( images ) )]
    
    print( 'Hit enter to generate a shitpost, or enter ? for a list of valid commands.' )

    while read != 'exit':
        read = input()

        if read == '?':
            print( 'Hit enter to generate a shitpost.' )
            print( "Enter 'exit' to exit the program." )
            print( "Enter 'train' to re-train the shitposter (this takes a while)." )
            print( "Enter 'board <board>' to switch to a different board (this takes a while)." )
        elif read == 'train':
            images = analyze_board( mc, board )
            print( 'Re-training complete.' )
        elif read == 'exit':
            pass
        elif read.startswith( 'board' ):
            try:
                board = read.split()[1].replace( '/', '' )
            except ( IndexError ):
                print( 'No board specified.' )
                continue

            try:
                urllib.request.urlopen( 'http://a.4cdn.org/' + board + '/threads.json' )
            except ( urllib.error.HTTPError ):
                print( 'Invalid board.' )
                continue

            mc, images = load_or_train_board( board )
            print( 'Switched to /{}/.'.format( board ) )
        elif read:
            print( 'Invalid input.' )
        else:
            image = image_grab()
            shitpost = mc.generateString()

            print( image )
            print( u'>{}'.format( shitpost ) )

def main( args ):
    board = ''

    print( 'Enter the name of the board you would like to learn how to shitpost from.' )
    print( 'Ex. /a/, /fit/, /tv/, etc.' )

    while not board:
        board = input().replace( '/', '' )

        try:
            urllib.request.urlopen( 'http://a.4cdn.org/' + board + '/threads.json' )
        except ( urllib.error.HTTPError ):
            print( "Invalid board - try again." )
            board = ''

    mc, images = load_or_train_board( board )
    shitpost_loop( mc, images, board )

if __name__ == '__main__':
    main( sys.argv[1:] )

