resource "aws_iam_role" "lambda_role" {
  name               = var.role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# Attach AWS Lambda Basic Execution Role
resource "aws_iam_policy_attachment" "lambda_basic_execution" {
  name       = "${var.role_name}_basic_execution"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allow Lambda to Invoke SageMaker Endpoints
resource "aws_iam_role_policy" "sagemaker_invoke" {
  name   = "${var.role_name}_sagemaker_invoke"
  role   = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sagemaker:InvokeEndpoint"
        Resource = "arn:aws:sagemaker:${var.aws_region}:${var.aws_account_id}:endpoint/*"
      }
    ]
  })
}


resource "aws_iam_policy" "lambda_sqs_policy" {
  name        = "${var.role_name}_sqs_access"
  description = "Allow Lambda to read messages from SQS"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ],
        Resource = "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:${var.sqs_queue_name}"
      }
    ]
  })
}

# Attach the SQS policy to the Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_sqs_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_sqs_policy.arn
}


<<<<<<< Updated upstream
=======
# ✅ Allow Lambda to Retrieve Secrets from Secrets Manager
resource "aws_iam_role_policy" "secretsmanager_access" {
  name   = "${var.role_name}_secretsmanager_access"
  role   = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "dynamodb_access" {
  name   = "${var.role_name}_dynamodb_access"
  role   = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:${var.aws_account_id}:table/*"
      }
    ]
  })
}
>>>>>>> Stashed changes
