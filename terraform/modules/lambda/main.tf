resource "aws_lambda_function" "lambda_function" {
  function_name = var.function_name
  role          = var.iam_role_arn
  package_type  = "Image"
  image_uri     = var.image_uri
  timeout       = var.timeout

  environment {
    variables = var.environment
  }
}



