# Cloud-Based IT Asset & System Monitoring Platform

Cloud-Based IT Asset & System Monitoring Platform centrally monitors multiple servers by using a lightweight Python monitoring agent that collects CPU, memory and disk utilization and sends the data to Flask REST APIs. The backend stores the metrics in MySQL, processes threshold-based alerts, and provides a dashboard to view asset health and historical metrics.

For the cloud deployment, I deployed the Flask application on AWS EC2 within a custom VPC, configured subnets, route tables, an Internet Gateway and Security Groups for network access. I use Amazon RDS for the MySQL database, Amazon S3 for storing reports/logs, and CloudWatch for monitoring the AWS infrastructure. The application follows a client-server architecture where monitoring agents send system metrics to the backend, the backend stores and analyzes the data, and the dashboard provides centralized visibility of all monitored assets.

## MVP Architecture

Linux Monitoring Agent -> Flask REST API -> MySQL -> Web Dashboard

## Stack

Python, Flask, MySQL, psutil, REST API, HTML/CSS/JavaScript

## Setup

1. Run `database/schema.sql` in MySQL.
2. Copy `.env.example` to `.env` and set your MySQL password.
3. Install packages:
   `pip install -r requirements.txt`
4. Start Flask:
   `cd backend`
   `python app.py`
5. In another terminal start the agent:
   `python agent/monitoring_agent.py`
6. Open `http://127.0.0.1:5000`

## AWS Deployment

The application is deployed on Amazon Web Services using a custom VPC.

### AWS Architecture

- **Amazon VPC** – Provides isolated network infrastructure
- **EC2** – Hosts the Flask application
- **Amazon RDS (MySQL)** – Provides managed database storage
- **Security Groups** – Controls inbound and outbound network access
- **EBS** – Provides persistent storage for the EC2 instance
- **EBS Snapshot** – Used as a backup/recovery point for the EC2 root volume

### Deployment Flow

Monitoring Agent
       ↓
Flask REST API
       ↓
Amazon EC2
       ↓
Amazon RDS (MySQL)
       ↓
Web Dashboard

### Network Architecture

Internet
   │
   ▼
AWS VPC
   │
   ├── Public Subnet
   │      └── EC2
   │           └── Flask Application
   │
   └── Database Layer
          └── RDS MySQL

### Application Dashboard

![Monitoring Dashboard](Screenshots/IT%20Monitoring%20.png)


###----------------------------------------------------------------------------------------------------------------------------------------------------------


![Asset Details](Screenshots/It%20Monitoring%20Asset%20Detail.png)

###----------------------------------------------------------------------------------------------------------------------------------------------------------


![Memory usage Graph](Screenshots/Memory%20usage.png) 

###----------------------------------------------------------------------------------------------------------------------------------------------------------


![CPU Usage Graph](Screenshots/CPU%20usage.png)

###----------------------------------------------------------------------------------------------------------------------------------------------------------


![Disk Usage Graph](Screenshots/disk%20usage.png)





### AWS EC2 Deployment

![EC2 Deployment](Screenshots/AWS%20EC2.png)

### Amazon RDS

![RDS Database](Screenshots/AWS%20RDS.png)

## Thresholds

CPU: warning 70%, critical 85%
Memory: warning 80%, critical 90%
Disk: warning 80%, critical 90%

AWS deployment (EC2, VPC, IAM, S3, CloudWatch) can be added after the local MVP works.
