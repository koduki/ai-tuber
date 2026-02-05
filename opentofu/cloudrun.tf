# Cloud Run service for Saint Graph
resource "google_cloud_run_v2_service" "saint_graph" {
  name     = "ai-tuber-saint-graph"
  location = var.region

  labels = {
    managed-by = "opentofu"
    app        = "ai-tuber"
  }

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
        name  = "GCS_BUCKET_NAME"
        value = var.bucket_name
      }

      env {
        name  = "BODY_URL"
        value = "http://${google_compute_instance.body_node.network_interface[0].network_ip}:8000"
      }

      env {
        name  = "WEATHER_MCP_URL"
        value = "https://ai-tuber-tools-weather-${data.google_project.project.number}-${var.region}.a.run.app/sse"
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
      egress = "PRIVATE_RANGES_ONLY"
    }

    service_account = google_service_account.ai_tuber_sa.email
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
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

      env {
        name  = "PORT"
        value = "8001"
      }

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

output "saint_graph_url" {
  value = google_cloud_run_v2_service.saint_graph.uri
}

output "tools_weather_url" {
  value = google_cloud_run_v2_service.tools_weather.uri
}
