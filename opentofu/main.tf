# Terraform configuration for AI Tuber GCP deployment
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-northeast1-a"
}

variable "bucket_name" {
  description = "GCS Bucket name for shared data"
  type        = string
}


variable "enable_spot_instance" {
  description = "Whether to use Spot instance for cost savings (risk of preemption during stream)"
  type        = bool
  default     = true
}

variable "repository_name" {
  description = "Artifact Registry repository name"
  type        = string
  default     = "ai-tuber"
}

variable "admin_ip_ranges" {
  description = "List of IP ranges allowed to access administrative ports (e.g. VNC)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Default to open, but should be overridden in terraform.tfvars
}

variable "character_name" {
  description = "Name of the character (e.g. ren)"
  type        = string
  default     = "ren"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "workflows" {
  service            = "workflows.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "workflowexecutions" {
  service            = "workflowexecutions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "vpcaccess" {
  service            = "vpcaccess.googleapis.com"
  disable_on_destroy = false
}
