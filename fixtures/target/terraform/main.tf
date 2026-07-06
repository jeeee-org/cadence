terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}

resource "aws_db_subnet_group" "payments" {
  name       = "payments-db"
  subnet_ids = ["subnet-0a1b2c3d", "subnet-4e5f6a7b"]
}

resource "aws_security_group" "db" {
  name   = "payments-db"
  vpc_id = "vpc-0123abcd"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}
