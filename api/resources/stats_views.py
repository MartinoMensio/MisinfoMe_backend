from fastapi import APIRouter, Query

from ..model import stats_manager


router = APIRouter()


@router.get("/twitter_accounts")
def get_twitter_accounts_stats(
    use_credibility: bool = Query(
        False,
        description="Wether to use the old model (false) or the new one based on credibility (legacy data interface as the old model)",
    )
):
    accounts_stats = stats_manager.get_overall_counts(use_credibility)

    return accounts_stats
