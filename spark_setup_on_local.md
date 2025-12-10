# Apache Spark 3.5.1 Setup on WSL2 Ubuntu (Kafka Structured Streaming)

This document describes the complete Spark-side setup used in this project.
It covers Java installation, Spark installation, environment variables, and
Kafka integration for Spark Structured Streaming.

Python virtual environments and requirements.txt apply only to ingestion services.
Spark itself is JVM-based and is not managed via pip.

------------------------------------------------------

SYSTEM ENVIRONMENT

Host OS: Windows  
Runtime OS: WSL2 Ubuntu  
Java Version: OpenJDK 11  
Spark Version: Apache Spark 3.5.1 (Hadoop 3 build)  
Spark Install Path: /opt/spark  
Execution Mode: local[*]

------------------------------------------------------

STEP 1: UPDATE SYSTEM PACKAGES

sudo apt update

------------------------------------------------------

STEP 2: INSTALL JAVA 11 (REQUIRED BY SPARK)

sudo apt install -y openjdk-11-jdk

Verify installation:

java -version

The output should show Java version 11.

------------------------------------------------------

STEP 3: CONFIGURE JAVA_HOME

Find the installed Java path:

readlink -f $(which java)

Expected result:

/usr/lib/jvm/java-11-openjdk-amd64/bin/java

Set JAVA_HOME permanently:

echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc

Reload shell configuration:

source ~/.bashrc

Verify:

echo $JAVA_HOME
java -version

------------------------------------------------------

STEP 4: DOWNLOAD APACHE SPARK 3.5.1

Go to a temporary directory:

cd /tmp

Download Spark 3.5.1 (Hadoop 3 build):

wget https://archive.apache.org/dist/spark/spark-3.5.1/spark-3.5.1-bin-hadoop3.tgz

------------------------------------------------------

STEP 5: INSTALL SPARK UNDER /opt

Create /opt directory if it does not exist:

sudo mkdir -p /opt

Extract Spark archive:

sudo tar -xzf spark-3.5.1-bin-hadoop3.tgz -C /opt

Rename the directory:

cd /opt
sudo mv spark-3.5.1-bin-hadoop3 spark

Final Spark location:

/opt/spark

------------------------------------------------------

STEP 6: CONFIGURE SPARK ENVIRONMENT VARIABLES

Add SPARK_HOME and update PATH:

echo 'export SPARK_HOME=/opt/spark' >> ~/.bashrc
echo 'export PATH=$SPARK_HOME/bin:$PATH' >> ~/.bashrc

Reload shell:

source ~/.bashrc

------------------------------------------------------

STEP 7: VERIFY SPARK INSTALLATION

Run:

spark-submit --version

The output must confirm:
- Spark version 3.5.1
- Scala 2.12
- Java 11

------------------------------------------------------

STEP 8: CREATE PROJECT DIRECTORY FOR SPARK JOBS

From project root:

cd ~/realtime-analytics
mkdir -p spark/streaming

Spark streaming jobs will be placed here.

------------------------------------------------------

STEP 9: KAFKA INTEGRATION FOR SPARK STRUCTURED STREAMING

Spark does not include Kafka support by default.

Kafka support is added at runtime using the following package:

org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1

This package matches:
- Spark 3.5.1
- Scala 2.12

------------------------------------------------------

STEP 10: RUN A SPARK STRUCTURED STREAMING JOB WITH KAFKA

From the project root directory:

spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
  spark/streaming/kafka_raw_stream.py

On first execution, Spark will:
- Download Kafka connector JARs
- Cache them under ~/.ivy2
- Start Spark in local[*] mode
- Connect to Kafka at localhost:9092
- Begin streaming data

------------------------------------------------------

STEP 11: STOP THE SPARK STREAMING JOB

To stop Spark cleanly:

Press Ctrl + C in the terminal where spark-submit is running.

Spark will terminate the streaming query and shut down safely.

------------------------------------------------------

NOTES

- Spark dependencies are not managed via requirements.txt
- PySpark is bundled with Spark itself
- Kafka integration is attached dynamically at runtime
- No executor or cluster sizing is configured because local[*] mode is used
- This setup maps directly to EMR or Databricks with only deployment changes
