import os


class Config:
    sos_scraper_environment: str = os.getenv("SOS_SCRAPER_ENVIRONMENT", "local")
    moto_url: str = os.getenv("MOTO_URL", "http://localhost:3000")
    pdp_source_bucket: str = "palm-data-pipeline"


CONFIG = Config()
