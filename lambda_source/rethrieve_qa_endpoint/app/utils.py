import boto3
import json

sns_client = boto3.client('sns')

def send_sns_message(topic_arn, message_dict, subject="Notification"):
    """
    Sends a JSON-formatted message to an SNS topic.

    :param topic_arn: ARN of the SNS topic
    :param message_dict: Dictionary containing the message payload
    :param subject: Subject of the message (optional)
    """
    message_json = json.dumps(message_dict)
    
    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=message_json,
        Subject=subject,
        MessageStructure="json"
    )
    
    return response
