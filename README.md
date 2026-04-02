# Real-Time Cryptocurrency Trade Ingestion Pipeline

This is a scalable data streaming pipeline that 
ingests over 1.3 million cryptocurrency trades a day from 
Coinbase Websocket API, which are made available in a Databricks
catalog.

## Tools/Services Used

![Architecture Diagram](images/arch_diagram.png)

### Data Ingestion

#### Websocket API Consumer Script

A Python script (`ecs/websocket_script_coinbase_v2.py`)
subscribes to the Coinbase Websocket API. 
The script is put into a Docker image and deployed as an ECS task. 
The ECS cluster uses the EC2 launch type, primarily for cost savings.

Received messages are sent to a Kinesis stream, then transformed 
using Firehose and saved to an existing S3 bucket.

#### Data Extraction to Databricks

An external location in Databricks was connected, in order to access raw data
from S3. Databricks automates the process of creating the necessary 
infrastructure such as IAM roles in the AWS account to enable access.

#### Raw Data Transformations

A dbt project was created under `coinbase_data_flow` that handles data 
transformations from the raw S3 data.

Data Models (Medallion Architecture)
* Bronze
  * raw_coinbase_data - returns raw trade data from the past 90 days
* Silver
  * trades_timeseries - deduped list of trades from the past 90 days
  * recent_coinbase_data_1d - simplified trade data from past 24 hours (used for troubleshooting)
  * recent_coinbase_data_1d_by_symbol - trade counts per symbol over the past 24 hours (used for troubleshooting)
  * recent_coinbase_data_1h_by_symbol - trade counts per symbol over the past hour (used for troubleshooting)
* Gold
  * btc_timeseries_minute - aggregate trade data by the minute for Bitcoin over the past 7 days
  * eth_timeseries_minute - aggregate trade data by the minute for Ethereum over the past 7 days

![dbt DAG](images/dbt-dag.png)


### VPC Infrastructure

The ECS cluster is deployed to a VPC private subnet. As the ECS task needs
to send requests to an external API, a NAT gateway is needed in a public subnet.  

In addition, a Kinesis Endpoint were created to direct traffic to AWS Kinesis 
along the AWS backbone, a small optimization.








