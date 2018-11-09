import json

def load_data(path='../datasets/data/all.json', by_url=False):
    with open(path) as f:
        content = json.load(f)
    if by_url:
        return {el['url']: el for el in content}
    else:
      return content
