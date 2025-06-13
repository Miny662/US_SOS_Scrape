import json

from scraper import Scraper


def lambda_handler(event, context):
    # TODO implement
    items = {}
    if "queryStringParameters" in event:
        print(event["queryStringParameters"])
        items = Scraper(event["queryStringParameters"]).parser()
    return {
        'statusCode': 200,
        'body': json.dumps(items)
    }