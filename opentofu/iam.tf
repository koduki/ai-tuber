# Service Account for AI Tuber resources
resource "google_service_account" "ai_tuber_sa" {
  account_id   = "ai-tuber-sa"
  display_name = "AI Tuber Service Account"
}

# Grant Secret Manager Access (Project-wide for simplicity with multiple secrets like YouTube/Google API)
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Allow writing metrics (Ops Agent)
resource "google_project_iam_member" "metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Allow writing logs
resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Note: Storage permissions are handled at the bucket level in storage.tf
# No project-wide storage.objectUser role is needed here, following least privilege.
