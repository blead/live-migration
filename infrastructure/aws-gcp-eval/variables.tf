variable "key_name" {
  description = "Desired name of key pair."
}

variable "public_key_path" {
  description = "Path to the SSH public key to be used for authentication."
}

variable "private_key_path" {
  description = "Path to the SSH private key to be used for authentication."
}

variable "gcp_project_id" {
  description = "The ID of the current project on GCP"
}

variable "gcp_credentials_path" {
  description = "Path to the GCP Service Account credential file to be used for authentication."
}