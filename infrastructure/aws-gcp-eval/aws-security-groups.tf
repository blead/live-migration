resource "aws_security_group" "allow_ssh" {
  name        = "allow-ssh"
  description = "Allow SSH. Managed by Terraform."
  vpc_id      = "${aws_vpc.default.id}"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "allow_http" {
  name        = "allow-http"
  description = "Allow HTTP. Managed by Terraform."
  vpc_id      = "${aws_vpc.default.id}"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "allow_internal" {
  name        = "allow-internal"
  description = "Allow internal traffic within VPC. Managed by Terraform."
  vpc_id      = "${aws_vpc.default.id}"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["${aws_vpc.default.cidr_block}"]
  }
}

resource "aws_security_group" "allow_gcp" {
  name        = "allow-gcp"
  description = "Allow traffic from GCP. Managed by Terraform."
  vpc_id      = "${aws_vpc.default.id}"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["${google_compute_subnetwork.live_migration-eval.ip_cidr_range}"]
  }
}

resource "aws_security_group" "allow_gcp_vpn" {
  name        = "allow-gcp-vpn"
  description = "Allow traffic from GCP VPN gateway. Managed by Terraform."
  vpc_id      = "${aws_vpc.default.id}"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["${google_compute_address.vpn-eval.address}/32"]
  }
}

resource "aws_security_group" "allow_egress" {
  name        = "allow-egress"
  description = "Allow outgoing traffic. Managed by Terraform."
  vpc_id      = "${aws_vpc.default.id}"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
