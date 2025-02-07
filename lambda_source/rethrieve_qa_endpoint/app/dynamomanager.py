import boto3
from botocore.exceptions import BotoCoreError, ClientError
import hashlib

class DynamoDBManager:
    def __init__(self, table_name, region_name='us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def upload_item(self, item_data):
        """
        Upload an item to DynamoDB.
        :param pk: Primary key value.
        :param item_data: Dictionary containing item attributes.
        """
        try:
            #item_data['pk'] = pk  # Ensure PK is included
            self.table.put_item(Item=item_data)
            return {"message": "Item uploaded successfully"}
        except (BotoCoreError, ClientError) as e:
            return {"error": str(e)}

    def retrieve_item(self, pk):
        """
        Retrieve an item from DynamoDB.
        :param pk: Primary key value.
        :return: Dictionary containing the item data or an error message.
        """
        try:
            response = self.table.get_item(Key={'id_generation': pk})
            return response.get('Item', {})
        except (BotoCoreError, ClientError) as e:
            return {"error": str(e)}

    def update_item(self, pk, update_data):
        """
        Update an item in DynamoDB.
        :param pk: Primary key value.
        :param update_data: Dictionary containing attributes to update.
        """
        try:
            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in update_data.keys())
            expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
            expression_attribute_values = {f":{k}": v for k, v in update_data.items()}
            
            self.table.update_item(
                Key={'id_generation': pk},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            return {"message": "Item updated successfully"}
        except (BotoCoreError, ClientError) as e:
            return {"error": str(e)}
        
    @staticmethod
    def generate_unique_id(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:8]  # Take the first 8 characters


