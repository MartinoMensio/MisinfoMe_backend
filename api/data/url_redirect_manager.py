import validators

from . import database
from . import utils

"""
def get_url_redirect_for(from_url):
    # TODO clean and check url
    from_url = clear_url(from_url)
    if not from_url:
        return from_url
    # TODO see if it is the case to go for a redirect
    if True:
        return from_url
    redirect_info = database.get_url_redirect(from_url)
    if redirect:
        to_url = redirect_info['to']
    else:
        to_url = get_redirect_info_remote(from_url)
        database.save_url_redirect(from_url, to_url)
    return to_url

def filter_need_redirect_check(url_list):
    alread_stored = database.get_url_redirects_in(url_list)
    return [el['to'] for el in alread_stored]

def get_redirect_info_remote(url):
    '''Interrogate the webservice for getting the redirect informations'''
    # TODO
    raise NotImplementedError()
"""

def clear_url(url):
    url = url[:1000] # mongo limit
    if validators.url(url) == True:
        return url
    else:
        return None


# migration function
def load_mappings(input_file_path):
    content = utils.read_json(input_file_path)
    for k,v in content.items():
        #k = lower(k)
        #v = lower(v)
        k = clear_url(k)
        v = clear_url(v)
        if not k or not v:
            continue
        database.save_url_redirect(k, v)

# migration function
def load():
    load_mappings('cache/url_mappings.json')
    load_mappings('../datasets/data/mappings.json')

# TODO run that to see when it's the case to retrieve the redirect info from the webservice
def analyse_redirects():
    # the list of redirects that have a different destination page
    different_redirects = []
    redirecting_domains = set()
    for redirect_info in database.get_url_redirects():
        from_url = redirect_info['_id']
        to_url = redirect_info['to']
        if from_url != to_url:
            different_redirects.append([from_url, to_url])
            try:
                from_domain = utils.get_url_domain(from_url)
                to_domain = utils.get_url_domain(to_url)
            except Exception as e:
                print(from_url, to_url)
                raise e
            if from_domain != to_domain:
                redirecting_domains.add(from_domain)
    print(redirecting_domains)