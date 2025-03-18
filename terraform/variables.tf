variable "aws_region" {
  type    = string
  default = ""
}

variable "db_username" {
  type    = string
  default = "root"
}

variable "db_password" {
  type      = string
  sensitive = true
  nullable  = false
}

variable "db_name" {
  type    = string
  default = "primal"
}

variable "monthly_budget_amount" {
  type    = number
  default = 100
}

variable "budget_alert_email" {
  description = "email address for budget alerts"
  type        = string
}

variable "environment" {
  type    = string
  default = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be either dev, staging, or prod"
  }
}

variable "access_key" {
  type      = string
  sensitive = true
}

variable "secret_key" {
  type      = string
  sensitive = true
}