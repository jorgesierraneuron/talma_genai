terraform {
  backend "s3" {
    bucket         = "talmaai-artifacts-dev"
    key            = "rethrieve_qa/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}
