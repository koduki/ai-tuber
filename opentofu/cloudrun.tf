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
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository}/saint-graph:latest"

        env {
          name  = "STORAGE_TYPE"
          value = "gcs"
        }

        env {
          name  = "SECRET_PROVIDER_TYPE"
          value = "gcp"
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "GCS_BUCKET_NAME"
          value = var.bucket_name
        }

        env {
          name  = "CHARACTER_NAME"
          value = var.character_name
        }

        env {
          name  = "STREAMING_MODE"
          value = "true"
        }

        env {
          name  = "STREAM_TITLE"
          value = var.stream_title
        }

        env {
          name  = "STREAM_DESCRIPTION"
          value = var.stream_description
        }

        env {
          name  = "STREAM_PRIVACY"
          value = "private"
        }

        env {
          name  = "BODY_URL"
          value = "http://${google_compute_instance.body_node.name}.${var.zone}.c.${var.project_id}.internal:8000"
        }

        env {
          name  = "WEATHER_MCP_URL"
          value = "${google_cloud_run_v2_service.tools_weather.uri}/sse"
        }

        env {
          name  = "BROADCAST_START_DELAY"
          value = var.broadcast_start_delay
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
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository}/tools-weather:latest"

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
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository}/news-collector:latest"

        env {
          name = "GOOGLE_API_KEY"
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
          name  = "STORAGE_TYPE"
          value = "gcs"
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

# Cloud Run service for Health Check Proxy
resource "google_cloud_run_v2_service" "healthcheck_proxy" {
  name     = "ai-tuber-healthcheck-proxy"
  location = var.region

  labels = {
    managed-by = "opentofu"
    app        = "ai-tuber"
  }

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository}/healthcheck-proxy:latest"
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
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
  }
}



output "tools_weather_url" {
  value = google_cloud_run_v2_service.tools_weather.uri
}

output "healthcheck_proxy_url" {
  value = google_cloud_run_v2_service.healthcheck_proxy.uri
}

# Cloud Run service for Ops Dashboard
resource "google_cloud_run_v2_service" "dashboard" {
  name     = "ai-tuber-dashboard"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  labels = {
    managed-by = "opentofu"
    app        = "ai-tuber"
  }

  template {
    # OAuth2 Proxy container (Primary / Ingress)
    containers {
      name  = "oauth2-proxy"
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository}/oauth2-proxy:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "FORCED_REDEPLOY_AT"
        value = "2026-03-17T12:30:00Z"
      }

      env {
        name  = "OAUTH2_PROXY_PROVIDER"
        value = "google"
      }

      env {
        name = "OAUTH2_PROXY_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = "oauth-client-id"
            version = "latest"
          }
        }
      }

      env {
        name = "OAUTH2_PROXY_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = "oauth-client-secret"
            version = "latest"
          }
        }
      }

      env {
        name = "OAUTH2_PROXY_COOKIE_SECRET"
        value_source {
          secret_key_ref {
            secret  = "dashboard-session-secret"
            version = "latest"
          }
        }
      }

      env {
        name  = "OAUTH2_PROXY_UPSTREAMS"
        value = "http://localhost:8081"
      }

      env {
        name  = "OAUTH2_PROXY_HTTP_ADDRESS"
        value = "0.0.0.0:8080"
      }

      env {
        name  = "OAUTH2_PROXY_REDIRECT_URL"
        value = "https://ai-tuber-dashboard-891439853880.asia-northeast1.run.app/oauth2/callback"
      }

      env {
        name  = "OAUTH2_PROXY_PROXY_PREFIX"
        value = "/oauth2"
      }

      env {
        name  = "OAUTH2_PROXY_EMAIL_DOMAINS"
        value = "*"
      }

      env {
        name  = "OAUTH2_PROXY_PASS_USER_HEADERS"
        value = "true"
      }

      env {
        name  = "OAUTH2_PROXY_SET_XAUTHREQUEST"
        value = "true"
      }

      env {
        name  = "OAUTH2_PROXY_REVERSE_PROXY"
        value = "true"
      }

      env {
        name  = "OAUTH2_PROXY_WHITELIST_DOMAINS"
        value = ".891439853880.asia-northeast1.run.app"
      }

      env {
        name  = "OAUTH2_PROXY_LOG_LEVEL"
        value = "debug"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }
    }

    # Dashboard App container (Sidecar)
    containers {
      name  = "dashboard"
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repository}/dashboard:latest"

      env {
        name  = "PORT"
        value = "8081"
      }

      env {
        name  = "ALLOWED_EMAILS"
        value = "pascalm3@gmail.com"
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_REGION"
        value = var.region
      }

      env {
        name  = "GCP_ZONE"
        value = var.zone
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

output "dashboard_url" {
  value = google_cloud_run_v2_service.dashboard.uri
}

resource "google_cloud_run_v2_service_iam_member" "dashboard_public" {
  project  = google_cloud_run_v2_service.dashboard.project
  location = google_cloud_run_v2_service.dashboard.location
  name     = google_cloud_run_v2_service.dashboard.name
  role     = "roles/run.invoker"
  member   = "allUsers" # アプリ層で保護するためパブリックにする
}
