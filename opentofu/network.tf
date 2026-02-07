# VPC for Cloud Run and GCE
resource "google_compute_network" "ai_tuber_network" {
  name                    = "ai-tuber-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "ai_tuber_subnet" {
  name          = "ai-tuber-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.ai_tuber_network.id
}

# Firewall: Allow Cloud Run to communicate with Body Node (API only)
resource "google_compute_firewall" "allow_cloud_run_to_body" {
  name    = "ai-tuber-allow-cloud-run-to-body"
  network = google_compute_network.ai_tuber_network.name

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = [google_compute_subnetwork.ai_tuber_subnet.ip_cidr_range]
  target_tags   = ["ai-tuber-body"]
}

# Firewall: Allow noVNC access for health check and monitoring
resource "google_compute_firewall" "allow_vnc" {
  name    = "ai-tuber-allow-vnc"
  network = google_compute_network.ai_tuber_network.name

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = var.admin_ip_ranges
  target_tags   = ["ai-tuber-body"]
}

# Firewall: Allow SSH only via IAP (Identity-Aware Proxy)
# See: https://cloud.google.com/iap/docs/using-tcp-forwarding
resource "google_compute_firewall" "allow_ssh_iap" {
  name    = "ai-tuber-allow-ssh-iap"
  network = google_compute_network.ai_tuber_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # This is the official Google IAP range
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["ai-tuber-body"]
}
