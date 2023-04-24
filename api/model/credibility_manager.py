import time
import re
from tqdm import tqdm
from collections import defaultdict

from ..data import database
from ..external import twitter_connector, credibility_connector, ExternalException
from ..data import utils, unshortener


zero_credibility = {"credibility": {"value": 0.0, "confidence": 0.0}}


def get_credibility_weight(credibility_value):
    """This provides a weight that gives more weight to negative credibility: from 1 (normal) to 100 (for -1)"""

    result = 1
    if credibility_value < 0:
        result *= -credibility_value * 100

    return result


# Source credibility


def get_source_credibility(source, update_status_fn=None):
    """Obtain the credibility score for a single source"""
    if update_status_fn:
        update_status_fn("computing the credibility")
    return credibility_connector.get_source_credibility(source)


def get_sources_credibility(sources):
    """Obtain the credibility score for multiple sources"""
    return credibility_connector.post_source_credibility_multiple(sources)


def get_url_credibility(url, update_status_fn=None):
    """Obtain the credibility score for a single source"""
    if update_status_fn:
        update_status_fn("computing the credibility of URL")
    return credibility_connector.get_url_credibility(url)


# Tweet credibility


def get_tweet_credibility_from_id(tweet_id, update_status_fn=None):
    # retrieve tweet then delegate to real function
    if update_status_fn:
        update_status_fn("retrieving a tweet")
    try:
        exception = None
        exception_real = None
        tweet = twitter_connector.get_tweet(tweet_id)
    except ExternalException as e:
        # tweet may have been deleted
        tweet = {
            "id": str(tweet_id),
            "text": None,
            "retweet": None,
            "retweet_source_tweet": None,
            "links": [],
            "user_id": None,
            "user_screen_name": None,
            "exception": vars(e),
        }
        # exception = dict(vars(e))
        # exception_real = e
    return get_tweet_credibility_from_tweet(
        tweet, exception, exception_real, update_status_fn
    )


def get_tweet_credibility_from_dirty_tweet_batch(dirty_tweets):
    tweets = [cleanup_tweet(t) for t in tqdm(dirty_tweets, desc="cleaning tweets")]
    sources_credibility = get_tweets_credibility(
        tweets, group_method="source"
    )  # TODO: this is source, instead in old analysis it's domain
    # {id: el for el in sources_credibility['assessments'] for id in el['tweets_containing']}
    sources_credibility_by_tweet_id_tmp = defaultdict(list)
    for el in sources_credibility["assessments"]:
        for id in el["tweets_containing"]:
            sources_credibility_by_tweet_id_tmp[id].append(el)
    sources_credibility_by_tweet_id = {}
    for tweet_id, values in sources_credibility_by_tweet_id_tmp.items():
        # aggregate between different sources for the same tweet
        credibility_sum = sum(el["credibility"]["value"] for el in values)
        confidence_sum = sum(el["credibility"]["confidence"] for el in values)
        if credibility_sum:
            credibility_weighted = credibility_sum / len(values)
            confidence_weighted = confidence_sum / len(values)
        else:
            credibility_weighted = 0.0
            confidence_weighted = 0.0
        sources_credibility_by_tweet_id[tweet_id] = {
            "credibility": {
                "value": credibility_weighted,
                "confidence": confidence_weighted,
            },
            "assessments": values,
        }

    urls_credibility = get_tweets_credibility(tweets, group_method="url")
    # {id: el for el in urls_credibility['assessments'] for id in el['tweets_containing']}
    # dict to avoid repeating the same source
    urls_credibility_by_tweet_id_tmp = defaultdict(dict)
    for el in urls_credibility["assessments"]:
        for id in el["tweets_containing"]:
            urls_credibility_by_tweet_id_tmp[id][el["itemReviewed"]] = el
    urls_credibility_by_tweet_id = {}
    for tweet_id, dicts in urls_credibility_by_tweet_id_tmp.items():
        values = list(dicts.values())
        # aggregate between different urls for the same tweet
        credibility_sum = sum(el["credibility"]["value"] for el in values)
        confidence_sum = sum(el["credibility"]["confidence"] for el in values)
        if credibility_sum:
            credibility_weighted = credibility_sum / len(values)
            confidence_weighted = confidence_sum / len(values)
        else:
            credibility_weighted = 0.0
            confidence_weighted = 0.0
        urls_credibility_by_tweet_id[tweet_id] = {
            "credibility": {
                "value": credibility_weighted,
                "confidence": confidence_weighted,
            },
            "assessments": values,
        }

    results = []
    for t in tqdm(tweets, desc="putting together credibility scores"):
        tweet_id = t["id"]
        if tweet_id in sources_credibility_by_tweet_id:
            s_c = sources_credibility_by_tweet_id[tweet_id]
            s_c = {k: v for k, v in s_c.items() if k != "tweets_containing"}
        else:
            s_c = zero_credibility
        if tweet_id in urls_credibility_by_tweet_id:
            u_c = urls_credibility_by_tweet_id[tweet_id]
            u_c = {k: v for k, v in u_c.items() if k != "tweets_containing"}
        else:
            u_c = zero_credibility
        # TODO profile_as_source_credibility, double check weights
        confidence_weighted = (
            s_c["credibility"]["confidence"] * 0.15
            + u_c["credibility"]["confidence"] * 0.6
        ) / (
            0.15 + 0.6
        )  # profile_as_source_credibility['credibility']['confidence'] * 0.6 +
        if confidence_weighted:
            # profile_as_source_credibility['credibility']['value'] * 0.6 * profile_as_source_credibility['credibility']['confidence'] +
            value_weighted = (
                s_c["credibility"]["value"] * 0.15 * s_c["credibility"]["confidence"]
                + u_c["credibility"]["value"] * 0.6 * u_c["credibility"]["confidence"]
            ) / confidence_weighted
        else:
            value_weighted = 0.0
        final_credibility = {"value": value_weighted, "confidence": confidence_weighted}

        misinfome_frontend_url = (
            f"https://misinfo.me/misinfo/credibility/tweets/{tweet_id}"
        )
        result = {
            "credibility": final_credibility,
            "profile_as_source_credibility": zero_credibility,  # TODO
            "sources_credibility": s_c,
            "urls_credibility": u_c,
            "itemReviewed": tweet_id,
            "ratingExplanationFormat": "url",
            "ratingExplanation": misinfome_frontend_url,
            "exception": None,
        }
        # if tweet_direct_credibility['credibility']['confidence'] > 0.01:
        #     result['tweet_direct_credibility'] = tweet_direct_credibility

        # if exception and not tweet_direct:
        #     raise exception_real

        # explanation
        explanation = get_credibility_explanation(result)
        result["ratingExplanation"] = explanation
        result["ratingExplanationFormat"] = "markdown"

        results.append(result)
    return results


def cleanup_tweet(dirty_tweet):
    return {
        "id": str(dirty_tweet["id"]),
        "text": dirty_tweet["text"],
        "retweet": any(
            el["type"] == "retweeted" for el in dirty_tweet.get("referenced_tweets", [])
        ),
        "retweeted_source_tweet": None,
        "links": [
            el["expanded_url"] for el in dirty_tweet.get("entities", {}).get("urls", [])
        ],
        # 'user_screen_name': None # TODO?
    }


def get_tweet_credibility_from_dirty_tweet(dirty_tweet):
    # a dirty tweet may come from API request
    tweet = cleanup_tweet(dirty_tweet)
    return get_tweet_credibility_from_tweet(
        tweet, exception=None, exception_real=None, update_status_fn=None
    )


def get_tweet_credibility_from_tweet(
    tweet, exception=None, exception_real=None, update_status_fn=None
):
    tweet_id = tweet["id"]
    # the real function inside for the tweet rating
    if update_status_fn:
        update_status_fn("computing the credibility of a tweet")
    sources_credibility = get_tweets_credibility([tweet])
    urls_credibility = get_tweets_credibility([tweet], group_method="url")

    # TODO: this does not look at the history of the user, just if it has been reviewed directly
    if tweet.get("user_screen_name", None):
        tweet_direct_credibility = get_tweets_credibility_directly_reviewed(tweet)
        screen_name = tweet["user_screen_name"]
        profile_as_source_credibility = credibility_connector.get_source_credibility(
            f"twitter.com/{screen_name}"
        )
    else:
        profile_as_source_credibility = tweet_direct_credibility = {
            "credibility": {"value": 0.0, "confidence": 0.0}
        }

    # profile as source: 20% weight
    # urls in tweet: 60%
    # sources in tweet: 20%
    # tweet_direct_credibility takes over if it exists
    if tweet_direct_credibility["credibility"]["confidence"] > 0.01:
        confidence_weighted = tweet_direct_credibility["credibility"]["confidence"]
        value_weighted = tweet_direct_credibility["credibility"]["value"]
        tweet_direct = True
    else:
        tweet_direct = False
        confidence_weighted = (
            profile_as_source_credibility["credibility"]["confidence"] * 0.2
            + sources_credibility["credibility"]["confidence"] * 0.2
            + urls_credibility["credibility"]["confidence"] * 0.6
        )
        if confidence_weighted:
            value_weighted = (
                profile_as_source_credibility["credibility"]["value"]
                * 0.2
                * profile_as_source_credibility["credibility"]["confidence"]
                + sources_credibility["credibility"]["value"]
                * 0.2
                * sources_credibility["credibility"]["confidence"]
                + urls_credibility["credibility"]["value"]
                * 0.6
                * urls_credibility["credibility"]["confidence"]
            ) / confidence_weighted
        else:
            value_weighted = 0.0
    final_credibility = {"value": value_weighted, "confidence": confidence_weighted}

    tweet_id = str(tweet_id)

    # TODO if tweet was removed, and we have some fact-checks, retrieve the user handle to show the other components of the score (credibility_as_source)

    misinfome_frontend_url = f"https://misinfo.me/misinfo/credibility/tweets/{tweet_id}"
    result = {
        "credibility": final_credibility,
        "profile_as_source_credibility": profile_as_source_credibility,
        "sources_credibility": sources_credibility,
        "urls_credibility": urls_credibility,
        "itemReviewed": tweet_id,
        "ratingExplanationFormat": "url",
        "ratingExplanation": misinfome_frontend_url,
        "exception": exception,
    }
    if tweet_direct_credibility["credibility"]["confidence"] > 0.01:
        result["tweet_direct_credibility"] = tweet_direct_credibility

    if exception and not tweet_direct:
        raise exception_real

    # explanation
    explanation = get_credibility_explanation(result)
    result["ratingExplanation"] = explanation
    result["ratingExplanationFormat"] = "markdown"

    return result


def get_credibility_explanation(rating):
    tweet_id = rating["itemReviewed"]
    misinfome_frontend_url = f"https://misinfo.me/misinfo/credibility/tweets/{tweet_id}"
    tweet_link = f"https://twitter.com/a/statuses/{tweet_id}"
    # TODO manage cases when multiple situations apply (sort by confidence the different conditions)
    if "tweet_direct_credibility" in rating:
        # Situation 1: the tweet has been fact-checked
        # TODO manage multiple reviews, agreeing and disagreeing
        tweet_rating = rating["tweet_direct_credibility"]["assessments"][0]["reports"][
            0
        ]
        factchecker_label = tweet_rating["coinform_label"].replace("_", " ")
        factchecker_name = tweet_rating["origin"]["name"]
        factchecker_assessment = tweet_rating["origin"]["assessment_url"]
        factchecker_report_url = tweet_rating["report_url"]
        explanation = (
            f"This [tweet]({tweet_link}) has been fact-checked as **{factchecker_label}** "
            f"by [{factchecker_name}]({factchecker_assessment}). "
            f"See their report [here]({factchecker_report_url}). "
        )  # \
        #   f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'''
    elif rating["urls_credibility"]["credibility"]["confidence"] > 0.01:
        # Situation 2: the tweet contains a link that was reviewed
        # TODO manage multiple URLs
        # TODO manage multiple reviews, agreeing and disagreeing
        # TODO provide source name??
        print("rating", rating)
        url_rating = rating["urls_credibility"]["assessments"][0]["assessments"][0][
            "reports"
        ][0]
        url_reviewed = "TODO"
        factchecker_label = url_rating["coinform_label"].replace("_", " ")
        factchecker_name = url_rating["origin"]["name"]
        factchecker_assessment = url_rating["origin"]["assessment_url"]
        factchecker_report_url = url_rating["report_url"]
        explanation = (
            f"This [tweet]({tweet_link}) contains a link fact-checked as **{factchecker_label}** "
            f"by [{factchecker_name}]({factchecker_assessment}). "
            f"See their report [here]({factchecker_report_url}). "
        )  # \
        # f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'''
    elif rating["sources_credibility"]["credibility"]["confidence"] > 0.2:
        # Situation 3: the tweet contains a link that comes from a source that is not credible
        source_evaluations = rating["sources_credibility"]["assessments"]
        # TODO manage multiple sources rated
        # TODO manage multiple reviews, agreeing and disagreeing
        source = source_evaluations[0]["itemReviewed"]
        # raise ValueError(rating)
        not_factchecking_report = [
            el
            for el in source_evaluations[0]["assessments"]
            if el["origin_id"] != "factchecking_report"
        ]
        print(not_factchecking_report)
        tools = sorted(
            not_factchecking_report,
            key=lambda el: el["weights"]["final_weight"],
            reverse=True,
        )[:3]
        factchecking_report = [
            el
            for el in source_evaluations[0]["assessments"]
            if el["origin_id"] == "factchecking_report"
        ]
        if factchecking_report:
            factchecking_report = factchecking_report[0]
            # TODO fact-checks may also be true!!!! In this case the list filtered by not_credible will become empty
            reports = factchecking_report["reports"]
            # dict removes duplicates
            print(reports)
            # origin is null if not a proper fact-checker
            factcheckers = {
                el["origin"]["id"]: el["origin"]
                for el in reports
                if (el["coinform_label"] == "not_credible" and el["origin"])
            }
            # create markdown for each one of them
            factcheckers_names = [el["name"] for el in factcheckers.values()]
            factcheckers_names = [
                f'[{el["name"]}]({el["assessment_url"]})'
                for el in factcheckers.values()
            ]
            additional_explanation_factchecking = f'*{source}* also contains false claims according to {", ".join(factcheckers_names)}. '
        else:
            additional_explanation_factchecking = ""
        # TODO tools have evaluation URLs, maybe it's better than linking to the homepage?
        tool_names = ", ".join(
            f"[{el['origin']['name']}]({el['origin']['homepage']})" for el in tools
        )
        label = get_coinform_label(rating["sources_credibility"]["credibility"])
        explanation = (
            f'This [tweet]({tweet_link}) contains a link to *{source}* which is a **{label.replace("_", " ")}** source '
            f"according to {tool_names}. "
            f"{additional_explanation_factchecking}"
        )  # \
        #   f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'
    elif rating["profile_as_source_credibility"]["credibility"]["confidence"] > 0.01:
        # Situation 4: the tweet comes from a non-credible profile
        profile_link = rating["profile_as_source_credibility"]["itemReviewed"]
        profile_name = profile_link.split("/")[-1]  # (the same as screenName)
        # profile_link = f'https://twitter.com/{profile_name}'
        assessments = rating["profile_as_source_credibility"]["assessments"]
        factchecking_report = [
            el for el in assessments if el["origin_id"] == "factchecking_report"
        ]
        reports = factchecking_report[0]["reports"]
        # TODO count by tweet reviewed, not by factchecker URL!!!
        misinfo_from_profile_cnt = len(
            set(
                el["report_url"]
                for el in reports
                if el["coinform_label"] == "not_credible"
            )
        )
        goodinfo_from_profile_cnt = len(
            set(
                el["report_url"] for el in reports if el["coinform_label"] == "credible"
            )
        )
        uncertain_from_profile_cnt = len(
            set(
                el["report_url"]
                for el in reports
                if el["coinform_label"] == "uncertain"
            )
        )
        if misinfo_from_profile_cnt:
            stats_piece = f"misinformation other {misinfo_from_profile_cnt} times"
        elif uncertain_from_profile_cnt:
            stats_piece = (
                f"uncertain informations other {uncertain_from_profile_cnt} times"
            )
        else:
            stats_piece = (
                f"verified information other {goodinfo_from_profile_cnt} times"
            )
        explanation = (
            f"This [tweet]({tweet_link}) comes from [{profile_name}]({profile_link}), "
            f"a profile that has shared {stats_piece}. "
        )  # \
        #   f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'
    else:
        explanation = f"We could not find any verified information regarding the credibility of this [tweet]({tweet_link})."  # \
        #   f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'

    return explanation


def get_coinform_label(credibility):
    label = "not_verifiable"
    if credibility["confidence"] >= 0.5:
        if credibility["value"] > 0.6:
            label = "credible"
        elif credibility["value"] > 0.25:
            label = "mostly_credible"
        elif credibility["value"] >= -0.25:
            label = "uncertain"
        else:
            label = "not_credible"
    return label
    # print(tweets_credibility)
    # if not tweets_credibility:
    #     return None # error tweets not found
    # return tweets_credibility


# def get_tweets_credibility_from_ids(tweet_ids): # NOT CALLED ANYWHERE
#     # TODO implement in twitter_connnector batch tweet retrieval
#     tweets = [twitter_connector.get_tweet(tweet_id) for tweet_id in tweet_ids]
#     sources_credibility = get_tweets_credibility(tweets)
#     urls_credibility = get_tweets_credibility(tweets, group_method='url')
#     # tweet_direct_credibility = get_tweets_credibility_directly_reviewed(tweet)
#     profile_as_source_credibility = {
#         'credibility':{
#             'value': 0,
#             'confidence': 0
#         }
#     }

#     # profile as source: 60% weight
#     # urls shared: 25%
#     # sources used: 15%
#     confidence_weighted = profile_as_source_credibility['credibility']['confidence'] * 0.6 + sources_credibility['credibility']['confidence'] * 0.15 + urls_credibility['credibility']['confidence'] * 0.25
#     if confidence_weighted:
#         value_weighted = (profile_as_source_credibility['credibility']['value'] * 0.6 * profile_as_source_credibility['credibility']['confidence'] + sources_credibility['credibility']['value'] * 0.15 * sources_credibility['credibility']['confidence']+ urls_credibility['credibility']['value'] * 0.25 * urls_credibility['credibility']['confidence']) / confidence_weighted
#     else:
#         value_weighted = 0.
#     final_credibility = {
#         'value': value_weighted,
#         'confidence': confidence_weighted
#     }

#     result = {
#         'credibility': final_credibility,
#         'profile_as_source_credibility': profile_as_source_credibility,
#         'sources_credibility': sources_credibility,
#         'urls_credibility': urls_credibility,
#         'itemReviewed': tweet_ids
#     }
#     return result


def get_tweets_credibility_directly_reviewed(tweet):
    # TODO how to deal with username change to search for tweet credibility?
    tweet_url = f'https://twitter.com/{tweet["user_screen_name"]}/status/{tweet["id"]}'
    result = credibility_connector.get_url_credibility(tweet_url)
    return result


def get_tweets_credibility(tweets, group_method="domain", update_status_fn=None):
    # TODO remove `group_method` param, do both 'domain' and 'source' together?
    if update_status_fn:
        update_status_fn("unshortening the URLs contained in the tweets")
    urls = twitter_connector.get_urls_from_tweets(tweets)

    print("retrieving the domains to assess")
    # let's count the group appearances in all the tweets
    groups_appearances = defaultdict(list)
    if group_method == "domain":
        fn_retrieve_credibility = credibility_connector.post_source_credibility_multiple
    elif group_method == "source":
        fn_retrieve_credibility = credibility_connector.post_source_credibility_multiple
    elif group_method == "url":
        fn_retrieve_credibility = credibility_connector.post_url_credibility_multiple
    else:
        raise ValueError(group_method)
    for url_object in urls:
        url_unshortened = url_object["resolved"]
        if group_method == "domain":
            group = utils.get_url_domain(url_unshortened)
        elif group_method == "source":
            # print(url_unshortened, url_object)
            group = utils.get_url_source(url_unshortened)
        elif group_method == "url":
            group = url_unshortened
        # TODO URL matches, credibility_connector.get_url_credibility(url_unshortened)
        groups_appearances[group].append(url_object["found_in_tweet"])
    credibility_sum = 0
    confidence_sum = 0
    weights_sum = 0
    sources_assessments = []
    print(f"getting credibility for {len(groups_appearances)} groups")
    group_assessments = fn_retrieve_credibility(list(groups_appearances.keys()))
    for group, group_credibility in group_assessments.items():
        if group == "twitter.com":
            continue
        if group_method in ["domain", "source"]:
            frontend_url = f"/misinfo/credibility/sources/{group}"
        else:
            frontend_url = "TODO"
        appearance_cnt = len(groups_appearances[group])
        credibility = group_credibility["credibility"]
        # print(group, credibility)
        credibility_value = credibility["value"]
        confidence = credibility["confidence"]
        if confidence < 0.1:
            continue
        credibility_weight = get_credibility_weight(credibility_value)
        final_weight = credibility_weight * confidence * appearance_cnt
        credibility_sum += credibility_value * final_weight
        confidence_sum += credibility_weight * confidence * appearance_cnt
        weights_sum += credibility_weight * appearance_cnt
        sources_assessments.append(
            {
                "itemReviewed": group,
                "credibility": credibility,
                "tweets_containing": groups_appearances[group],
                "url": frontend_url,
                "credibility_weight": credibility_weight,
                "weights": {
                    #'origin_weight': origin_weight,
                    "final_weight": final_weight
                },
                "assessments": group_credibility["assessments"],
            }
        )
    print(f"retrieved credibility for {len(sources_assessments)} groups")
    if credibility_sum:
        credibility_weighted = credibility_sum / confidence_sum
        confidence_weighted = confidence_sum / weights_sum
    else:
        credibility_weighted = 0.0
        confidence_weighted = 0.0
    return {
        "credibility": {
            "value": credibility_weighted,
            "confidence": confidence_weighted,
        },
        "assessments": sources_assessments  ##{
        #'sources': sources_assessments, # here matches at the source-level
        #'documents': [], # here matches at the document-level
        #'claims': [] # here matches at the claim-level
        # },
        #'itemReviewed': tweet_ids # TODO a link to the tweets
    }


# User credibility


def get_user_credibility_from_user_id(user_id):
    # TODO deprecate, just use the one from screen name
    user = {}  # twitter_connector.(user_id)
    raise NotImplementedError("just use get_user_credibility_from_screen_name")
    return get_user_credibility_from_screen_name(user["screen_name"])


def get_user_credibility_from_screen_name(screen_name, update_status_fn=None):
    if update_status_fn:
        update_status_fn("retrieving the information about the profile")
    itemReviewed = twitter_connector.search_twitter_user_from_screen_name(screen_name)
    if update_status_fn:
        update_status_fn("retrieving the tweets from the profile")
    tweets = twitter_connector.search_tweets_from_screen_name(screen_name)
    itemReviewed["tweets_cnt"] = len(tweets)
    if update_status_fn:
        update_status_fn("unshortening the URLs contained in the tweets")
    urls = twitter_connector.get_urls_from_tweets(tweets)
    itemReviewed["shared_urls_cnt"] = len(urls)
    if update_status_fn:
        update_status_fn("computing the credibility of the profile as a source")
    profile_as_source_credibility = credibility_connector.get_source_credibility(
        f"twitter.com/{screen_name}"
    )
    if update_status_fn:
        update_status_fn(
            "computing the credibility from the sources used in the tweets"
        )
    sources_credibility = get_tweets_credibility(
        tweets, update_status_fn=update_status_fn
    )
    if update_status_fn:
        update_status_fn("computing the credibility from the URLs used in the tweets")
    urls_credibility = get_tweets_credibility(
        tweets, group_method="url", update_status_fn=update_status_fn
    )
    # get_tweets_credibility_directly_reviewed data is already in `profile_as_source_credibility`

    # profile as source: 60% weight
    # urls shared: 25%
    # sources used: 15%
    confidence_weighted = (
        profile_as_source_credibility["credibility"]["confidence"] * 0.6
        + sources_credibility["credibility"]["confidence"] * 0.15
        + urls_credibility["credibility"]["confidence"] * 0.25
    )
    if confidence_weighted:
        value_weighted = (
            profile_as_source_credibility["credibility"]["value"]
            * 0.6
            * profile_as_source_credibility["credibility"]["confidence"]
            + sources_credibility["credibility"]["value"]
            * 0.15
            * sources_credibility["credibility"]["confidence"]
            + urls_credibility["credibility"]["value"]
            * 0.25
            * urls_credibility["credibility"]["confidence"]
        ) / confidence_weighted
    else:
        value_weighted = 0.0
    final_credibility = {"value": value_weighted, "confidence": confidence_weighted}

    result = {
        "credibility": final_credibility,
        "profile_as_source_credibility": profile_as_source_credibility,
        "sources_credibility": sources_credibility,
        "urls_credibility": urls_credibility,
        "itemReviewed": itemReviewed,
    }
    database.save_user_credibility_result(itemReviewed["id"], result)
    return result


def get_user_friends_credibility_from_screen_name(screen_name, limit):
    friends = twitter_connector.search_friends_from_screen_name(screen_name, limit)
    results = []
    for f in friends:
        cached = database.get_user_credibility_result(f["id"])
        if cached and "itemReviewed" in cached.keys():
            result = cached
            result["cache"] = "hit"
            # TODO proper marshalling
            result["updated"] = str(result["updated"])
            result["screen_name"] = result["itemReviewed"]["screen_name"]
            # too many details for the friends, removing them
            del result["profile_as_source_credibility"]
            del result["sources_credibility"]
            del result["urls_credibility"]
        else:
            result = {"cache": "miss", "screen_name": f["screen_name"]}
        results.append(result)
    return results


# Credibility origins
def get_credibility_origins():
    return credibility_connector.get_origins()


def get_factcheckers():
    return credibility_connector.get_factcheckers()


# new analysis for MisinfoMe v2
def get_v2_profile_credibility(screen_name, until_id=None, update_status_fn=None):
    if update_status_fn:
        update_status_fn("retrieving profile")
    profile = twitter_connector.search_twitter_user_from_username_v2(screen_name)
    user_id = profile["id"]
    if update_status_fn:
        update_status_fn("searching for previous analysis")
    # find a previous analysis of this profile
    previous_profile_analysis = database.get_reviewed_profile_v2(user_id)
    # get the tweets that have already been checked
    already_analysed_tweets = list(database.find_reviewed_tweets_v2(user_id))
    tweet_ids_already_analysed = [el["id"] for el in already_analysed_tweets]
    # find directly reviewed tweets
    if update_status_fn:
        update_status_fn("analysing the credibility of the profile")
    profile_credibility = credibility_connector.get_source_credibility(
        f"twitter.com/{screen_name}"
    )
    profile_assessments = profile_credibility["assessments"]
    factchecking = next(
        (el for el in profile_assessments if el["origin_id"] == "factchecking_report"),
        None,
    )
    directly_reviewed_tweets = []
    if factchecking:
        for report in factchecking["reports"]:
            itemReviewed = report["itemReviewed"]
            pieces = itemReviewed.split("/")
            if len(pieces) > 4 and pieces[2] == "twitter.com" and pieces[4] == "status":
                # https://twitter.com/user/status/tweet_id/...
                tweet_id = pieces[5]
                print(itemReviewed, tweet_id)
                # tweet_cred = get_tweets_credibility_directly_reviewed({'id': tweet_id, 'user_screen_name': screen_name})
                #     tweet_cred_full = {
                #         'tweet': twitter_connector.get_tweet(tweet_id),
                #         'urls_credibility': tweet_cred,
                #         'sources_credibility':
                #     }
                #     pass
                print(report)
                # TODO solve this
                # try:
                tweet_cred = get_tweet_credibility_from_id(
                    tweet_id, update_status_fn=update_status_fn
                )
                # except Exception as e:
                #     print(e)
                #     continue
                # TODO attach tweet object, if still available, otherwise leave a "tweet not available" message
                try:  # TODO
                    tweet = twitter_connector.get_tweet(tweet_id)
                except:
                    # the tweet was deleted!!!
                    tweet = {
                        "id": str(tweet_id),
                        "text": None,
                        "retweet": None,
                        "retweet_source_tweet": None,
                        "links": [],
                        "user_id": None,
                        "user_screen_name": screen_name,
                        # 'exception': vars(e)
                    }
                tweet_cred["tweet"] = tweet
                tweet_cred["itemReviewed"] = tweet_id
                print(tweet_id, type(tweet_id))
                directly_reviewed_tweets.append(tweet_cred)
                # TODO add directly reviewed tweets to response!!!

    # get tweets from profile
    # if it is the first request, get_all set to true, otherwise false
    if update_status_fn:
        update_status_fn("getting new tweets from the profile")
    get_all = True if not until_id else False
    tweets_info = twitter_connector.search_tweets_from_user_id_v2(
        user_id, get_all, until_id
    )
    tweets_to_analyse = [
        el for el in tweets_info["tweets"] if el["id"] not in tweet_ids_already_analysed
    ]
    total_tweets = tweets_info["total_tweets"]
    next_until_id = tweets_info["next_until_id"]
    tweets_by_id = {el["id"]: el for el in tweets_to_analyse}

    # analyse the batch of tweets
    if update_status_fn:
        update_status_fn("analysing the credibility of the tweets")
    new_tweets_analysed = get_tweet_credibility_from_dirty_tweet_batch(
        tweets_to_analyse
    )
    # attach the tweet object here
    for el in new_tweets_analysed:
        el["tweet"] = tweets_by_id[el["itemReviewed"]]

    dict_by_id = lambda items: {el["itemReviewed"]: el for el in items}
    # put all together (overwriting) TODO warning directly reviewed may disappear
    all_tweets_reviewed = {
        **dict_by_id(already_analysed_tweets),
        **dict_by_id(new_tweets_analysed),
        **dict_by_id(directly_reviewed_tweets),
    }
    # print(all_tweets_reviewed.keys())
    all_tweets_reviewed = list(all_tweets_reviewed.values())
    # only keep worthy
    print("all_tweets_reviewed", len(all_tweets_reviewed))
    all_tweets_reviewed = [
        el for el in all_tweets_reviewed if el["credibility"]["confidence"] > 0.01
    ]
    print("with a bit of confidence", len(all_tweets_reviewed))
    # sort worst first
    all_tweets_reviewed = sorted(
        all_tweets_reviewed, key=lambda el: el["credibility"]["value"]
    )
    for el in all_tweets_reviewed:
        el["coinform_label"] = get_coinform_label(el["credibility"])
        el["user_id"] = user_id
        el["id"] = el["itemReviewed"]
    # save to DB the reviews from these tweets
    database.save_reviewed_tweets_v2(all_tweets_reviewed)
    # by credibility

    # TODO limit (huge on frontend) and sort
    # TODO select if not_verifiable should be returned or not! (threshold)
    # tweets_to_display = not_credible_tweets + credible_tweets + uncertain_tweets # + not_verifiable_tweets[:100]

    # only show tweets that are verifiable (link-based)
    # tweets_to_display = [el for el in all_tweets_reviewed if el['coinform_label'] != 'not_verifiable']

    # more inclusive filter to display the tweets that are link-based or also source-based but not from factchecking_report
    # tweets_to_display = []
    # for el in all_tweets_reviewed:
    #     if el['coinform_label'] == 'not_verifiable':
    #         tweets_to_display.append(el)
    #     else:
    tweets_to_display = all_tweets_reviewed

    # then sort by default worse first
    tweets_to_display = sorted(
        tweets_to_display, key=lambda el: el["credibility"]["value"]
    )
    # final conversion to easy format
    matching_tweets = []
    not_verifiable_source_tweets = 0
    for el in tweets_to_display:
        sources_info = get_sources_assessments_v2(el)
        links_info = get_links_factchecks_v2(el)
        # # avoid the ones that only have the profile info
        # print(el['tweet']['id'], sources_info, links_info)
        # if not links_info and all(el['source'] == f'twitter.com/{screen_name}' for el in sources_info):
        #     continue
        # avoid the ones that only have factchecking_report info
        keep = True
        # without info
        if not sources_info and not links_info:
            keep = False
        # skip the ones that only have factchecking_report info
        if not links_info:
            for source_info in sources_info:
                assessments = source_info["source_assessments"]
                if (
                    len(assessments) == 1
                    and assessments[0]["origin_id"] == "factchecking_report"
                ):
                    keep = False
                    break
        if keep:
            links_label = "not_verifiable"
            if any(el["coinform_label"] == "not_credible" for el in links_info):
                links_label = "not_credible"
            elif any(el["coinform_label"] == "uncertain" for el in links_info):
                links_label = "uncertain"
            elif any(el["coinform_label"] == "mostly_credible" for el in links_info):
                links_label = "mostly_credible"
            elif any(el["coinform_label"] == "credible" for el in links_info):
                links_label = "credible"
            sources_label = "not_verifiable"
            if any(el["coinform_label"] == "not_credible" for el in sources_info):
                sources_label = "not_credible"
            elif any(el["coinform_label"] == "uncertain" for el in sources_info):
                sources_label = "uncertain"
            elif any(el["coinform_label"] == "mostly_credible" for el in sources_info):
                sources_label = "mostly_credible"
            elif any(el["coinform_label"] == "credible" for el in sources_info):
                sources_label = "credible"
            matching_tweets.append(
                {
                    "tweet": el["tweet"],
                    "coinform_label": el["coinform_label"],
                    "credibility_score": el["credibility"]["value"],
                    "matching_links": links_info,
                    "matching_sources": sources_info,  # TODO
                    "links_label": links_label,
                    "sources_label": sources_label,
                }
            )

    # splitting according to credibility and confidence:
    # - leads to most of the tweets being labelled as not_verifiable
    credible_tweets = [
        el
        for el in matching_tweets
        if el["coinform_label"] in ["credible", "mostly_credible"]
    ]
    not_credible_tweets = [
        el for el in matching_tweets if el["coinform_label"] == "not_credible"
    ]
    not_verifiable_tweets = [
        el for el in matching_tweets if el["coinform_label"] == "not_verifiable"
    ]
    uncertain_tweets = [
        el for el in matching_tweets if el["coinform_label"] == "uncertain"
    ]
    # unknown_tweets_cnt = total_tweets - len(not_credible_tweets + uncertain_tweets + credible_tweets)
    unknown_tweets_cnt = len(all_tweets_reviewed) - len(
        not_credible_tweets + uncertain_tweets + credible_tweets
    )

    # splitting according to credibility score:
    # - leads to less tweets being labelled as not_verifiable
    tweets_positive_credibility_cnt = len(
        [el for el in matching_tweets if el["credibility_score"] > 0.2]
    )
    tweets_negative_credibility_cnt = len(
        [el for el in matching_tweets if el["credibility_score"] <= -0.2]
    )
    tweets_mixed_credibility_cnt = (
        len(matching_tweets)
        - tweets_positive_credibility_cnt
        - tweets_negative_credibility_cnt
    )
    tweets_unknown_credibility_cnt = total_tweets - len(matching_tweets)

    # cut the results to the top 100
    truncated_matching_tweets = []
    for el in matching_tweets:
        keep = True
        # not useful, just keep a few of them
        if not links_info and el["coinform_label"] == "not_verifiable":
            if not_verifiable_source_tweets < 100:
                not_verifiable_source_tweets += 1
            else:
                keep = False
        if keep:
            truncated_matching_tweets.append(el)

    response = {
        "next_until_id": next_until_id,
        "profile": profile,
        "tweets_analysed_stats": {
            "tweets_retrieved_count": total_tweets,
            "tweets_matching_count": len(all_tweets_reviewed),
            "tweets_credible_count": len(credible_tweets),
            "tweets_not_credible_count": len(not_credible_tweets),
            "tweets_mixed_count": len(uncertain_tweets),
            "tweets_unknown_count": unknown_tweets_cnt,
            "tweets_positive_credibility_count": tweets_positive_credibility_cnt,
            "tweets_negative_credibility_count": tweets_negative_credibility_cnt,
            "tweets_mixed_credibility_count": tweets_mixed_credibility_cnt,
            "tweets_unknown_credibility_count": tweets_unknown_credibility_cnt,
        },
        "matching_tweets": truncated_matching_tweets,
    }
    database.save_reviewed_profile_v2(response)
    return response


def get_v2_tweet_credibility(tweet_id):
    tweet_info = twitter_connector.get_tweet_from_id_v2(tweet_id)
    new_tweets_analysed = get_tweet_credibility_from_dirty_tweet_batch([tweet_info])[0]
    # attach the tweet object here
    new_tweets_analysed["tweet"] = tweet_info
    # author object is extra
    author = tweet_info["author"]
    # print(all_tweets_reviewed.keys())
    all_tweets_reviewed = [new_tweets_analysed]
    # all_tweets_reviewed = [
    #     el for el in all_tweets_reviewed if el["credibility"]["confidence"] > 0.01
    # ]
    # sort worst first
    # all_tweets_reviewed = sorted(
    #     all_tweets_reviewed, key=lambda el: el["credibility"]["value"]
    # )
    for el in all_tweets_reviewed:
        el["coinform_label"] = get_coinform_label(el["credibility"])
        el["user_id"] = author["id"]
        el["id"] = el["itemReviewed"]
    # save to DB the reviews from these tweets
    database.save_reviewed_tweets_v2(all_tweets_reviewed)
    # get the sources and links info
    sources_info = get_sources_assessments_v2(new_tweets_analysed)
    links_info = get_links_factchecks_v2(new_tweets_analysed)

    links_label = "not_verifiable"
    if any(el["coinform_label"] == "not_credible" for el in links_info):
        links_label = "not_credible"
    elif any(el["coinform_label"] == "uncertain" for el in links_info):
        links_label = "uncertain"
    elif any(el["coinform_label"] == "mostly_credible" for el in links_info):
        links_label = "mostly_credible"
    elif any(el["coinform_label"] == "credible" for el in links_info):
        links_label = "credible"
    sources_label = "not_verifiable"
    if any(el["coinform_label"] == "not_credible" for el in sources_info):
        sources_label = "not_credible"
    elif any(el["coinform_label"] == "uncertain" for el in sources_info):
        sources_label = "uncertain"
    elif any(el["coinform_label"] == "mostly_credible" for el in sources_info):
        sources_label = "mostly_credible"
    elif any(el["coinform_label"] == "credible" for el in sources_info):
        sources_label = "credible"

    result = {
        "author": author,
        "tweet": el["tweet"],
        "coinform_label": el["coinform_label"],
        "credibility_score": el["credibility"]["value"],
        "matching_links": links_info,
        "matching_sources": sources_info,  # TODO
        "links_label": links_label,
        "sources_label": sources_label,
    }
    return result


def get_links_factchecks_v2(credibility_assessment):
    results = []
    # TODO what about directly reviewed tweets?
    for ass in credibility_assessment.get("urls_credibility", {}).get(
        "assessments", []
    ) + [credibility_assessment.get("tweet_direct_credibility", None)]:
        if not ass:
            continue
        print(ass)
        link = ass["itemReviewed"]
        fact_checks = [
            report for report in ass["assessments"][0]["reports"]
        ]  # assumption that only factchecking_report provides assessments
        results.append(
            {
                "link": link,
                "coinform_label": get_coinform_label(ass["credibility"]),
                "fact_checks": fact_checks,
            }
        )
    return results


def get_sources_assessments_v2(credibility_assessment):
    results = []
    for ass in credibility_assessment.get("sources_credibility", {}).get(
        "assessments", []
    ):
        source = ass["itemReviewed"]
        # TODO factchecking report should be linked to old frontend? Ask to the team
        source_assessments = ass["assessments"]
        results.append(
            {
                "source": source,
                "coinform_label": get_coinform_label(ass["credibility"]),
                "source_assessments": source_assessments,
            }
        )
    return results
