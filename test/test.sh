set -e
py.test test_tweets.tavern.yaml -v
py.test test_twitter_accounts.tavern.yaml -v