#!/bin/bash
set -e

# Configuración
ENV="dev"
AWS_REGION="us-east-1"
ECR_REPO_NAME="lambda-container-repo"
DOCKER_TAG_RETHRIEVE_QA="rethrieve_qa_test_${ENV}"
DOCKER_TAG_JSON_TO_KNOWLEDGE="json_to_knowledge_${ENV}"
DOCKER_TAG_MANUALES="manuales_${ENV}"
DOCKER_TAG_MANUALES_TEST="manuales_test_${ENV}"


# Retrieve AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

if [ -z "$ACCOUNT_ID" ]; then
  echo "Error: No se pudo obtener el AWS Account ID. Verifica tus credenciales de AWS."
  exit 1
fi

ECR_URL="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

# 1. Construir y subir imágenes a ECR
function upload_to_ecr() {
  echo "Autenticando con ECR..."
  aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

  #aws ecr create-repository --repository-name lambda-container-repo --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE --region $AWS_REGION


  # echo "Construyendo imagen para rethriever_qa..."
  # docker build --platform linux/amd64 -t $ECR_REPO_NAME:$DOCKER_TAG_RETHRIEVE_QA ./lambda_source/rethrieve_qa
  # docker tag $ECR_REPO_NAME:$DOCKER_TAG_RETHRIEVE_QA "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$ECR_REPO_NAME:$DOCKER_TAG_RETHRIEVE_QA"
  # docker push "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$ECR_REPO_NAME:$DOCKER_TAG_RETHRIEVE_QA"  


  # echo "Construyendo imagen para json_to_knowledge..."
  # docker build --platform linux/amd64 -t $ECR_REPO_NAME:$DOCKER_TAG_JSON_TO_KNOWLEDGE ./lambda_source/json_to_knowledge
  # docker tag $ECR_REPO_NAME:$DOCKER_TAG_JSON_TO_KNOWLEDGE "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$ECR_REPO_NAME:$DOCKER_TAG_JSON_TO_KNOWLEDGE"
  # docker push "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$ECR_REPO_NAME:$DOCKER_TAG_JSON_TO_KNOWLEDGE"

  echo "Construyendo imagen para manuales..."
  DOCKER_DEFAULT_PLATFORM=linux/amd64
  docker buildx build -o type=image,oci-mediatypes=false --platform linux/amd64/v2 -t $ECR_REPO_NAME:$DOCKER_TAG_MANUALES ./lambda_source/manuales
  docker tag $ECR_REPO_NAME:$DOCKER_TAG_MANUALES "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$ECR_REPO_NAME:$DOCKER_TAG_MANUALES"
  docker push "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$ECR_REPO_NAME:$DOCKER_TAG_MANUALES"

  # echo "Construyendo imagen para manuales test..."
  # docker build --platform linux/amd64 -t $ECR_REPO_NAME:$DOCKER_TAG_MANUALES_TEST ./lambda_source/manuales_test
  # docker tag $ECR_REPO_NAME:$DOCKER_TAG_MANUALES_TEST "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$ECR_REPO_NAME:$DOCKER_TAG_MANUALES_TEST"
  # docker push "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$ECR_REPO_NAME:$DOCKER_TAG_MANUALES_TEST"

}



# 2. Desplegar Terraform
function deploy_terraform() {
  echo "Inicializando Terraform..."
  cd ./terraform || { echo "Error: No se pudo acceder al directorio ./terraform"; exit 1; }

  echo "Ejecutando terraform init..."
  terraform init || { echo "Error: terraform init falló"; exit 1; }

  echo "Ejecutando terraform plan..."
  terraform plan -out=tfplan || { echo "Error: terraform plan falló"; exit 1; }

  echo "Aplicando infraestructura con terraform apply..."
  terraform apply -auto-approve tfplan || { echo "Error: terraform apply falló"; exit 1; }

  cd - || { echo "Error: No se pudo volver al directorio anterior"; exit 1; }
}


# Ejecutar
upload_to_ecr
#deploy_terraform
