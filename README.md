# realtime-analytics
Project: Real-Time Clickstream Analytics Platform

Design and implement a real-time data pipeline that ingests high-volume user clickstream events, processes them using PySpark Structured Streaming, applies aggregations and data quality checks, and serves curated data in Snowflake for analytical use cases. The system handles late-arriving data, ensures fault tolerance, and is orchestrated with Airflow.


# Pipeline
Event Generator → Kafka → Spark Structured Streaming
                          ↓
                       Raw Storage (S3 / ADLS)
                          ↓
                    Curated Tables (Snowflake)
                          ↓
                       BI / Queries

# Event Schema
{
  "event_id": "uuid",
  "user_id": "string",
  "session_id": "string",
  "event_type": "click | view | purchase",
  "page_url": "string",
  "event_timestamp": "timestamp",
  "ingestion_timestamp": "timestamp",
  "device": "mobile | web",
  "country": "string"
}
