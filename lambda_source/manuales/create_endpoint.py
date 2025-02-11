import boto3

sagemaker_client = boto3.client("sagemaker", region_name="us-east-1") 

model_name = "visionrag-model"
role_arn = "arn:aws:iam::242201272670:role/SageMakerExecutionRole"
ecr_image_uri = "242201272670.dkr.ecr.us-east-1.amazonaws.com/lambda-container-repo:manuales_dev"


# Create the model in SageMaker
sagemaker_client.create_model(
    ModelName=model_name,
    PrimaryContainer={"Image": ecr_image_uri},
    ExecutionRoleArn=role_arn,
)

# Create endpoint configuration
endpoint_config_name = "visionrag-endpoint-config"
sagemaker_client.create_endpoint_config(
    EndpointConfigName=endpoint_config_name,
    ProductionVariants=[
        {
            "VariantName": "AllTraffic",
            "ModelName": model_name,
            "InstanceType": "ml.c5.xlarge",  # Choose instance type
            "InitialInstanceCount": 1,
            "ContainerStartupHealthCheckTimeoutInSeconds": 600, 
        }
    ],
)

# Deploy the endpoint
endpoint_name = "visionrag-endpoint"
sagemaker_client.create_endpoint(
    EndpointName=endpoint_name,
    EndpointConfigName=endpoint_config_name,
)

print("Endpoint deployment started!")
