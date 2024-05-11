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
    source = "../spark/apps/comments_count.py"
    bucket = google_storage_bucket.spark_bucket.name
}

# Create a BigQuery Dataset
resource "google_bigquery_dataset" "IPC_dataset" {
    dataset_id = "ipc_dataset" # Israelo Palestinian Conflict
    project    = var.project_id
}

# Create a BigQuery Table
resource "google_bigquery_table" "comments_count" {
    dataset_id = google_bigquery_dataset.IPC_dataset.dataset_id
    table_id   = "comments_count"
    project    = var.project_id
    schema = <<EOF
[
    {
        "name": "date",
        "type": "Timestamp",
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
