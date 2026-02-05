# Secret Manager for API keys
resource "google_secret_manager_secret" "google_api_key" {
  secret_id = "google-api-key"

  replication {
    auto {}
  }
}

# Grant access to service account
resource "google_secret_manager_secret_iam_member" "google_api_key_accessor" {
  secret_id = google_secret_manager_secret.google_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}

# Note: The actual secret value must be set manually:
# gcloud secrets versions add google-api-key --data-file=- <<< "YOUR_API_KEY"
