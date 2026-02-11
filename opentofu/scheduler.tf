# Cloud Workflows to orchestrate the streaming pipeline
resource "google_workflows_workflow" "streaming_pipeline" {
  name            = "ai-tuber-streaming-pipeline"
  region          = var.region
  description     = "Orchestrates news collection, GCE startup, streaming, and GCE shutdown"
  service_account = google_service_account.ai_tuber_sa.email
  source_contents = templatefile("${path.module}/workflow.yaml", {
    project_id         = var.project_id
    region             = var.region
    zone               = var.zone
    body_node_name     = google_compute_instance.body_node.name
    news_collector_job = google_cloud_run_v2_job.news_collector.name
    saint_graph_job    = google_cloud_run_v2_job.saint_graph.name
  })

  labels = {
    managed-by = "opentofu"
  }

  depends_on = [
    google_project_service.workflows,
    google_project_service.workflowexecutions
  ]
}

# Replace individual Scheduler jobs with a single Workflow trigger
resource "google_cloud_scheduler_job" "workflow_trigger" {
  name             = "ai-tuber-workflow-daily"
  description      = "Triggers the streaming pipeline workflow daily"
  schedule         = "00 07 * * *" # Start at 07:00 JST
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/workflows/${google_workflows_workflow.streaming_pipeline.name}/executions"

    oauth_token {
      service_account_email = google_service_account.ai_tuber_sa.email
    }
  }
}
