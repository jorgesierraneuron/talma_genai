#!/bin/bash

# Usage: ./deploy.sh -dev/-test/-prod

if [ $# -ne 1 ]; then
  echo "Usage: $0 -dev | -test | -prod"
  exit 1
fi

# Extract environment
case "$1" in
  -dev)
    ENV="dev"
    ;;
  -test)
    ENV="test"
    ;;
  -prod)
    ENV="prod"
    ;;
  *)
    echo "Invalid option: $1. Use -dev, -test, or -prod"
    exit 1
    ;;
esac

echo "Deploying Terraform for environment: $ENV"

# Navigate to the templates directory (assumes deploy.sh is inside setup folder)
cd "$(dirname "$0")/../templates" || { echo "Failed to change directory to templates"; exit 1; }

# Update terraform.tfvars with the selected environment
sed -i "s/^env = \".*\"/env = \"$ENV\"/" terraform.tfvars

# Initialize Terraform
terraform init

# Apply Terraform configuration
if terraform apply -var-file=terraform.tfvars -auto-approve; then
  echo "Terraform deployment for $ENV completed successfully!"
else
  echo "Terraform deployment for $ENV failed!"
  exit 1
fi
