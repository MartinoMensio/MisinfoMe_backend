# Backend

The backend is a REST service that:

- receives requests for a specific twitter account (username/tokens)
- retrieves the tweets for the specified user
- compares them with the aggregated dataset of fake/true
- provides back a measure of gullibility

Things to consider:

- which platform
  - free, fast, languages
- caching / storing results
