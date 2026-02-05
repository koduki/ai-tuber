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

# Serverless VPC Access Connector for Cloud Run
resource "google_vpc_access_connector" "cloud_run_connector" {
  name          = "ai-tuber-connector"
  region        = var.region
  network       = google_compute_network.ai_tuber_network.name
  ip_cidr_range = "10.8.0.0/28"
}

# Firewall rule to allow internal communication
resource "google_compute_firewall" "allow_internal" {
  name    = "ai-tuber-allow-internal"
  network = google_compute_network.ai_tuber_network.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/24", "10.8.0.0/28"]
}

# Firewall rule for SSH (optional for debugging)
resource "google_compute_firewall" "allow_ssh" {
  name    = "ai-tuber-allow-ssh"
  network = google_compute_network.ai_tuber_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ai-tuber-body"]
}
