provider "aws" {
  region = "us-east-1" 
}

resource "aws_vpc" "my_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "MyVPC"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id     = aws_vpc.my_vpc.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "PublicSubnet"
  }
}

resource "aws_instance" "api_instance" {
  ami           = "ami-0c55b159cbfafe1f0"  
  instance_type = "t2.micro"              
  key_name      = "mykey"                 

  vpc_security_group_ids = [aws_security_group.api_sg.id]

  tags = {
    Name = "API Server"
  }
}

resource "aws_security_group" "api_sg" {
  name        = "api-security-group"
  description = "Security group for API instance with HTTPS access"
  vpc_id      = "vpc-123abc"  # 指定VPC ID

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elb" "api_elb" {
  name               = "api-load-balancer"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  listener {
    instance_port     = 80
    instance_protocol = "HTTP"
    lb_port           = 443
    lb_protocol       = "HTTPS"
    ssl_certificate_id = aws_acm_certificate.ssl_cert.arn
  }
}

resource "aws_acm_certificate" "ssl_cert" {
  domain_name       = "dev.jellysillyfish.me"
  validation_method = "DNS"
}

resource "aws_route53_record" "cert_validation" {
  zone_id = aws_route53_zone.my_zone.id
  name    = aws_acm_certificate.ssl_cert.domain_validation_options.0.resource_record_name
  type    = aws_acm_certificate.ssl_cert.domain_validation_options.0.resource_record_type
  records = [aws_acm_certificate.ssl_cert.domain_validation_options.0.resource_record_value]
  ttl     = 60
}



