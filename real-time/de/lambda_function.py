import json

from scraper import Scraper


def lambda_handler(event, context):
    # TODO implement
    items = {}
    if "queryStringParameters" in event:
        try:
            print(event["queryStringParameters"])
            params = event["queryStringParameters"]
            id = params.get("id", None)
            items = Scraper(id).parser()
        except:
            pass
    return {
        'statusCode': 200,
        'body': json.dumps(items)
    }