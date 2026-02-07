# Secret Manager for API keys
resource "google_secret_manager_secret" "google_api_key" {
  secret_id = "google-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "youtube_client_secret" {
  secret_id = "youtube-client-secret"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "youtube_token" {
  secret_id = "youtube-token"
  replication {
    auto {}
  }
}

# Grant access to service account (Project-wide accessor is handled in iam.tf, but let's be explicit if needed)
# Since we have roles/secretmanager.secretAccessor project-wide in iam.tf, 
# explicit secret-level permissions are optional but good for clarity.

# Note: The actual secret value must be set manually:
# gcloud secrets versions add google-api-key --data-file=- <<< "YOUR_API_KEY"
