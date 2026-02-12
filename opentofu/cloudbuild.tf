# Cloud Build Triggers for CI/CD

# Variables for Repository
variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "" # Should be set in terraform.tfvars
}

variable "github_repo_name" {
  description = "GitHub repository name"
  type        = string
  default     = "ai-tuber"
}

# 1. Trigger for SaintGraph (Soul/Mind Engine)
resource "google_cloudbuild_trigger" "saint_graph_trigger" {
  name        = "ai-tuber-saint-graph"
  description = "Build and deploy SaintGraph on changes in src/saint_graph/ or src/infra/"

  github {
    owner = var.github_owner
    name  = var.github_repo_name
    push {
      branch = "^main$|^master$|^dev/.*$" # Trigger on main/master/dev branches
    }
  }

  included_files = [
    "src/saint_graph/**",
    "src/infra/**",
    "cloudbuild-saint-graph.yaml"
  ]

  filename = "cloudbuild-saint-graph.yaml"

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = var.repository_name
  }
}

# 2. Trigger for Body (Streaming Control)
resource "google_cloudbuild_trigger" "body_trigger" {
  name        = "ai-tuber-body"
  description = "Build and push Body streamer on changes in src/body/ or src/infra/"

  github {
    owner = var.github_owner
    name  = var.github_repo_name
    push {
      branch = "^main$|^master$|^dev/.*$"
    }
  }

  included_files = [
    "src/body/**",
    "src/infra/**",
    "cloudbuild-body.yaml"
  ]

  filename = "cloudbuild-body.yaml"

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = var.repository_name
  }
}

# 3. Trigger for News Collector
resource "google_cloudbuild_trigger" "news_collector_trigger" {
  name        = "ai-tuber-news-collector"
  description = "Build and deploy News Collector on changes in scripts/news_collector/ or src/infra/"

  github {
    owner = var.github_owner
    name  = var.github_repo_name
    push {
      branch = "^main$|^master$|^dev/.*$"
    }
  }

  included_files = [
    "scripts/news_collector/**",
    "src/infra/**",
    "cloudbuild-news-collector.yaml"
  ]

  filename = "cloudbuild-news-collector.yaml"

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = var.repository_name
  }
}

# 4. Trigger for Weather Tools (MCP)
resource "google_cloudbuild_trigger" "tools_weather_trigger" {
  name        = "ai-tuber-tools-weather"
  description = "Build and deploy Weather Tools on changes in src/tools/weather/ or src/infra/"

  github {
    owner = var.github_owner
    name  = var.github_repo_name
    push {
      branch = "^main$|^master$|^dev/.*$"
    }
  }

  included_files = [
    "src/tools/weather/**",
    "src/infra/**",
    "cloudbuild-tools-weather.yaml"
  ]

  filename = "cloudbuild-tools-weather.yaml"

  substitutions = {
    _REGION     = var.region
    _REPOSITORY = var.repository_name
  }
}

# 5. Trigger for Mind Data Sync
resource "google_cloudbuild_trigger" "mind_data_sync_trigger" {
  name        = "ai-tuber-mind-data-sync"
  description = "Sync mind data to GCS on changes in data/mind/"

  github {
    owner = var.github_owner
    name  = var.github_repo_name
    push {
      branch = "^main$|^master$|^dev/.*$"
    }
  }

  included_files = [
    "data/mind/**",
    "cloudbuild-mind.yaml"
  ]

  filename = "cloudbuild-mind.yaml"

  substitutions = {
    _BUCKET_NAME = var.bucket_name
    _REGION      = var.region
  }
}

# --- IAM Roles for Cloud Build Service Account ---

data "google_project" "project" {}

locals {
  cloudbuild_sa = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

# Allow Cloud Build to manage Cloud Run
resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = local.cloudbuild_sa
}

# Allow Cloud Build to act as the AI Tuber SA
resource "google_service_account_iam_member" "cloudbuild_sa_user" {
  service_account_id = google_service_account.ai_tuber_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = local.cloudbuild_sa
}

# Allow Cloud Build to push images to Artifact Registry
resource "google_project_iam_member" "cloudbuild_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = local.cloudbuild_sa
}

# Allow Cloud Build to sync data to GCS
resource "google_storage_bucket_iam_member" "cloudbuild_storage_admin" {
  bucket = google_storage_bucket.ai_tuber_data.name
  role   = "roles/storage.objectAdmin"
  member = local.cloudbuild_sa
}
