'''
Module for checking if url links return HTTP Success or Client Error.

Available functions:
- check_links           : Given a list of urls, returns two lists of valid and
                          dead links
- get_status_code       : Given a url, returns its status code
- is_valid_status       : Given a status code, return False if it is a Client
                          Error, True otherwise
- confirm_links_checked : Checks that all urls are either valid or dead, and
                          returns list of urls that weren't scrapped

If running the module as the main program, it takes in the following args:
--path_to_links      : file containing list of urls to check
--valid_links_output : file to save list of valid links
--dead_links_output  : file to save list of dead links
'''
import aiohttp
import argparse
import ast
import asyncio
import json
import random
import requests
from time import sleep

# Maximum amount of delay between each HTTP request.
# The actual delay time is uniformly distributed from [0, DELAY] seconds
DELAY = 1

# Maximum number of connections to the server at one time
MAX_CONNECTIONS = 5

# User agent headers for HTTP requests
HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
        'AppleWebKit/537.11 (KHTML, like Gecko) '
        'Chrome/23.0.1271.64 Safari/537.11',
        'Accept': ('text/html,application/xhtml+xml,application/xml;'
                   'q=0.9,*/*;q=0.8'),
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'
    },
    {
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/84.0.4147.105 Safari/537.36'),
        'Accept': ('text/html,application/xhtml+xml,application/xml;'
                   'q=0.9,image/webp,image/apng,*/*;q=0.8,application'
                   '/signed-exchange;v=b3;q=0.9'),
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
    },
    {
        'User-Agent': ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) '
                       'Gecko/20100101 Firefox/79.0'),
        'Accept': ('text/html,application/xhtml+xml,application/xml;'
                   'q=0.9,image/webp,*/*;q=0.8'),
        'Accept-Language': 'en-GB,en;q=0.7,en-US;q=0.3',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    {
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Ubuntu Chromium/83.0.4103.61 '
                       'Chrome/83.0.4103.61 Safari/537.36'),
        'Accept': ('text/html,application/xhtml+xml,application/xml;'
                   'q=0.9,image/webp,image/apng,*/*;'
                   'q=0.8,application/signed-exchange;v=b3;q=0.9'),
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8,my;q=0.7',
    }]


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


class _ProgressBar():
    '''
    Create a progress bar entity that can be updated asynchronously
    '''

    def __init__(self, total_items):
        '''
        Initialise the number of items to iterate and print the progress bar
        in the terminal
        '''
        self.iteration = -1
        self.total = total_items
        self.update_progress_bar()

    def update_progress_bar(self, decimals=1, length=25, fill='█'):
        '''
        Call in each iteration of a loop to update the terminal progress bar

        Args:
            decimals    - Optional  : decimals places in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        '''
        self.iteration += 1
        percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                         (self.iteration /
                                                          float(self.total)))
        filledLength = int(length * self.iteration // self.total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\rProgress: |{bar}| {percent}% Complete', end='\r')
        # Print New Line on Complete
        if self.iteration == self.total:
            print()


def get_status_code(url):
    '''
    Returns the status code of a given url

    This function runs in a random amount of time given the DELAY specified
    '''
    # Add delay to avoid being blocked by website
    sleep(DELAY * random.random())

    # Randomly select from a list of headers to pretend to be a real browser
    headers = random.choice(HEADERS_LIST)

    try:
        with requests.get(url, headers=headers) as r:
            status_code = r.status_code
            if not is_valid_status(status_code):
                print(url, status_code)
        return status_code
    except Exception as e:
        print(e)
        print(f'{url} could not be scrapped synchronously, please rerun '
              'script on this url or perform a manual check')

    return None


def is_valid_status(status):
    '''
    Return False if a given status code is a Client Error.
    Return True otherwise.

    '''
    if status >= 200 and status < 400:
        return True
    return False


async def _async_get_status_code(url, progress_bar=None):
    '''
    Returns the status code of a given url and a HTTP session
    This function is called asynchronously with other HTTP requests

    This function runs in a random amount of time given the DELAY specified
    '''
    # Randomly select from a list of headers to pretend to be a real browser
    headers = random.choice(HEADERS_LIST)
    conn = aiohttp.TCPConnector(
        limit=MAX_CONNECTIONS, limit_per_host=MAX_CONNECTIONS)

    try:
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(url, headers=headers) as r:
                status_code = r.status

                if not is_valid_status(status_code):
                    print(url, status_code)
        if progress_bar:
            progress_bar.update_progress_bar()

        return (url, status_code)

    except Exception as e:
        print(e)
    return (url, None)


async def _async_check_links(links, print_progress=False):
    '''
    Helper function for check_links() to make HTTP requests asynchronously
    '''
    valid_links = []
    dead_links = []

    # Initialise progress bar
    n_links = len(links)
    progress_bar = None
    if print_progress:
        progress_bar = _ProgressBar(n_links)

    # Create client session and make HTTP requests

    try:
        tasks = []
        for url in links:
            tasks.append(
                asyncio.ensure_future(
                    _async_get_status_code(url, progress_bar)))
            await asyncio.sleep(DELAY * random.random())

        results = await asyncio.gather(*tasks)
    except Exception as e:
        print(e)

    # Split urls into valid and dead lists
    for url, status in results:
        # Fall back to synchronous checking if url failed
        if not status:
            print(f'{url} failed to be scrapped asynchronously, retrying...')
            status = get_status_code(url)
            if status:
                print(f'{url} scrapped successfully')
            else:
                print(f'{url} could not be scrapped, please '
                      'rerun script on this url or perform a manual check')
                continue

        if is_valid_status(status):
            valid_links.append(url)
        else:
            dead_links.append(url)

    return valid_links, dead_links


def confirm_links_checked(links, valid_links, dead_links):
    '''
    Confirms that all links given to check_links() have been checked.
    Otherwise, prints a list of links to rerun the script on.
    '''
    links = set(links)
    valid_links = set(valid_links)
    dead_links = set(dead_links)

    set_difference = links - valid_links - dead_links

    print()

    if not set_difference:
        print('All links checked successfully.')
        return True

    print(f'WARNING. {len(set_difference)} urls not scrapped successfully. '
          'Please rerun script on the following urls:')
    print(json.dumps(list(set_difference)))

    return False


def check_links(links, print_progress=False):
    '''
    Given a list of urls, returns two lists of valid and dead links
    '''

    valid_links, dead_links = asyncio.run(
        _async_check_links(links, print_progress=print_progress))

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
        print('Valid links: ', json.dumps(valid_links))
        print('Dead links: ', json.dumps(dead_links))

        # Confirm that all links have been scrapped
        confirm_links_checked(links, valid_links, dead_links)

    if args.valid_links_output:
        with open(args.valid_links_output, 'w') as output:
            output.write(json.dumps(valid_links))

    if args.dead_links_output:
        with open(args.dead_links_output, 'w') as output:
            output.write(json.dumps(dead_links))
