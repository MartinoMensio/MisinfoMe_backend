from ..data import database


def get_overall_counts(use_credibility):
    if use_credibility:
        counts = database.get_all_user_credibility()
    else:
        counts = database.get_all_counts()
    counts = [el for el in counts]
    score = 50
    if len(counts):
        score = sum(c.get("score", 0) for c in counts) / len(counts)
    return {
        "tweets_cnt": sum(c.get("tweets_cnt", 0) for c in counts),
        "shared_urls_cnt": sum(c.get("shared_urls_cnt", 0) for c in counts),
        "verified_urls_cnt": sum(c.get("verified_urls_cnt", 0) for c in counts),
        "mixed_urls_cnt": sum(c.get("mixed_urls_cnt", 0) for c in counts),
        "fake_urls_cnt": sum(c.get("fake_urls_cnt", 0) for c in counts),
        "unknown_urls_cnt": sum(c.get("unknown_urls_cnt", 0) for c in counts),
        "score": score,
        "twitter_profiles_cnt": len(counts),
    }
