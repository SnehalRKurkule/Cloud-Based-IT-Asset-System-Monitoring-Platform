# Cloud-Based IT Asset & System Monitoring Platform

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

## Thresholds

CPU: warning 70%, critical 85%
Memory: warning 80%, critical 90%
Disk: warning 80%, critical 90%

AWS deployment (EC2, VPC, IAM, S3, CloudWatch) can be added after the local MVP works.
