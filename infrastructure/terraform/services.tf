resource "aws_ecs_cluster" "main" {


  name = var.name
  setting {

    name  = "containerInsights"
    value = "enabled"
  }

}
resource "aws_cloudwatch_log_group" "app" {


  for_each = toset(keys(local.commands))

  name = "/ecs/${var.name}/${each.key}"

  retention_in_days = 14

}
resource "aws_iam_role" "execution" {


  name_prefix = "${var.name}-execution-"

  assume_role_policy = jsonencode({

    Version = "2012-10-17",
    Statement = [{

      Effect = "Allow",
      Principal = {

        Service = "ecs-tasks.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })

}
resource "aws_iam_role_policy_attachment" "execution" {


  role = aws_iam_role.execution.name

  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"

}
resource "aws_iam_role_policy" "secrets" {


  role = aws_iam_role.execution.name

  policy = jsonencode({

    Version = "2012-10-17",
    Statement = [{

      Effect   = "Allow",
      Action   = ["secretsmanager:GetSecretValue"],
      Resource = var.application_secret_arn
    }]
  })

}
resource "aws_iam_role" "app" {


  name_prefix = "${var.name}-app-"

  assume_role_policy = aws_iam_role.execution.assume_role_policy

}
resource "aws_iam_role_policy" "app" {


  role = aws_iam_role.app.name

  policy = jsonencode({

    Version = "2012-10-17",
    Statement = [
      {

        Effect   = "Allow",
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
        Resource = [for bucket in aws_s3_bucket.media : "${bucket.arn}/*"]
      },
      {

        Effect   = "Allow",
        Action   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:ChangeMessageVisibility", "sqs:GetQueueAttributes"],
        Resource = aws_sqs_queue.jobs.arn
      },
      {

        Effect   = "Allow",
        Action   = ["bedrock:InvokeModel"],
        Resource = var.bedrock_model_arn
      }
    ]
  })

}
locals {


  app_environment = {


    CQ_ENV = "production"

    CQ_DEMO_MODE = "false"

    CQ_ORIGIN = "https://${var.domain}"

    CQ_CATCHES_PUBLIC = "false"

    CQ_PUBLIC_DATA_APPROVED = tostring(var.approved_public_data)

    CQ_STORAGE = "s3"

    CQ_AWS_REGION = var.region

    CQ_ORIGINAL_BUCKET = aws_s3_bucket.media["originals"].id

    CQ_DERIVATIVE_BUCKET = aws_s3_bucket.media["derivatives"].id

    CQ_QUEUE_MODE = "sqs"

    CQ_SQS_ENDPOINT = ""

    CQ_QUEUE_URL = aws_sqs_queue.jobs.url

    CQ_REDIS_URL = "rediss://${aws_elasticache_replication_group.main.primary_endpoint_address}:6379/0"

    CQ_BEDROCK_MODEL_ID = var.bedrock_model_id

    CQ_MAPTILER_KEY = var.maptiler_key

  }

  commands = {


    api = ["uvicorn", "civicquest.main:app", "--host", "0.0.0.0", "--port", "8000"]

    worker = ["civicquest", "worker"]

    migration = ["alembic", "upgrade", "head"]

    retention = ["civicquest", "retention"]

    reference_refresh = ["civicquest", "refresh-reference"]

    web = ["node", "apps/web/server.js"]

  }

}

resource "aws_iam_role" "scheduler" {
  name_prefix = "${var.name}-scheduler-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler" {
  role = aws_iam_role.scheduler.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["ecs:RunTask"]
        Resource = [aws_ecs_task_definition.app["retention"].arn,
                    aws_ecs_task_definition.app["reference_refresh"].arn]
      },
      {
        Effect = "Allow"
        Action = ["iam:PassRole"]
        Resource = [aws_iam_role.execution.arn, aws_iam_role.app.arn]
      }
    ]
  })
}

locals {
  scheduled_tasks = {
    retention = {
      expression = "rate(1 day)"
      task       = "retention"
    }
    reference-refresh = {
      expression = "cron(0 3 1 * ? *)"
      task       = "reference_refresh"
    }
  }
}

resource "aws_scheduler_schedule" "maintenance" {
  for_each = local.scheduled_tasks
  name     = "${var.name}-${each.key}"
  state    = var.enable_schedules ? "ENABLED" : "DISABLED"
  flexible_time_window { mode = "OFF" }
  schedule_expression          = each.value.expression
  schedule_expression_timezone = "Asia/Kolkata"
  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.scheduler.arn
    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.app[each.value.task].arn
      launch_type         = "FARGATE"
      network_configuration {
        subnets          = var.private_subnet_ids
        security_groups  = [aws_security_group.app.id]
        assign_public_ip = false
      }
    }
  }
}
resource "aws_ecs_task_definition" "app" {


  for_each = local.commands

  family = "${var.name}-${each.key}"

  network_mode = "awsvpc"

  requires_compatibilities = ["FARGATE"]

  cpu = "512"

  memory = "1024"

  execution_role_arn = aws_iam_role.execution.arn

  task_role_arn = each.key == "web" ? null : aws_iam_role.app.arn

  container_definitions = jsonencode([{


    name = each.key

    image = each.key == "web" ? var.web_image : var.api_image

    essential = true

    command = each.value

    portMappings = each.key == "web" ? [{

      containerPort = 3000,
      protocol      = "tcp"
      }] : (each.key == "api" ? [{

        containerPort = 8000,
        protocol      = "tcp"
    }] : [])

    environment = each.key == "web" ? [{

      name  = "API_INTERNAL_URL",
      value = "http://api.${var.name}.internal:8000"
      }] : [for name, value in local.app_environment : {

      name  = name,
      value = value
    }]

    secrets = each.key == "web" ? [] : [for key in ["CQ_DATABASE_URL", "CQ_SECRET", "CQ_GOOGLE_CLIENT_ID", "CQ_GOOGLE_CLIENT_SECRET"] : {

      name      = key,
      valueFrom = "${var.application_secret_arn}:${key}::"
    }]

    logConfiguration = {

      logDriver = "awslogs",
      options = {

        awslogs-group         = aws_cloudwatch_log_group.app[each.key].name,
        awslogs-region        = var.region,
        awslogs-stream-prefix = each.key
      }
    }

  }])

}
resource "aws_ecs_service" "app" {


  for_each = toset(["api", "work