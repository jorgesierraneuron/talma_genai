terraform {
  backend "s3" {
    bucket         = "talmaai-artifacts-dev"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}
