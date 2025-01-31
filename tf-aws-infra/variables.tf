# variables.tf

# AWS 区域
variable "aws_region" {
  description = "AWS region to deploy resources."
  type        = string
  default     = "us-east-1"  # 可以根据需求调整
}

variable "aws_profile" {
  description = "The AWS profile to use."
  type        = string
  default     = ""  # 默认空，表示使用默认配置
}

# 域名相关配置
variable "domain_name" {
  description = "The domain name for the API."
  type        = string
}

variable "hosted_zone_id" {
  description = "The Route53 Hosted Zone ID for the domain."
  type        = string
}

# EC2 实例配置
variable "ec2_instance_type" {
  description = "The instance type for the EC2 instance."
  type        = string
  default     = "t2.micro"  # 根据需求调整
}


# S3 存储桶名称（用于存放 webapp.zip）
variable "s3_bucket" {
  description = "The S3 bucket name where webapp.zip is stored."
  type        = string
}

# SSH 访问配置
variable "allowed_ssh_cidr" {
  description = "The CIDR block that is allowed to SSH into the EC2 instance."
  type        = string
  default     = "YOUR_IP_ADDRESS/32"  # 替换为你的 IP 地址
}

variable "ssh_key_name" {
  description = "The name of the SSH key pair to access the EC2 instance."
  type        = string
  default     = ""  # 如果需要 SSH 访问，请设置键名称，否则保持为空
}

# ALB 配置
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



