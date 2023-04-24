import re
import tldextract

from . import utils

url = "https://web.archive.org/web/20200528182006/https://ru.armeniasputnik.am/video/20200528/23207253/Printsip-kazhdyy-za-sebya-torzhestvuet-Lavrov-o-politike-Zapada-na-fone-pandemii--video.html"

domain = utils.get_url_domain(url)

print(domain)  # archive.org

# specific regular expressions for archive websites
archive_map = {
    # regexp with named group (`?P<original>` just assigns a name to the group)
    "archive.org": r"^https?:\/\/web\.archive\.org.*\/(?P<original>https?:\/\/.*)",
    # TODO for other similar websites
}

if domain in archive_map:
    match = re.search(archive_map[domain], url)
    # extract the group value
    original_url = match.group("original")

    # look at the original domain
    original_domain = utils.get_url_domain(original_url)

    # the `only_tld` just keeps one part after the `.com` / `.ru` part
    print(original_domain)  # armeniasputnik.am
    print(utils.get_url_domain(original_url, only_tld=False))  # ru.armeniasputnik.am
