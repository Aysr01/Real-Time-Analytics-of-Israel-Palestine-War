from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, count, window, udf, sum
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, TimestampType, FloatType
import logging
import random
from cassandra.cluster import Cluster

logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(filename)s - %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Starting the Spark Application")


# Create a PostgreSQL table if not exists
table_name = "reddit_ipc_comments"

# Connect to the Cassandra cluster
cluster = Cluster(['cassandra'])  # Replace with your Cassandra node IP addresses
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
        label TEXT,
        comments_count INT,
        total_ups INT
    )
""")
logger.info("Table created successfully")

# Close the cluster connection
cluster.shutdown()
# try:
#     conn_details = psycopg2.connect(
#     host="postgres",
#     database="ispac",
#     user="postgres",
#     password="postgres",
#     port= '5432'
#     )
# except Exception as e:
#     logging.error(f"Error while connecting to PostgreSQL: {e}")
# else:
#     logging.info("Connection to PostgreSQL established successfully")
#     cursor = conn_details.cursor()
#     cursor.execute(f"""
#                    CREATE TABLE IF NOT EXISTS {table_name}
#                     (
#                         date TIMESTAMP,
#                         label varchar(30),
#                         comments_count INT,
#                         total_ups INT,
#                         PRIMARY KEY (date, label)
#                     )"""
#     )
#     conn_details.commit()
#     cursor.close()
#     conn_details.close()
#     logging.info("Table created successfully")


# Create a Spark Session
try:
    spark = SparkSession.builder \
                .appName("Comments_Count") \
                .config("spark.sql.shuffle.partitions", 4) \
                .config("spark.cassandra.connection.host", "cassandra") \
                .config('spark.cassandra.connection.port', '9042') \
                .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")
    logging.info("Spark Session created successfully")
except Exception as e:
    logging.error(f"Error while creating Spark Session: {e}")


# Create a UDF
@udf("string")
def label_comment(comment_text):
    labels = ["with israel", "with palestine", "neutral"]
    label = random.choice(labels)
    return label


comments_schema = StructType(
    [
        StructField("timestamp", FloatType(), False),
        StructField("id", StringType(), False),
        StructField("body", StringType(), True),
        StructField("author", StringType(), True),
        StructField("subreddit_id", StringType(), False),
        StructField("subreddit", StringType(), False),
        StructField("ups", IntegerType(), True),
        StructField("parent_id", StringType(), True),
        StructField("submission", StringType(), True)
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
                    .withColumn("label", label_comment(col("body"))) \
                    .withColumns({
                        "event_time": col("timestamp").cast(TimestampType())
                        }) \
                    .withWatermark("event_time", "3 minutes") \
                    .groupBy(window("event_time", "1 minute"), "label") \
                    .agg(count("id").alias("comments_count"), sum("ups").alias("total_ups")) \
                    .select(col("window").start.alias("date"), "label", "comments_count", "total_ups")


def writeToPsql(batch, batch_id):
    batch.write\
         .format("cassandra") \
         .options(table=table_name, keyspace="reddit_keyspace") \
         .mode("append") \
         .save()

write_stream = comments_counts.writeStream \
            .format("console") \
            .foreachBatch(writeToPsql) \
            .outputMode("append") \
            .option("checkpointLocation", "/tmp/checkpoint/") \
            .start(truncate=False)

write_stream.awaitTermination()