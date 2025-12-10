import os
from pyspark.sql import SparkSession

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"
)

TOPIC = os.getenv(
    "KAFKA_TOPIC", "raw_wikimedia_events"
)

CHECKPOINT_LOCATION = os.getenv(
    "SPARK_CHECKPOINT_DIR",
    "/tmp/spark-checkpoints/raw_wikimedia"
)

# ---------------------------------------------------
# Spark session
# ---------------------------------------------------
spark = (
    SparkSession.builder
    .appName("KafkaRawStreamTest")
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ---------------------------------------------------
# Kafka stream
# ---------------------------------------------------
df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .load()
)

# ---------------------------------------------------
# Output stream (console sink)
# ---------------------------------------------------
query = (
    df
    .selectExpr(
        "CAST(key AS STRING) AS key",
        "CAST(value AS STRING) AS value",
        "topic",
        "partition",
        "offset",
        "timestamp"
    )
    .writeStream
    .format("console")
    .option("truncate", "false")
    .option("checkpointLocation", CHECKPOINT_LOCATION)
    .outputMode("append")
    .start()
)

query.awaitTermination()
