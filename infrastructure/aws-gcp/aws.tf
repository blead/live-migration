provider "aws" {
  version    = "=2.7"
  region     = "ap-southeast-1"
}

resource "aws_key_pair" "auth" {
  key_name   = "${var.key_name}"
  public_key = "${file(var.public_key_path)}"
}

resource "aws_vpc" "default" {
  cidr_block = "172.31.0.0/16"
  enable_dns_hostnames = true
}

resource "aws_internet_gateway" "default" {
  vpc_id = "${aws_vpc.default.id}"
}

resource "aws_route" "internet_access" {
  route_table_id         = "${aws_vpc.default.main_route_table_id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = "${aws_internet_gateway.default.id}"
}

resource "aws_route" "to_gcp" {
  route_table_id         = "${aws_vpc.default.main_route_table_id}"
  destination_cidr_block = "${google_compute_subnetwork.live_migration.ip_cidr_range}"
  instance_id            = "${aws_instance.vpn.id}"
}

resource "aws_subnet" "default" {
  vpc_id                  = "${aws_vpc.default.id}"
  cidr_block              = "172.31.1.0/24"
  map_public_ip_on_launch = true
}

resource "aws_instance" "host" {
  ami                    = "ami-0dad20bd1b9c8c004"
  instance_type          = "t2.micro"
  key_name               = "${aws_key_pair.auth.id}"
  associate_public_ip_address = true
  subnet_id              = "${aws_subnet.default.id}"
  source_dest_check      = "false"
  vpc_security_group_ids = [
    "${aws_security_group.allow_ssh.id}",
    "${aws_security_group.allow_http.id}",
    "${aws_security_group.allow_internal.id}",
    "${aws_security_group.allow_gcp.id}",
    "${aws_security_group.allow_gcp_vpn.id}",
    "${aws_security_group.allow_egress.id}",
  ]

  tags = {
    Name = "host"
  }

  provisioner "remote-exec" {
    # connection {
    #   user = "ubuntu"
    #   host = "${aws_instance.host.public_ip}"
    # }
    connection {
      host = "${self.public_ip}"
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

resource "aws_instance" "vpn" {
  ami                    = "ami-0dad20bd1b9c8c004"
  instance_type          = "t2.micro"
  key_name               = "${aws_key_pair.auth.id}"
  associate_public_ip_address = true
  subnet_id              = "${aws_subnet.default.id}"
  source_dest_check      = "false"
  vpc_security_group_ids = [
    "${aws_security_group.allow_ssh.id}",
    "${aws_security_group.allow_internal.id}",
    "${aws_security_group.allow_gcp.id}",
    "${aws_security_group.allow_gcp_vpn.id}",
    "${aws_security_group.allow_egress.id}",
  ]

  tags = {
    Name = "vpn"
  }

  provisioner "remote-exec" {
    # connection {
    #   user = "ubuntu"
    #   host = "${aws_instance.vpn.public_ip}"
    # }
    connection {
      host = "${self.public_ip}"
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
