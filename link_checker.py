'''
Module for checking if url links return HTTP Success or Client Error.

Available functions:
- check_links     : Given a list of urls, returns two lists of valid and
                    dead links
- get_status_code : Given a url, returns its status code
- is_valid_status : Given a status code, return False if it is a Client Error,
                    True otherwise

If running the module as the main program, it takes in the following args:
--path_to_links      : file containing list of urls to check
--valid_links_output : file to save list of valid links
--dead_links_output  : file to save list of dead links
'''
import argparse
import ast
import aiohttp
import json
import random
import requests
from time import sleep

# Average amount of time between each HTTP request
DELAY = 0.1

# User agent headers for HTTP requests
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
           'AppleWebKit/537.11 (KHTML, like Gecko) '
           'Chrome/23.0.1271.64 Safari/537.11',
           'Accept': ('text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,*/*;q=0.8'),
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}


def _parse_args():
    '''
    Returns arguments when running module as the main program
    '''
    parser = argparse.ArgumentParser(description="Dead links checker")
    parser.add_argument('--path_to_links',
                        type=str,
                        required=False,
                        help=('Path to url links to be checked'))
    parser.add_argument('--valid_links_output',
                        type=str,
                        required=False,
                        help=('File to store valid links'))
    parser.add_argument('--dead_links_output',
                        type=str,
                        required=False,
                        help=('File to store valid links'))
    return parser.parse_args()


def _update_progress_bar(iteration, total, decimals=1, length=50, fill='█'):
    '''
    Call in a loop to create terminal progress bar

    Args:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    '''
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\rProgress: |{bar}| {percent}% Complete', end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def get_status_code(url):
    '''
    Returns the status code of a given url

    This function runs in a random amount of time given the DELAY specified
    '''
    # Add delay to avoid being blocked by website
    sleep(0.5 * random.random())
    with requests.head(url, headers=HEADERS, allow_redirects=True) as r:
        status_code = r.status_code
        print(url, " ", status_code)
    return status_code


def is_valid_status(status):
    '''
    Return False if a given status code is a Client Error.
    Return True otherwise.

    '''
    if status >= 400 and status < 500:
        return False
    return True


def check_links(links, print_progress=False):
    '''
    Given a list of urls, returns two lists of valid and dead links
    '''
    valid_links = []
    dead_links = []
    status_codes = []

    # Initialise progress bar
    n_links = len(links)
    if print_progress:
        _update_progress_bar(0, n_links)

    # Get status codes
    for i, url in enumerate(links):
        status_codes.append(get_status_code(url))
        if print_progress:
            _update_progress_bar(i+1, n_links)

    # Split urls into valid and dead lists
    for link, status in zip(links, status_codes):
        if is_valid_status(status):
            valid_links.append(link)
        else:
            print(link)
            dead_links.append(link)

    return valid_links, dead_links


if __name__ == '__main__':
    '''
    If this module is run as the main program, we assume that the user wants to
    run the link checker on a supplied list of urls, and to store the output.

    Args:
        --path_to_links      : file containing list of urls to check
        --valid_links_output : file to save list of valid links
        --dead_links_output  : file to save list of dead links
    '''
    args = _parse_args()
    if args.path_to_links:
        links_file = open(args.path_to_links).read()
        links = ast.literal_eval(links_file)
        valid_links, dead_links = check_links(links, print_progress=True)
        print(json.dumps(valid_links),
              json.dumps(dead_links))

    if args.valid_links_output:
        with open(args.valid_links_output, 'w') as output:
            output.write(json.dumps(valid_links))

    if args.dead_links_output:
        with open(args.dead_links_output, 'w') as output:
            output.write(json.dumps(dead_links))
