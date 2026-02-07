# GCS Bucket for news scripts and shared data
resource "google_storage_bucket" "ai_tuber_data" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Grant permissions to service account
resource "google_storage_bucket_iam_member" "ai_tuber_data_reader" {
  bucket = google_storage_bucket.ai_tuber_data.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.ai_tuber_sa.email}"
}
