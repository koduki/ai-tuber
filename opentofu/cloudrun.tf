# Cloud Run Job for Saint Graph (Streaming)
resource "google_cloud_run_v2_job" "saint_graph" {
  name     = "ai-tuber-saint-graph"
  location = var.region

  labels = {
    managed-by = "opentofu"
    app        = "ai-tuber"
  }

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name}/saint-graph:latest"

        env {
          name  = "GOOGLE_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.google_api_key.secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "YOUTUBE_CLIENT_SECRET_JSON"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.youtube_client_secret.secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "YOUTUBE_TOKEN_JSON"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.youtube_token.secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "GCS_BUCKET_NAME"
          value = var.bucket_name
        }

        env {
          name  = "STREAMING_MODE"
          value = "true"
        }

        env {
          name  = "STREAM_TITLE"
          value = "紅月れんのAIニュース配信テスト"
        }

        env {
          name  = "STREAM_DESCRIPTION"
          value = "Google ADKとGeminiを使った次世代AITuber、紅月れんのニュース配信テストです。"
        }

        env {
          name  = "STREAM_PRIVACY"
          value = "private"
        }

        env {
          name  = "BODY_URL"
          value = "http://${google_compute_instance.body_node.network_interface[0].network_ip}:8000"
        }

        env {
          name  = "WEATHER_MCP_URL"
          value = "${google_cloud_run_v2_service.tools_weather.uri}/sse"
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }

      vpc_access {
        network_interfaces {
          network    = google_compute_network.ai_tuber_network.name
          subnetwork = google_compute_subnetwork.ai_tuber_subnet.name
        }
        egress = "ALL_TRAFFIC"
      }

      service_account = google_service_account.ai_tuber_sa.email
      timeout         = "3600s" # 1 hour max for streaming
    }
  }
}

# Cloud Run service for Tools Weather (MCP)
resource "google_cloud_run_v2_service" "tools_weather" {
  name     = "ai-tuber-tools-weather"
  location = var.region

  labels = {
    managed-by = "opentofu"
    app        = "ai-tuber"
  }

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name}/tools-weather:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    service_account = google_service_account.ai_tuber_sa.email
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Cloud Run Job for News Collector
resource "google_cloud_run_v2_job" "news_collector" {
  name     = "ai-tuber-news-collector"
  location = var.region

  labels = {
    managed-by = "opentofu"
    app        = "ai-tuber"
  }

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name}/news-collector:latest"

        env {
          name  = "GOOGLE_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.google_api_key.secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "GCS_BUCKET_NAME"
          value = var.bucket_name
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }

      service_account = google_service_account.ai_tuber_sa.email
    }
  }
}

# Allow unauthenticated access (adjust based on requirements)
resource "google_cloud_run_service_iam_member" "tools_weather_noauth" {
  location = google_cloud_run_v2_service.tools_weather.location
  service  = google_cloud_run_v2_service.tools_weather.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

data "google_project" "project" {
  project_id = var.project_id
}

output "tools_weather_url" {
  value = google_cloud_run_v2_service.tools_weather.uri
}
