# sos-scraper

## Development
Please follow the following process when contributing to this project:
1. Create a new branch with the ticket number and a short description. For example, if your ticket is https://linear.app/palmfi/issue/PAL-2105/scrape-delaware, create a branch called `PAL-2105_add_delaware_historical_scraper`.
2. Make and test your changes locally, committing your changes to your ticket's branch periodically along the way.
3. When your work is ready for a review and merge, please push your branch to github and open a pull request against the `main` branch and request a review.
4. Tag a teammate on the pull request, and after they've reviewed the changes, merge the pull request into `main`.

## Deployment
### Real Time Scrapers
Real time scrapers (files in `real-time/`) are deployed as lambda functions in AWS. New lambdas and updates to existing 
lambdas in the `real-time/{state}/` subdirectories are deployed automatically upon a merge into the `main` branch. These can also 
be deployed via a manual dispatch of the `Real-Time Lambda Deploy` GitHub Action. 

The deployment pipeline does not currently support the following and will require additional work to support (as of Jun 
16, 2025):
- New layers
- New scrapers that use a docker image (automated updates to the existing real-time scraper with a docker image are supported)

### Long Running Scrapers
Long Running/Historical Data scrapers (files in the `historical-data`) are packaged into a Docker image and pushed to 
ECR when a branch is merged into `main`. This can also be triggered by a manual dispatch of the Historical Data Package 
and Deploy GitHubAction.

Additional features (i.e. running the dockerized scrapers in ECS, writing scraper output to S3) coming soon.
