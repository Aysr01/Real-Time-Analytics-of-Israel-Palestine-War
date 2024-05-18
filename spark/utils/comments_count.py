from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, count, window, udf, sum
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, TimestampType, FloatType
import logging
import random
import requests
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(filename)s - %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Starting the Spark Application")


# Define the table name
cassandra_host = "cassandra"
table_name = "reddit_ipc_comments"

# Connect to the Cassandra cluster
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
cluster = Cluster([cassandra_host], auth_provider= auth_provider)  # Replace with your Cassandra node IP addresses
session = cluster.connect()

# Create a keyspace
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS reddit_keyspace
    WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': '1'}
""")

# Use the created keyspace
logger.info("Using the reddit_keyspace keyspace")
session.set_keyspace('reddit_keyspace')

# Create a table
session.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        date TIMESTAMP PRIMARY KEY,
        subreddit TEXT,
        label TEXT,
        comments_count INT,
        total_ups INT
    )
""")
logger.info("Table created successfully")

# Close the cluster connection
cluster.shutdown()


# Create a Spark Session
spark = SparkSession.builder \
            .appName("Comments_Count") \
            .config("spark.sql.shuffle.partitions", 4) \
            .config("spark.cassandra.connection.host", "cassandra") \
            .config('spark.cassandra.connection.port', '9042') \
            .config('spark.cassandra.auth.username', 'cassandra') \
            .config('spark.cassandra.auth.password', 'cassandra') \
            .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
logging.info("Spark Session created successfully")


# Create a UDF
@udf("string")
def label_comment(submission_title, submission_post, parent, comment_text):
    url = "http://model-endpoint:5000/predict"
    submission_title = submission_title if submission_title is not None else ""
    parent = "" if parent is None else parent
    submission_post = "" if submission_post is None else submission_post
    data = {
        "title": submission_title,
        "post": submission_post + ". " + parent,
        "comment": comment_text
    }
    response = requests.post(url, json=data)
    return response.text


comments_schema = StructType(
    [
        StructField("timestamp", FloatType(), False),
        StructField("id", StringType(), False),
        StructField("body", StringType(), True),
        StructField("author", StringType(), True),
        StructField("subreddit_id", StringType(), False),
        StructField("subreddit", StringType(), False),
        StructField("ups", IntegerType(), True),
        StructField("parent_content", StringType(), True),
        StructField("submission_text", StringType(), True),
        StructField("submission_title", StringType(), True)
    ]
)

# Read the data from Kafka
df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "reddit_comments") \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()
logging.info("Connection to Kafka established successfully")

comments_counts = df.withColumn("value", from_json(col("value").astype("string"), comments_schema)) \
                    .select("value.*") \
                    .withColumn(
                        "label", 
                        label_comment(col("submission_title"), col("submission_text"), col("parent_content"), col("body"))
                    ) \
                    .withColumns({
                        "event_time": col("timestamp").cast(TimestampType())
                        }) \
                    .withWatermark("event_time", "15 minute") \
                    .groupBy(window("event_time", "1 hour"), "subreddit", "label") \
                    .agg(count("id").alias("comments_count"), sum("ups").alias("total_ups")) \
                    .select(col("window").start.alias("date"), "subreddit", "label", "comments_count", "total_ups")


def writeToCassandra(batch, batch_id):
    batch.write\
         .format("org.apache.spark.sql.cassandra") \
         .options(table=table_name, keyspace="reddit_keyspace") \
         .mode("append") \
         .save()

write_stream = comments_counts.writeStream \
            .format("console") \
            .foreachBatch(writeToCassandra) \
            .outputMode("update") \
            .trigger(processingTime="5 seconds") \
            .option("checkpointLocation", "/tmp/checkpoint/") \
            .start(truncate=False)

write_stream.awaitTermination()