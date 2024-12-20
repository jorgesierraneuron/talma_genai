#!/bin/bash

# Variables
AWS_REGION="us-east-1" # Cambia esto a tu región
AWS_ACCOUNT_ID="<account_id>" # Reemplaza con tu ID de cuenta AWS
ECR_REPO_NAME="lambda-container-repo" # Nombre del repositorio ECR
TERRAFORM_DIR="." # Directorio donde están los archivos de Terraform

# Imágenes
IMAGES=("clean-files" "convert-json")

# Login en ECR
echo "Autenticando Docker en ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Crear repositorio ECR si no existe
echo "Creando el repositorio ECR si no existe..."
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION >/dev/null 2>&1 || \
aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

# Construir y subir imágenes
for IMAGE in "${IMAGES[@]}"; do
    echo "Construyendo la imagen Docker para $IMAGE..."
    docker build -t $IMAGE ./$IMAGE

    echo "Etiquetando la imagen $IMAGE..."
    docker tag $IMAGE:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:$IMAGE

    echo "Subiendo la imagen $IMAGE a ECR..."
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:$IMAGE
done

# Desplegar Terraform
echo "Inicializando Terraform..."
cd $TERRAFORM_DIR
terraform init

echo "Revisando el plan de Terraform..."
terraform plan

echo "Aplicando Terraform para desplegar la infraestructura..."
terraform apply -auto-approve

echo "Despliegue completado exitosamente 🚀"
