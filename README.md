# Fast Link Checking
Given a list of urls, this script checks whether the url is dead or alive. i.e. whether it returns a HTTP Success code (2xx), or if it returns a HTTP Client error (4xx)/HTTP Server error (5xx) status code. It then returns two lists, one containing the valid urls that were successfully visited, and one that contains dead urls that gave an unsuccessful status code.

## Install
All requirements for this script are included in `requirements.txt`. After cloning this project, simply run the following to install all dependencies.

```
$ pip install -r requirements.txt
```

## Usage
This script can be run as a command-line program, or imported as a module.


### Command Line Options

__`--path_to_links=<filename>` (required)__

File containing list of urls to check. Urls should be given as a python-style/json-style list of strings.

```
$ python link_checker.py --path_to_links=links.json
```

__`--valid_links_output <filename>`__

File to save list of valid links. The list is jsonified before saving.

```
$ python link_checker.py --path_to_links=links.json --valid_links_output=valid.json
```

__`--dead_links_output=<filename>`__

File to save list of dead links. The list is jsonified before saving.

```
$ python link_checker.py --path_to_links=links.json --dead_links_output=dead.json
```

__`--delay=<number>`__

The maximum delay between each HTTP request. The actual delay is uniformly and randomly distributed between `[0, delay]` for each request. The final rate of scraping would then be _~2/delay urls/second_.

```
$ python link_checker.py --path_to_links=links.json --delay=1
```

__`--use_head`__

Check urls via HEAD requests. This reduces the load on the server we are scraping from and reduces the risk of being blocked. By default, this option is turned off because not all servers correctly implement HEAD requests. So for example, we might receive status code 200 when making a GET request to a url, but 404 when making a HEAD request.

```
$ python link_checker.py --path_to_links=links.json --use_head
```

## API

### check_links(links, delay?, head?, print_progress?)

__links__

__delay__

__head__

__print_progress__

### get_status_code(url)

__url__

### is_valid_status(status)

__status__

### confirm_links_checked(links, valid_links, dead_links)

__links__

__valid_links__

__dead_links__

## Failure to check links

Occassionally, a url might fail to be checked either through some unexpected error, or when blocked by the target server. In this case, this script falls back to check the status of the link synchronously after closing all other sessions.

If, after retrying, the link still fails to be scraped, this script will output a warning followed by the list of urls that failed to be scraped. These urls should be checked either manually, or by running the script on them again.

## Notes
This tool was primarily built to scrape data from [Singapore Statutes Online](https://sso.agc.gov.sg/), so the methods employed for scraping are fine-tuned to this site and might need to be updated accordingly in the future.

The SSO's HTTP request limiter that prevents the same session from making too many requests within a short period of time, but does not prevent the same IP address from making many requests at the same time. As such, this script opens an asynchronous client session with the target website for each url. But if the SSO's server rules change in the future, proxies might need to be employed to prevent getting blocked.

We also impose a current average scraping rate of _~2 urls/second_. This current rate was arbitrarily decided. As a government-run website, we assume that such a rate will not be overwhelming, while at the same time gives us a reasonable run time for the script. This rate can be adjusted as needed through the `DELAY` global parameter, the `delay` parameter for `check_links()`, or through the command-line argument `--delay` as specified above. The final rate of scraping would then be _~2/delay urls/second_.
