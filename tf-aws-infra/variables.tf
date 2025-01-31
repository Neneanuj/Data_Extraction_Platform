# variables.tf


variable "aws_region" {
  description = "AWS region to deploy resources."
  type        = string
  default     = "us-east-1" 
}

variable "aws_profile" {
  description = "The AWS profile to use."
  type        = string
  default     = ""
}


variable "domain_name" {
  description = "The domain name for the API."
  type        = string
}

variable "hosted_zone_id" {
  description = "The Route53 Hosted Zone ID for the domain."
  type        = string
}


variable "ec2_instance_type" {
  description = "The instance type for the EC2 instance."
  type        = string
  default     = "t2.micro"
}



variable "s3_bucket" {
  description = "The S3 bucket name where webapp.zip is stored."
  type        = string
}


variable "allowed_ssh_cidr" {
  description = "The CIDR block that is allowed to SSH into the EC2 instance."
  type        = string
  default     = "YOUR_IP_ADDRESS/32" 
}

variable "ssh_key_name" {
  description = "The name of the SSH key pair to access the EC2 instance."
  type        = string
  default     = "" 
}


variable "alb_name" {
  description = "The name of the Application Load Balancer."
  type        = string
  default     = "jellysillyfish-alb"
}

variable "target_group_name" {
  description = "The name of the Target Group."
  type        = string
  default     = "jellysillyfish-ec2-tg"
}



