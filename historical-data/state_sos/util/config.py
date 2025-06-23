import os


class Config:
    SOS_SCRAPER_ENVIRONMENT: str = os.getenv("SOS_SCRAPER_ENVIRONMENT", "local")


CONFIG = Config()
