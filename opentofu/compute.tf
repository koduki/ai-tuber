# Compute Engine instance for Body (OBS + VoiceVox + Streamer)
resource "google_compute_instance" "body_node" {
  name         = "ai-tuber-body-node"
  machine_type = "g2-standard-4"
  zone         = var.compute_zone

  tags = ["ai-tuber-body"]

  boot_disk {
    initialize_params {
      # Deep Learning VM: NVIDIA drivers (570) + CUDA 12.8 + Docker (NVIDIA runtime) pre-installed
      image = "deeplearning-platform-release/common-cu128-ubuntu-2204-nvidia-570"
      size  = 50
      type  = "pd-balanced"
    }
  }

  # GPU attachment
  guest_accelerator {
    type  = "nvidia-l4"
    count = 1
  }

  scheduling {
    preemptible       = var.enable_spot_instance
    automatic_restart = false
    # GPU instances (L4) cannot be live-migrated — always TERMINATE
    on_host_maintenance = "TERMINATE"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.ai_tuber_subnet.id

    # Assign external IP for internet access (can be removed if using NAT)
    access_config {
    }
  }

  metadata = {
    enable-oslogin     = "TRUE"
    gcs_bucket         = var.bucket_name
    character_name     = var.character_name
    stream_title       = var.stream_title
    stream_description = var.stream_description
    primary_region     = var.region
  }

  metadata_startup_script = file("${path.module}/../scripts/gce/startup.sh")

  service_account {
    email  = google_service_account.ai_tuber_sa.email
    scopes = ["cloud-platform"]
  }

  # Allow instance to be stopped/started by Cloud Scheduler
  allow_stopping_for_update = true
}

output "body_node_internal_ip" {
  value = google_compute_instance.body_node.network_interface[0].network_ip
}

output "body_node_external_ip" {
  value = google_compute_instance.body_node.network_interface[0].access_config[0].nat_ip
}
