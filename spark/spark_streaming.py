from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("KafkaSparkStreaming")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "click_events")
    .option("startingOffsets", "earliest")
    .load()
)

# Convert Kafka value (binary) to string
value_df = df.selectExpr("CAST(value AS STRING)")

query = (
    value_df.writeStream
    .format("console")
    .option("truncate", "false")
    .start()
)

query.awaitTermination()

