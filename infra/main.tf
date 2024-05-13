# Create a Bucket
resource "google_storage_bucket" "spark_bucket" {
    name          = "${var.project_id}-${var.bucket_name}"
    location      = var.region
    project       = var.project_id
    force_destroy = true
}

# Add Spark Application to the Bucket
resource "google_storage_bucket_object" "spark_app" {
    name   = "spark_app.py"
    source = "./comments_count.py"
    bucket = google_storage_bucket.spark_bucket.name
}

# Add Pubsub jar file to the Bucket
resource "google_storage_bucket_object" "pubsublite_jar" {
    name   = "pubsublite.jar"
    source = "./pubsublite-spark-sql-streaming-1.0.0-with-dependencies.jar"
    bucket = google_storage_bucket.spark_bucket.name
}

# Create a BigQuery Dataset
resource "google_bigquery_dataset" "IPC_dataset" {
    dataset_id = var.dataset_id
    project    = var.project_id
}

# Create a BigQuery Table
resource "google_bigquery_table" "comments_count" {
    dataset_id = google_bigquery_dataset.IPC_dataset.dataset_id
    table_id   = var.table_id
    project    = var.project_id
    schema     = <<EOF
[
    {
        "name": "date",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "comment_count",
        "type": "INTEGER",
        "mode": "REQUIRED"
    }
]
EOF
}

# Create a pubsub reservation
resource "google_pubsub_lite_reservation" "ipc_reservation" {
  name                = "ipc-reservation"
  project             = var.project_id
  throughput_capacity = 2
}

# Create a Pub/Sub reservation, topic, subscription
resource "google_pubsub_lite_topic" "ipc_topic" {
  name    = "ipc-topic"
  project = var.project_id

  partition_config {
    count = 1
  }

  retention_config {
    per_partition_bytes = 32212254720
  }

  reservation_config {
    throughput_reservation = google_pubsub_lite_reservation.ipc_reservation.name
  }
}

resource "google_pubsub_lite_subscription" "ipc_subscription" {
  name  = "ipc-subscription"
  topic = google_pubsub_lite_topic.ipc_topic.name
  delivery_config {
    delivery_requirement = "DELIVER_AFTER_STORED"
  }
}

# Create a DataProc Cluster
# resource "google_dataproc_cluster" "my_cluster" {
#   name   = "cluster-740a"
#   region = var.region
#   project = var.project_id
#   cluster_config {
#     gce_cluster_config{
#       internal_ip_only = false
#       network = "default"
#     }
#     master_config {
#       num_instances = 1
#       machine_type  = "n2-standard-4"
#       disk_config {
#         boot_disk_type = "pd-balanced"
#         boot_disk_size_gb = 30
#       }
#     }

#     worker_config {
#       num_instances    = 2
#       machine_type     = "n2-standard-2"
#       disk_config {
#         boot_disk_type = "pd-balanced"
#         boot_disk_size_gb = 30
#       }
#     }

#     software_config {
#       image_version = "2.2-debian12"
#       optional_components = ["JUPYTER"]
#     }
#   }
# }

# Create a DataProc Job
resource "google_dataproc_job" "pyspark" {
  region = var.region
  force_delete = true
  placement {
    cluster_name = "cluster-ba3d" # google_dataproc_cluster.my_cluster.name
  }
  reference {
    job_id = format("my-job-%s", uuid())
  }
  pyspark_config {
    main_python_file_uri = "gs://${google_storage_bucket.spark_bucket.name}/${google_storage_bucket_object.spark_app.name}"
    jar_file_uris = [
      "gs://${google_storage_bucket.spark_bucket.name}/${google_storage_bucket_object.pubsublite_jar.name}"
    ]
    properties = {
      "spark.logConf" = "true"
    }
  }
}

# Check out current state of the jobs
# output "spark_status" {
#   value = google_dataproc_job.spark.status[0].state
# }

# output "pyspark_status" {
#   value = google_dataproc_job.pyspark.status[0].state
# }
