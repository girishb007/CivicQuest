terraform {


  required_version = ">= 1.9, < 2.0"
  required_providers {


    aws = {

      source  = "hashicorp/aws",
      version = "~> 5.99"
    }

  }

}
provider "aws" {

  region = var.region
}
variable "region" {

  default = "ap-south-1"
}
variable "name" {

  default = "civicquest"
}
variable "vpc_id" {

  type = string
}
variable "private_subnet_ids" {

  type = list(string)
}
variable "public_subnet_ids" {

  type = list(string)
}
variable "api_image" {

  type = string
}
variable "web_image" {

  type = string
}
variable "domain" {

  type = string
}
variable "alb_certificate_arn" {

  type = string
}
variable "cloudfront_certificate_arn" {

  type = string
}
variable "application_secret_arn" {


  type = string

  description = "Secrets Manager JSON: CQ_DATABASE_URL, CQ_SECRET, CQ_GOOGLE_CLIENT_ID, CQ_GOOGLE_CLIENT_SECRET. Populate after the database exists."

}
variable "approved_public_data" {


  type = bool

  default = false

}
variable "bedrock_model_arn" {

  type = string
}
variable "bedrock_model_id" {

  type = string
}
variable "maptiler_key" {

  type = string
}
variable "alarm_email" {

  type = string
}
variable "enable_schedules" {
  type        = bool
  default     = false
  description = "Enable reviewed retention and reference refresh schedules after networking and operator checks pass."
}
