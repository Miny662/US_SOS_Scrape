# sos-scraper

## Deployment
Real time scrapers (files in `real-time/`) are deployed as lambda functions in AWS. New lambdas and updates to existing 
lambdas in the `real-time/{state}/` subdirectories are deployed automatically upon a merge into the `main` branch. These can also 
be deployed via a manual dispatch of the `Real-Time Lambda Deploy` GitHub Action. 

The deployment pipeline does not currently support the following and will require additional work to support (as of Jun 
16, 2025):
- New layers
- New scrapers that use a docker image (automated updates to the existing real-time scraper with a docker image are supported)