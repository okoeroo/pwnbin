import time
import urllib2
import datetime
import sys, getopt
from collections import defaultdict
from bs4 import BeautifulSoup
import re

def has_paste(key, paste_list):
    for paste in paste_list:
        if key == paste['key']:
            return True
    return False

def clean_paste_list(paste_list):
    clean_list = []

    for paste in paste_list:
        found = False
        for p2 in clean_list:
            if p2['key'] == paste['key']:
                found = True
                break
        if not found:
            clean_list.append(paste)

    return clean_list


def main(argv):

    paste_list                              = []
    root_url                                = 'http://pastebin.com'
    raw_url                                 = 'http://pastebin.com/raw.php?i='
    file_name, keywords, append, run_time = initialize_options(argv)

    print "\nCrawling %s Press ctrl+c to save file to %s" % (root_url, file_name)

    try:
        # Continually loop until user stops execution
        while True:
            # Get pastebin home page html
            root_html = BeautifulSoup(fetch_page(root_url), 'html.parser')

            # For each paste in the public pastes section of home page
            for paste_key in find_new_pastes(root_html):
                # Skip if already listed
                if has_paste(paste_key, paste_list):
                    continue

                paste = {}
                paste['key'] = paste_key
                paste['url'] = raw_url+paste_key
                paste['processed'] = False
                paste['time_discovered'] = datetime.datetime.utcnow().isoformat()
                paste_list.append(paste)

            for paste in paste_list:
                # Skip if already processed
                if paste['processed']:
                    continue

                # For every paste, check for keywords
                find_keywords(paste, keywords)
                paste['processed'] = True
                paste['time_processed'] = datetime.datetime.utcnow().isoformat()

                # Report
                report(paste, file_name)

            time.sleep(2)
            print "wait..."

    #     On keyboard interupt
    except KeyboardInterrupt:
        print "Exiting..."

    #    If http request returns an error and
    except urllib2.HTTPError, err:
        if err.code == 404:
            print "\n\nError 404: Pastes not found!"
        elif err.code == 403:
            print "\n\nError 403: Pastebin is mad at you!"
        else:
            print "\n\nYou\'re on your own on this one! Error code ", err.code

    #    If http request returns an error and
    except urllib2.URLError, err:
        print "\n\nYou\'re on your own on this one! Error code ", err

def report(paste, file_name):
    sys.stdout.write("Pastebin %s has %d hit(s)" %
            (paste['url'], len(paste['found_keywords'])))
    if len(paste['found_keywords']) > 0:
        for fk in paste['found_keywords']:
            sys.stdout.write(", %s" % fk['keyword'])
    sys.stdout.write(".\n")
    sys.stdout.flush()


    if len(paste['found_keywords']) == 0:
        return

    f = open(file_name, 'a')
    f.write("Pastebin %s has %d hit(s)" %
            (paste['url'], len(paste['found_keywords'])))
    if len(paste['found_keywords']) > 0:
        for fk in paste['found_keywords']:
            f.write(", %s" % fk['keyword'])
    f.write(".\n")
    f.flush()
    f.close()


def find_new_pastes(root_html):
    new_pastes = []

    div = root_html.find('div', {'id': 'menu_2'})
    ul = div.find('ul', {'class': 'right_menu'})

    for li in ul.findChildren():
        if li.find('a'):
            new_pastes.append(str(li.find('a').get('href')).replace("/", ""))

    return new_pastes

def find_keywords(paste, keywords):
    found_keywords = []
    page = fetch_page(paste['url'])

    for keyword in keywords:
        match = re.search(keyword, page, re.MULTILINE)
        if match:
            print "has match" + ' ' + keyword + ' ' + match.group(0)
#            print match.groupdict()

            mtch = {}
            mtch['keyword'] = keyword
            mtch['match'] = match.group(0)
            found_keywords.append(mtch)

    paste['found_keywords'] = found_keywords
    return paste

def fetch_page(page):
    response = urllib2.urlopen(page)
    return response.read()

def help():
    print 'pwnbin.py -k <keyword1>,<keyword2>,<keyword3>..... -o <outputfile>'


def initialize_options(argv):
    keywords = ['ssh', 'pass', 'key', 'token']
    file_name = 'log.txt'
    keyword_file_name = 'keywords.txt'
    append = False
    run_time = 0

    try:
        opts, args = getopt.getopt(argv,"h:k:o:at:i:")
    except getopt.GetoptError:
        help()
        sys.exit(2)

    for opt, arg in opts:

        if opt == '-h':
            help()
            sys.exit()
        elif opt == '-a':
            append = True
        elif opt == "-k":
            keywords = set(arg.split(","))
        elif opt == "-i":
            keyword_file_name = arg
        elif opt == "-o":
            file_name = arg
        elif opt == "-t":
            try:
                run_time = int(arg)
            except ValueError:
                print "Time must be an integer representation of seconds"
                sys.exit()

    f = open(keyword_file_name, 'r')
    d = f.read()
    f.close()
    keywords = set(d.split("\n"))
    keywords.remove('')

    return file_name, keywords, append, run_time

if __name__ == "__main__":
    main(sys.argv[1:])
