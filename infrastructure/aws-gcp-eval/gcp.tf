provider "google" {
    project = "${var.gcp_project_id}"
    credentials = "${file(var.gcp_credentials_path)}"
    region = "asia-northeast1"
    zone = "asia-northeast1-a"
}

# resource "google_compute_project_metadata_item" "os_login2" {
#     project = "${var.gcp_project_id}"
#     key = "enable-oslogin"
#     value = "TRUE"
# }

resource "google_compute_project_metadata_item" "ssh_keys-eval" {
    project = "${var.gcp_project_id}"
    key = "ssh-keys-eval"
    value = "ubuntu:${file(var.public_key_path)}"
}

resource "google_compute_network" "live_migration-eval" {
    name = "live-migration-network-eval"
    auto_create_subnetworks = "false"
}

resource "google_compute_subnetwork" "live_migration-eval" {
    name = "internal-eval"
    ip_cidr_range = "10.0.1.0/24"
    network = "${google_compute_network.live_migration-eval.self_link}"
}

resource "google_compute_route" "live_migration-eval" {
    name = "live-migration-route-table-eval"
    dest_range = "${aws_vpc.default.cidr_block}"
    network = "${google_compute_network.live_migration-eval.name}"
    next_hop_ip = "${google_compute_instance.vpn-eval.network_interface.0.network_ip}"
    priority = 100
}

# Not needed for the host machine 
# (${google_compute_instance.host.network_interface.0.access_config.0.nat_ip} is enough) 
resource "google_compute_address" "vpn-eval" {
    name = "vpn-pip-2"
}

resource "google_compute_instance" "host-eval" {
  name         = "host2-eval"
  machine_type = "n1-standard-1"
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1804-bionic-v20190404"
    }
  }

  network_interface {
    subnetwork    = "${google_compute_subnetwork.live_migration-eval.self_link}"
    access_config {
    }
  }

  provisioner "remote-exec" {
    # connection {
    #   host = "${google_compute_instance.host.network_interface.0.access_config.0.nat_ip}"
    #   user = "ubuntu"
    # }
    connection {
      host = "${self.network_interface.0.access_config.0.nat_ip}"
      type        = "ssh"
      user        = "ubuntu"
      timeout     = "500s"
      private_key = "${file(var.private_key_path)}"
    }

    inline = [
      # "export DEBIAN_FRONTEND=noninteractive",
      # "sudo apt-get -y update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get -y update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get -y update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get -y install python",
    ]
  }
}

resource "google_compute_instance" "vpn-eval" {
  name         = "vpn2-eval"
  machine_type = "n1-standard-1"
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1804-bionic-v20190404"
    }
  }

  network_interface {
    subnetwork    = "${google_compute_subnetwork.live_migration-eval.self_link}"
    access_config {
        nat_ip = "${google_compute_address.vpn-eval.address}"
    }
  }

  provisioner "remote-exec" {
    # connection {
    #   host = "${google_compute_instance.vpn.network_interface.0.access_config.0.nat_ip}"
    #   user = "ubuntu"
    # }
    connection {
      host = "${self.network_interface.0.access_config.0.nat_ip}"
      type        = "ssh"
      user        = "ubuntu"
      timeout     = "500s"
      private_key = "${file(var.private_key_path)}"
    }

    inline = [
      # "export DEBIAN_FRONTEND=noninteractive",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get -y update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get -y update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get -y install python",
    ]
  }
}
