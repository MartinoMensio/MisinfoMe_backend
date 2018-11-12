
def count(shared_urls, dataset_by_url, tweets):
    matching = [dataset_by_url[el] for el in shared_urls if el in dataset_by_url]
    verified = [el for el in matching if el['label'] == 'true']
    fake = [el for el in matching if el['label'] == 'fake']
    return {
        'tweets_cnt': len(tweets),
        'shared_urls_cnt': len(shared_urls),
        'verified_cnt': len(verified),
        'fake_cnt': len(fake),
        'fake_urls': fake,
        'unknown_cnt': len(shared_urls) - len(matching)
    }
