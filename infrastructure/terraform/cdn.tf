variable "origin_domain" {
  type        = string
  description = "DNS name pointing to the ALB, covered by its regional TLS certificate"
}
data "aws_cloudfront_cache_policy" "disabled" { name = "Managed-CachingDisabled" }
data "aws_cloudfront_origin_request_policy" "viewer" { name = "Managed-AllViewer" }
resource "aws_cloudfront_distribution" "web" {
  enabled     = true
  aliases     = [var.domain]
  price_class = "PriceClass_200"
  origin {
    domain_name = var.origin_domain
    origin_id   = "web"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {
    target_origin_id         = "web"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.viewer.id
    compress                 = true
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
  viewer_certificate {
    acm_certificate_arn      = var.cloudfront_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
output "cloudfront_domain" { value = aws_cloudfront_distribution.web.domain_name }
