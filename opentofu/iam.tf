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

# Allow reading from Artifact Registry (for GCE to pull Docker images)
resource "google_project_iam_member" "artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Allow Cloud Scheduler (via ai-tuber-sa) to start/stop the GCE instance
resource "google_project_iam_member" "compute_instance_admin" {
  project = var.project_id
  role    = "roles/compute.instanceAdmin.v1"
  member  = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Allow ai-tuber-sa to execute News Collector Job
resource "google_cloud_run_v2_job_iam_member" "invoke_news_collector" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.news_collector.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Allow ai-tuber-sa to execute Saint Graph Job
resource "google_cloud_run_v2_job_iam_member" "invoke_saint_graph" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.saint_graph.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Allow Workflow execution
resource "google_project_iam_member" "workflows_editor" {
  project = var.project_id
  role    = "roles/workflows.editor"
  member  = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Allow Service Account to act as itself (Service Account User) for Workflows
resource "google_service_account_iam_member" "sa_user_itself" {
  service_account_id = google_service_account.ai_tuber_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Allow ai-tuber-sa to read Cloud Run Jobs/Executions (needed for run.executions.get)
resource "google_project_iam_member" "run_viewer" {
  project = var.project_id
  role    = "roles/run.viewer"
  member  = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Note: Storage permissions are handled at the bucket level in storage.tf
# No project-wide storage.objectUser role is needed here, following least privilege.
