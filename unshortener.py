import os
import json
import multiprocessing
import requests
import time
import tqdm
import signal
import sys

from bs4 import BeautifulSoup


import database
import utils

resolver_url = 'https://unshorten.me/'

shortening_domains = [
    # https://bit.do/list-of-url-shorteners.php
    't.co',
    'bit.do',
    'lnkd.in',
    'db.tt',
    'qr.ae',
    'adf.ly',
    'goo.gl',
    'bitly.com',
    'curl.tv',
    'tinyurl.com',
    'ow.ly',
    'bit.ly',
    'ity.im',
    'q.gs',
    'is.gd',
    'po.st',
    'bc.vc',
    'twitthis.com',
    'u.to',
    'j.mp',
    'buzurl.com',
    'cutt.us',
    'u.bb',
    'yourls.org',
    'x.co',
    'prettylinkpro.com',
    'scrnch.me',
    'filoops.info',
    'vzturl.com',
    'qr.net',
    '1url.com',
    'tweez.me',
    'v.gd',
    'tr.im',
    'link.zip.net',
    'tinyarrows.com',
    '➡.ws',
    '/✩.ws',
    'vai.la',
    'go2l.ink'
]

class Unshortener(object):
    def __init__(self):
        self.session = requests.Session()
        res_text = self.session.get(resolver_url).text
        soup = BeautifulSoup(res_text, 'html.parser')
        csrf = soup.select('input[name="csrfmiddlewaretoken"]')[0]['value']
        #print(csrf)
        self.csrf = csrf

    def unshorten(self, url, handle_error=True):
        domain = utils.get_url_domain(url)
        if domain in shortening_domains:
            cached = database.get_url_redirect(url)
            if not cached:
                res_text = self.session.post(resolver_url, headers={'Referer': resolver_url}, data={'csrfmiddlewaretoken': self.csrf, 'url': url}).text
                soup = BeautifulSoup(res_text, 'html.parser')
                try:
                    source_url = soup.select('section[id="features"] h3 code')[0].get_text()
                except:
                    print('ERROR for', url)
                    if handle_error:
                        source_url = url
                    else:
                        source_url = None
                m = (url, source_url)
                print('unshortened', url, source_url)
                #print(m)
                #self.mappings[m[0]] = m[1]
                database.save_url_redirect(url, source_url)
            else:
                source_url = cached['to']
        else:
            # not doing it!
            source_url = url
        return source_url

def func(params):
    url, uns = params
    res = uns.unshorten(url)
    #print(res)
    return (url, res)

def unshorten_multiprocess(url_list, pool_size=4):
    # one unshortener for each process
    unshorteners =  [Unshortener() for _ in range(pool_size)]
    args = [(url, unshorteners[idx % pool_size]) for (idx,url) in enumerate(url_list)]
    with multiprocessing.Pool(pool_size) as pool:
        # one-to-one with the url_list
        specific_results = {}
        for result in tqdm.tqdm(pool.imap_unordered(func, args), total=len(args)):
            url, resolved = result
            specific_results[url] = resolved
    return specific_results


if __name__ == "__main__":
    with open('data/aggregated_urls.json') as f:
        data = json.load(f)
    urls = data.keys()
    unshorten_multiprocess(urls)
