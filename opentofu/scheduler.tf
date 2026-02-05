# Cloud Scheduler job to trigger news collection
resource "google_cloud_scheduler_job" "news_collection" {
  name             = "ai-tuber-news-collection"
  description      = "Daily news collection job"
  schedule         = "0 7 * * *"  # Every day at 07:00 JST (adjust timezone as needed)
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "600s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.news_collector.name}:run"

    oauth_token {
      service_account_email = google_service_account.ai_tuber_sa.email
    }
  }
}

# Cloud Scheduler job to start GCE instance
resource "google_cloud_scheduler_job" "start_body_node" {
  name             = "ai-tuber-start-body-node"
  description      = "Start Body Node for streaming"
  schedule         = "15 7 * * *"  # 07:15 JST
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "180s"

  http_target {
    http_method = "POST"
    uri         = "https://compute.googleapis.com/compute/v1/projects/${var.project_id}/zones/${var.zone}/instances/${google_compute_instance.body_node.name}/start"

    oauth_token {
      service_account_email = google_service_account.ai_tuber_sa.email
    }
  }
}

# Cloud Scheduler job to stop GCE instance
resource "google_cloud_scheduler_job" "stop_body_node" {
  name             = "ai-tuber-stop-body-node"
  description      = "Stop Body Node after streaming"
  schedule         = "35 8 * * *"  # 08:35 JST
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "180s"

  http_target {
    http_method = "POST"
    uri         = "https://compute.googleapis.com/compute/v1/projects/${var.project_id}/zones/${var.zone}/instances/${google_compute_instance.body_node.name}/stop"

    oauth_token {
      service_account_email = google_service_account.ai_tuber_sa.email
    }
  }
}
