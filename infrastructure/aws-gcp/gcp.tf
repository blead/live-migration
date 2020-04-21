provider "google" {
    project = "${var.gcp_project_id}"
    credentials = "${file(var.gcp_credentials_path)}"
    region = "asia-southeast1"
    zone = "asia-southeast1-a"
}

resource "google_compute_project_metadata_item" "os_login" {
    project = "${var.gcp_project_id}"
    key = "enable-oslogin"
    value = "TRUE"
}

resource "google_compute_project_metadata_item" "ssh_keys" {
    project = "${var.gcp_project_id}"
    key = "ssh-keys"
    value = "ubuntu:${file(var.public_key_path)}"
}

resource "google_compute_network" "live_migration" {
    name = "live-migration-network"
    auto_create_subnetworks = "false"
}

resource "google_compute_subnetwork" "live_migration" {
    name = "internal"
    ip_cidr_range = "10.0.1.0/24"
    network = "${google_compute_network.live_migration.self_link}"
}

resource "google_compute_route" "live_migration" {
    name = "live-migration-route-table"
    dest_range = "${aws_vpc.default.cidr_block}"
    network = "${google_compute_network.live_migration.name}"
    next_hop_ip = "${google_compute_instance.vpn.network_interface.0.network_ip}"
    priority = 100
}

# Not needed for the host machine 
# (${google_compute_instance.host.network_interface.0.access_config.0.nat_ip} is enough) 
resource "google_compute_address" "vpn" {
    name = "vpn-pip"
}

resource "google_compute_instance" "host" {
  name         = "host2"
  machine_type = "n1-standard-1"
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1804-bionic-v20190404"
    }
  }

  network_interface {
    subnetwork    = "${google_compute_subnetwork.live_migration.self_link}"
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
      "sudo apt-get -y update",
      "sudo apt-get -y update",
      "sudo apt-get -y install python",
    ]
  }
}

resource "google_compute_instance" "vpn" {
  name         = "vpn2"
  machine_type = "n1-standard-1"
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1804-bionic-v20190404"
    }
  }

  network_interface {
    subnetwork    = "${google_compute_subnetwork.live_migration.self_link}"
    access_config {
        nat_ip = "${google_compute_address.vpn.address}"
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
      "sudo apt-get -y update",
      "sudo apt-get -y update",
      "sudo apt-get -y install python",
    ]
  }
}
