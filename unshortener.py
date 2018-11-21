import requests

from bs4 import BeautifulSoup

resolver_url = 'https://unshorten.me/'

class Unshortener(object):
    def __init__(self, mappings={}):
        self.session = requests.Session()
        res_text = self.session.get(resolver_url).text
        soup = BeautifulSoup(res_text, 'html.parser')
        csrf = soup.select('input[name="csrfmiddlewaretoken"]')[0]['value']
        print(csrf)
        self.csrf = csrf
        self.mappings = mappings

    def unshorten(self, url):
        if url not in self.mappings:
            res_text = self.session.post(resolver_url, headers={'Referer': resolver_url}, data={'csrfmiddlewaretoken': self.csrf, 'url': url}).text
            soup = BeautifulSoup(res_text, 'html.parser')
            try:
                source_url = soup.select('section[id="features"] h3 code')[0].get_text()
            except:
                print('ERROR for', url)
                source_url = url
            m = (url, source_url)
            #print(m)
            self.mappings[m[0]] = m[1]
        else:
            source_url = self.mappings[url]
        return source_url


if __name__ == "__main__":
    a = Unshortener()
    a.unshorten('http://fb.me/5McHagkob')