resource "google_compute_firewall" "allow-inbound-eval" {
  name    = "tf-allow-inbound-eval"
  network = "${google_compute_network.live_migration-eval.self_link}"

  allow {
    protocol = "tcp"
    ports    = ["80", "22"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "allow-internal-eval" {
  name    = "tf-allow-internal-eval"
  network = "${google_compute_network.live_migration-eval.self_link}"

  allow {
    protocol = "all"
  }

  source_ranges = ["${google_compute_subnetwork.live_migration-eval.ip_cidr_range}"]
}

resource "google_compute_firewall" "allow-aws-eval" {
  name    = "tf-allow-aws-eval"
  network = "${google_compute_network.live_migration-eval.self_link}"

  allow {
    protocol = "all"
  }

  source_ranges = ["${aws_vpc.default.cidr_block}"]
}

resource "google_compute_firewall" "allow-aws-vpn-eval" {
  name    = "tf-allow-aws-vpn-eval"
  network = "${google_compute_network.live_migration-eval.self_link}"

  allow {
    protocol = "all"
  }

  source_ranges = ["${aws_instance.vpn.public_ip}/32"]
}

resource "google_compute_firewall" "allow-egress-eval" {
  name    = "tf-allow-egress-eval"
  direction = "EGRESS"
  network = "${google_compute_network.live_migration-eval.self_link}"

  allow {
    protocol = "all"
  }

}
