# main.tf

# ----------------------------
# 1. 配置 AWS Provider
# ----------------------------


provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile  # 新增此行
}


# ----------------------------
# 2. 创建 VPC 网络
# ----------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "jellysillyfish-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.11.0/24", "10.0.12.0/24"]

  enable_nat_gateway = false  # 生产环境建议启用
}

# ----------------------------
# 3. IAM Role & Policy，用于 EC2 访问 S3
# ----------------------------
resource "aws_iam_role" "ec2_role" {
  name = "ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}
# 附加 AmazonEC2InstanceConnect 策略到 EC2 IAM 角色





resource "aws_iam_role_policy_attachment" "ssm_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "ec2_s3_policy" {
  name = "ec2-s3-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      Effect   = "Allow",
      Resource = [
        "arn:aws:s3:::${var.s3_bucket}",
        "arn:aws:s3:::${var.s3_bucket}/*"
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "ec2-instance-profile"
  role = aws_iam_role.ec2_role.name
}

# main.tf

# ----------------------------
# 4. 安全组配置
# ----------------------------

# ALB Security Group
resource "aws_security_group" "alb_sg" {
  name        = "jellysillyfish-alb-sg"
  description = "Security group for ALB"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow inbound HTTP traffic from anywhere"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow inbound HTTPS traffic from anywhere"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
}

# EC2 Security Group
resource "aws_security_group" "ec2_sg" {
  name        = "jellysillyfish-ec2-sg"
  description = "Security group for EC2 instance"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
    description     = "Allow traffic from ALB on port 8000"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow SSH access from specified IP"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
}



# ----------------------------
# 5. 创建 EC2 实例（已修改为 Ubuntu 官方镜像）
# ----------------------------

# 新增：动态获取最新 Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Ubuntu 官方账户 ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "webapp_ec2" {
  ami                    = data.aws_ami.ubuntu.id  # 使用动态获取的 Ubuntu AMI
  instance_type          = var.ec2_instance_type
  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true

  # 新增：Ubuntu 默认用户名是 "ubuntu"，确保 SSH 配置匹配
  key_name               = var.ssh_key_name  # 如果使用 SSH，请取消注释并配置

  iam_instance_profile = aws_iam_instance_profile.ec2_instance_profile.name

  # 注意：Ubuntu 使用 apt 包管理器，确保 setup.sh 脚本兼容
 user_data = base64encode(templatefile("${path.module}/setup.sh", {}))

  tags = {
    Name = "jellysillyfish-ec2-ubuntu"
  }
}

# ----------------------------
# 6. 创建 Target Group 指向 EC2 实例
# ----------------------------
resource "aws_lb_target_group" "ec2_tg" {
  name        = var.target_group_name
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "instance"

  
}

# ----------------------------
# 7. 创建 ALB
# ----------------------------
resource "aws_lb" "alb" {
  name               = var.alb_name
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = false
}

# ----------------------------
# 8. 将 EC2 实例添加到 Target Group 
# ----------------------------
resource "aws_lb_target_group_attachment" "ec2_attachment" {
  target_group_arn = aws_lb_target_group.ec2_tg.arn
  target_id        = aws_instance.webapp_ec2.id
  port             = 8000
}

# ----------------------------
# 9. 创建 ALB Listener (HTTPS)
# ----------------------------
resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate_validation.cert_validation.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ec2_tg.arn
  }

  depends_on = [aws_acm_certificate_validation.cert_validation]
}

# ----------------------------
# 10. 创建 ALB Listener (HTTP -> HTTPS 重定向)
# ----------------------------
resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      protocol    = "HTTPS"
      port        = "443"
      status_code = "HTTP_301"
    }
  }
}

# ----------------------------
# 11. 创建 ACM SSL 证书
# ----------------------------
resource "aws_acm_certificate" "ssl" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# ----------------------------
# 12. 自动创建 DNS 验证记录
# ----------------------------
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.ssl.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = var.hosted_zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 300
}

# ----------------------------
# 13. 等待证书验证完成
# ----------------------------
resource "aws_acm_certificate_validation" "cert_validation" {
  certificate_arn         = aws_acm_certificate.ssl.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# ----------------------------
# 14. Route53 记录指向 ALB
# ----------------------------
resource "aws_route53_record" "api" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.alb.dns_name
    zone_id                = aws_lb.alb.zone_id
    evaluate_target_health = true
  }
}

# ----------------------------
# 15. 输出信息
# ----------------------------
output "ec2_instance_id" {
  description = "The ID of the EC2 instance"
  value       = aws_instance.webapp_ec2.id
}

output "alb_dns_name" {
  description = "The DNS name of the ALB"
  value       = aws_lb.alb.dns_name
}

output "certificate_arn" {
  description = "The ARN of the ACM certificate"
  value       = aws_acm_certificate.ssl.arn
}

output "domain_url" {
  description = "The URL of the deployed API"
  value       = "https://${var.domain_name}"
}
