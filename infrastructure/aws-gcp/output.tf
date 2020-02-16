data "template_file" "ansible_aws_host" {
  template = "${file("${path.module}/host.tpl")}"
  vars = {
    public_ip  = "${aws_instance.host.public_ip}"
    private_ip = "${aws_instance.host.private_ip}"
    private_subnet = "${aws_subnet.default.cidr_block}"
  }
}

data "template_file" "ansible_gcp_host" {
  template = "${file("${path.module}/host.tpl")}"
  vars = {
    public_ip  = "${google_compute_instance.host.network_interface.0.access_config.0.nat_ip}"
    private_ip = "${google_compute_instance.host.network_interface.0.network_ip}"
    private_subnet = "${google_compute_subnetwork.live_migration.ip_cidr_range}"
  }
}

data "template_file" "ansible_aws_vpn" {
  template = "${file("${path.module}/host.tpl")}"
  vars = {
    public_ip  = "${aws_instance.vpn.public_ip}"
    private_ip = "${aws_instance.vpn.private_ip}"
    private_subnet = "${aws_subnet.default.cidr_block}"
  }
}

data "template_file" "ansible_gcp_vpn" {
  template = "${file("${path.module}/host.tpl")}"
  vars = {
    public_ip  = "${google_compute_instance.vpn.network_interface.0.access_config.0.nat_ip}"
    private_ip = "${google_compute_instance.vpn.network_interface.0.network_ip}"
    private_subnet = "${google_compute_subnetwork.live_migration.ip_cidr_range}"
  }
}

data "template_file" "ansible_inventory" {
  template = "${file("${path.module}/inventory.tpl")}"
  vars = {
    hosts = "${join("",list(data.template_file.ansible_aws_host.rendered, data.template_file.ansible_gcp_host.rendered))}"
    vpns = "${join("",list(data.template_file.ansible_aws_vpn.rendered, data.template_file.ansible_gcp_vpn.rendered))}"
    private_key_file = "${var.private_key_path}"
    ssh_user = "ubuntu"
  }
}

output "ansible_inventory" {
	value = "${data.template_file.ansible_inventory.rendered}"
}
