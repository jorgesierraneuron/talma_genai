resource "aws_iam_role" "lambda_role" {
  name               = var.role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

# IAM Trust Policy for Lambda
data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ✅ Attach AWS Lambda Basic Execution Role (for logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ✅ Allow Lambda to Invoke SageMaker Endpoints
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

# ✅ **SNS Policy for Lambda (Publish & Subscribe)**
resource "aws_iam_policy" "lambda_sns_policy" {
  name        = "${var.role_name}_sns_access"
  description = "Allow Lambda to publish and subscribe to SNS"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "sns:Publish",
          "sns:Subscribe"
        ],
        Resource = "arn:aws:sns:${var.aws_region}:${var.aws_account_id}:*"
      }
    ]
  })
}

# ✅ Attach the SNS policy to the Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_sns_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_sns_policy.arn
}

# ✅ **Allow SNS to Invoke All Lambda Functions**
resource "aws_lambda_permission" "sns_lambda_invoke_all" {
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = "arn:aws:sns:${var.aws_region}:${var.aws_account_id}:${var.sns_topic_name}"
}

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
