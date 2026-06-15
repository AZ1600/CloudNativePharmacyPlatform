# Cloud-Native Serverless Pharmacy Platform

## Overview

A multi-tenant serverless pharmacy management platform built on AWS using event-driven architecture and Infrastructure as Code principles.

The platform enables pharmacies and healthcare organizations to securely manage pharmaceutical inventory, monitor stock levels, process low-stock alerts, and support tenant-isolated operations using a shared SaaS architecture.

Built using AWS Lambda, API Gateway, DynamoDB, Amazon Cognito, SQS, EventBridge, and AWS SAM, the solution demonstrates cloud-native application design, serverless computing, event-driven processing, and scalable AWS architecture patterns.

---

## Architecture

Client Application

↓

Amazon API Gateway

↓

AWS Lambda

↓

Amazon DynamoDB

↓

Low Stock Event

├── Amazon SQS Queue
│ └── Lambda Consumer

└── Amazon EventBridge
    └── Lambda Consumer

↓

Amazon Cognito JWT Authentication

---

## Features

* Multi-Tenant SaaS Design
* JWT Authentication with Amazon Cognito
* Drug Inventory Management
* Low Stock Detection
* Event-Driven Processing
* SQS Queue Processing
* EventBridge Event Routing
* Dead Letter Queue (DLQ) Support
* Infrastructure as Code using AWS SAM
* Automated Deployment Pipelines

---

## AWS Services Used

* AWS Lambda
* Amazon API Gateway
* Amazon DynamoDB
* Amazon Cognito
* Amazon SQS
* Amazon EventBridge
* AWS IAM
* AWS CloudWatch
* AWS SAM
* AWS CloudFormation

---

## Skills Demonstrated

* Serverless Architecture
* Event-Driven Design
* Cloud Engineering
* AWS Solutions Architecture
* Multi-Tenant SaaS Design
* Infrastructure as Code
* Security and Identity Management
* DynamoDB Data Modeling
* API Development
* DevOps Automation

---

## Technical Highlights

### Tenant Isolation

Inventory records are stored using:

PK = TENANT#{tenant_id}

SK = DRUG#{drug_id}

This provides logical isolation between customers while maintaining a cost-efficient shared infrastructure model.

### Event Processing

Low-stock inventory events are published to:

* Amazon SQS for reliable background processing
* Amazon EventBridge for event routing and integration

### Reliability

* Dead Letter Queues
* Retry Mechanisms
* Lambda Event Source Mappings
* Failure Handling Patterns

---

## Future Enhancements

* Prescription Management
* Patient Records
* Inventory Forecasting
* Notification Services
* Analytics Dashboards
* CI/CD Automation

---

## Deployment

Deployment instructions are available through AWS SAM and CloudFormation templates included in this repository.
