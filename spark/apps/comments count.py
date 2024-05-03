from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, count, window, current_timestamp
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, TimestampType, FloatType
import logging

logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(filename)s - %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Starting the Spark Application")
try:
    spark1 = SparkSession.builder \
                .appName("Comments_Count01") \
                .config("spark.sql.shuffle.partitions", 4) \
                .getOrCreate()

    spark1.sparkContext.setLogLevel("ERROR")
    logging.info("Spark Session created successfully")
except Exception as e:
    logging.error(f"Error while creating Spark Session: {e}")

comments_schema = StructType(
    [
        StructField("timestamp", FloatType(), False),
        StructField("id", StringType(), False),
        StructField("submission_id", StringType(), False),
        StructField("body", StringType(), True),
        StructField("author", StringType(), True),
        StructField("ups", IntegerType(), True)
    ]
)

# Read the data from Kafka
df = spark1.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "reddit_comments") \
        .option("startingOffsets", "earliest") \
        .load()
logging.info("Connection to Kafka established successfully")

comments_counts = df.withColumn("value", from_json(col("value").astype("string"), comments_schema)) \
                    .select("value.*") \
                    .withColumns({
                        "event_time": col("timestamp").cast(TimestampType())
                        }) \
                    .withWatermark("event_time", "3 minutes") \
                    .groupBy(window("event_time", "1 minute")) \
                    .agg(count("id").alias("num_comments"))


write_stream = comments_counts.writeStream \
            .format("console") \
            .outputMode("append") \
            .option("checkpointLocation", "/tmp/checkpoint1/") \
            .start(truncate=False)

write_stream.awaitTermination()