import json
from urllib.parse import urlparse
import tldextract
import re


def add_protocol(url):
    """when the URL does not have http://"""
    if not re.match(r"[a-z]+://.*", url):
        # default protocol
        url = "https://" + url
    return url


def get_url_domain(url, only_tld=True):
    """Returns the domain of the URL"""
    if not url:
        return ""
    ext = tldextract.extract(url)
    if not only_tld:
        result = ".".join(part for part in ext if part)
    else:
        result = ".".join([ext.domain, ext.suffix])
    if result.startswith("www."):
        # sometimes the www is there, sometimes not
        result = result[4:]
    return result.lower()


def get_url_domain_without_subdomains(url):
    ext = tldextract.extract(url)
    result = "{}.{}".format(ext[1], ext[2])
    return result.lower()


# this regex works for facebook and twitter and extracts the source as account name
# TODO for youtube extract the channel name as in the second answer here https://stackoverflow.com/questions/17806944/how-to-get-youtube-channel-name
social_regex = r"^(https?:\/\/)?([a-z-]+\.)*(?P<res>(facebook\.com|facebook\.com\/pages|twitter\.com|youtube\.com)\/([A-Za-z0-9_.]*))(\/.*)?"


# TODO do a remote call to credibility or viceversa
def get_url_source(url):
    """Returns the source of the URL (may be different from domain)"""
    match = re.search(social_regex, url)
    if match:
        result = match.group("res")
        print(url, "-->", result)
        return result
    else:
        return get_url_domain(url, only_tld=False)


def read_json(input_path):
    with open(input_path) as f:
        return json.load(f)
