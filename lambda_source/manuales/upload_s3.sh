#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# S3 bucket and path configuration
S3_BUCKET="talma-artifacts"
S3_BASE_PATH="lambda_source_files"

# Array of directories to upload
DIRECTORIES=("app/datasets_local" "app/local_model" "app/local_processor")

# Upload each directory to the corresponding S3 path
for DIR in "${DIRECTORIES[@]}"; do
  if [ -d "$DIR" ]; then
    echo "Uploading $DIR to s3://$S3_BUCKET/$S3_BASE_PATH/$DIR..."
    aws s3 cp "./$DIR" "s3://$S3_BUCKET/$S3_BASE_PATH/$DIR" --recursive
    echo "Successfully uploaded $DIR to S3."
  else
    echo "Directory $DIR does not exist. Skipping..."
  fi
done

echo "All directories uploaded successfully!"
