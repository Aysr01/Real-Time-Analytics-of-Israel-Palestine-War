# Define variables for the project

variable "credentials_file" {
  description = "Path to the GCP credentials file"
  type        = string
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "zone" {
  description = "The GCP zone"
  type        = string
}

variable "bucket_name" {
  description = "The GCP bucket name"
  type        = string
}

variable "dataset_id" {
  description = "The BigQuery dataset ID"
  type        = string
}

variable "table_id" {
  description = "The BigQuery table ID"
  type        = string
}