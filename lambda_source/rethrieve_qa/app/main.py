import json
import pandas as pd

def handler(event, context):
    """
    A simple AWS Lambda function example.
    """
    # Extract name from the event
    name = event.get('name', 'From QA')
    
    # Create a response
    response = {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Hello, {name}!"
        })
    }
    return response
