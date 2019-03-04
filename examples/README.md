# Examples

This folder contains some response objects from the Misinformation Detection API.

# url kfc dearborn

request: `GET /api/analysis/urls?url=https://www.facebook.com/kenneth.buddin/posts/1552264144844018`

response: [json response](analyse_url_kfc_dearborn.jsonc)

Details: the url (https://www.facebook.com/kenneth.buddin/posts/1552264144844018) has been fact-checked by snopes (as it can be seen in the `reasons`: https://www.snopes.com/fact-check/kfc-dearborn-shariah-law/)

# tweet_1

request: `GET /api/analysis/tweets/1100526678617526272`

response: [json response](analyse_tweet_1.jsonc)

Details: the tweet (https://twitter.com/BernieSanders/status/1100526678617526272) has been factchecked by politifact (https://www.politifact.com/truth-o-meter/statements/2019/mar/01/bernie-sanders/fact-checking-bernie-sanders-15-minimum-wage/)

# tweet_2

request: `GET /api/analysis/tweets/1099251789759635456`

response: [json response](analyse_tweet_2.jsonc)

Details: the tweet (https://twitter.com/newstutu/status/1099251789759635456) contains a link (https://t.co/SUqIeeQOqU?amp=1 --> https://100percentfedup.com/report-illegal-caught-on-video-in-shootout-with-sheriffs-deputy-was-deported-three-times-video/?utm_source=dlvr.it&utm_medium=twitter) that belongs to a domain (100percentfedup.com) that is known for spreading misinforming content (several datasets saying that).
