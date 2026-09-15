# Uses an operator-provided VPC with two private AZ subnets and outbound NAT or
# AWS service endpoints. No infrastructure is created merely by validating this module.
resource "aws_security_group" "edge" {


  name_prefix = "${var.name}-edge-"

  vpc_id = var.vpc_id
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
resource "aws_security_group" "app" {


  name_prefix = "${var.name}-app-"

  vpc_id = var.vpc_id
  ingress {

    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.edge.id]
  }
  ingress {

    from_port = 8000
    to_port   = 8000
    protocol  = "tcp"
    self      = true
  }
  egress {

    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

}
resource "aws_security_group" "data" {


  name_prefix = "${var.name}-data-"

  vpc_id = var.vpc_id
  ingress {

    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  ingress {

    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

}
resource "aws_lb" "web" {


  name = var.name

  internal = false

  load_balancer_type = "application"

  security_groups = [aws_security_group.edge.id]

  subnets = var.public_subnet_ids

}
resource "aws_lb_target_group" "web" {


  name = var.name

  port = 3000

  protocol = "HTTP"

  target_type = "ip"

  vpc_id = var.vpc_id
  health_check {

    path    = "/offline.html"
    matcher = "200"
  }

}
resource "aws_lb_listener" "https" {


  load_balancer_arn = aws_lb.web.arn

  port = 443

  protocol = "HTTPS"

  ssl_policy = "ELBSecurityPolicy-TLS13-1-2-2021-06"

  certificate_arn = var.alb_certificate_arn
  default_action {

    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }

}
resource "aws_service_discovery_private_dns_namespace" "main" {


  name = "${var.name}.internal"

  vpc = var.vpc_id

}
resource "aws_service_discovery_service" "api" {


  name = "api"
  dns_config {


    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    dns_records {

      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"

  }
  health_check_custom_config {

    failure_threshold = 1
  }

}
