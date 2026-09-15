resource "aws_s3_bucket" "media" {


  for_each = toset(["originals", "derivatives"])

  bucket_prefix = "${var.name}-${each.key}-"

}
resource "aws_s3_bucket_public_access_block" "media" {


  for_each = aws_s3_bucket.media

  bucket = each.value.id

  block_public_acls = true

  block_public_policy = true

  ignore_public_acls = true

  restrict_public_buckets = true

}
resource "aws_s3_bucket_server_side_encryption_configuration" "media" {


  for_each = aws_s3_bucket.media

  bucket = each.value.id
  rule {
    apply_server_side_encryption_by_default {

      sse_algorithm = "AES256"
    }
  }

}
resource "aws_s3_bucket_versioning" "media" {


  for_each = aws_s3_bucket.media

  bucket = each.value.id
  versioning_configuration {

    status = "Enabled"
  }

}
resource "aws_s3_bucket_cors_configuration" "originals" {


  bucket = aws_s3_bucket.media["originals"].id
  cors_rule {


    allowed_headers = ["content-type"]

    allowed_methods = ["PUT"]

    allowed_origins = ["https://${var.domain}"]

    max_age_seconds = 300

  }

}
resource "aws_s3_bucket_lifecycle_configuration" "media" {


  for_each = aws_s3_bucket.media

  bucket = each.value.id
  rule {


    id = "expired-versions"

    status = "Enabled"
    filter {

      prefix = ""
    }
    noncurrent_version_expiration {

      noncurrent_days = 30
    }
    abort_incomplete_multipart_upload {

      days_after_initiation = 1
    }

  }
  rule {


    id = "unclaimed-staging"

    status = "Enabled"
    filter {

      prefix = "staging/"
    }
    expiration {

      days = 1
    }

  }

}
resource "aws_sqs_queue" "dead" {


  name = "${var.name}-dead"

  message_retention_seconds = 1209600

  sqs_managed_sse_enabled = true

}
resource "aws_sqs_queue" "jobs" {


  name = "${var.name}-jobs"

  visibility_timeout_seconds = 120

  message_retention_seconds = 1209600

  sqs_managed_sse_enabled = true

  redrive_policy = jsonencode({

    deadLetterTargetArn = aws_sqs_queue.dead.arn,
    maxReceiveCount     = 10
  })

}
resource "aws_db_subnet_group" "main" {


  name = var.name

  subnet_ids = var.private_subnet_ids

}
resource "aws_db_instance" "main" {


  identifier = var.name

  engine = "postgres"

  engine_version = "16"

  instance_class = "db.t4g.small"

  allocated_storage = 30

  max_allocated_storage = 100

  storage_encrypted = true

  db_name = "civicquest"

  username = "civicquest"

  manage_master_user_password = true

  multi_az = true

  publicly_accessible = false

  db_subnet_group_name = aws_db_subnet_group.main.name

  vpc_security_group_ids = [aws_security_group.data.id]

  backup_retention_period = 7

  deletion_protection = true

  skip_final_snapshot = false

  final_snapshot_identifier = "${var.name}-final"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

}
resource "aws_elasticache_subnet_group" "main" {


  name = var.name

  subnet_ids = var.private_subnet_ids

}
resource "aws_elasticache_replication_group" "main" {


  replication_group_id = var.name

  description = "CivicQuest rebuildable caches and rate limits"

  engine = "redis"

  engine_version = "7.1"

  node_type = "cache.t4g.micro"

  num_cache_clusters = 2

  automatic_failover_enabled = true

  multi_az_enabled = true

  at_rest_encryption_enabled = true

  transit_encryption_enabled = true

  subnet_group_name = aws_elasticache_subnet_group.main.name

  security_group_ids = [aws_security_group.data.id]

  snapshot_retention_limit = 1

}
