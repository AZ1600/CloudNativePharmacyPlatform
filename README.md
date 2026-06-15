# Cloud-Native Multi-Tenant Pharmacy Inventory Platform

## Overview

Cloud-native serverless pharmacy inventory platform designed using AWS managed services and event-driven architecture principles.

The solution enables healthcare organisations to securely manage pharmaceutical inventory, monitor stock levels, trigger automated low-stock workflows, and support tenant-isolated SaaS operations from a shared infrastructure model.

The platform demonstrates modern cloud engineering practices including:

* Serverless application design
* Event-driven architecture
* Infrastructure as Code (AWS SAM)
* Multi-tenant SaaS data modelling
* Secure API authentication and authorisation
* Automated deployment pipelines

The solution was built using AWS Lambda, API Gateway, DynamoDB, Amazon Cognito, Amazon SQS, Amazon EventBridge and AWS CloudFormation.

---

## Architecture

```text
                ┌─────────────────────┐
                │ Client Application  │
                └──────────┬──────────┘
                           │
                           ▼
                 Amazon API Gateway
                           │
                           ▼
                      AWS Lambda
                           │
                           ▼
                    Amazon DynamoDB
                           │
                Low Stock Event Created
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                     ▼

   Amazon SQS Queue                    Amazon EventBridge
        │                                     │
        ▼                                     ▼

   Lambda Consumer                     Lambda Consumer

                           ▲
                           │
                  Amazon Cognito
               JWT Authentication
```

---

## Key Features

* Multi-Tenant SaaS Architecture
* JWT Authentication with Amazon Cognito
* Drug Inventory Management
* Automated Low Stock Detection
* Event-Driven Processing
* Amazon SQS Queue Integration
* Amazon EventBridge Event Routing
* Dead Letter Queue (DLQ) Support
* Infrastructure as Code with AWS SAM
* Automated Deployment Pipelines
* Tenant-Isolated Data Model
* Serverless Compute Architecture

---

## AWS Services Used

* AWS Lambda
* Amazon API Gateway
* Amazon DynamoDB
* Amazon Cognito
* Amazon SQS
* Amazon EventBridge
* AWS IAM
* Amazon CloudWatch
* AWS SAM
* AWS CloudFormation

---

## Skills Demonstrated

### Cloud Engineering

* Serverless Architecture Design
* Event-Driven System Design
* Multi-Tenant SaaS Architecture
* Cloud Security and Identity Management
* API Development and Integration

### DevOps & Platform Engineering

* Infrastructure as Code (IaC)
* AWS SAM Deployments
* CI/CD Pipeline Integration
* Cloud Resource Automation
* Environment Provisioning

### AWS Services

* Lambda
* API Gateway
* DynamoDB
* Cognito
* SQS
* EventBridge
* IAM
* CloudFormation
* CloudWatch

---

## Project Outcomes

This project demonstrates the ability to:

* Design and implement a multi-tenant SaaS platform
* Build secure serverless APIs using AWS managed services
* Implement event-driven workflows using SQS and EventBridge
* Model scalable DynamoDB data structures
* Apply Infrastructure as Code principles using AWS SAM
* Design resilient cloud-native systems with retries and dead-letter queues
* Implement authentication and authorization using Amazon Cognito
* Build loosely coupled distributed systems

---

## Technical Highlights

### Tenant Isolation

Inventory data is stored using a single-table DynamoDB design:

```text
PK = TENANT#{tenant_id}
SK = DRUG#{drug_id}
```

This provides logical isolation between customers while maintaining a cost-efficient shared infrastructure model.

---

### Event Processing

When inventory falls below a defined threshold, the platform publishes events to:

* Amazon SQS for reliable asynchronous processing
* Amazon EventBridge for event routing and service integration

This demonstrates two common event-driven architectural patterns used in production AWS environments.

---

### Reliability & Resilience

The platform incorporates:

* Dead Letter Queues (DLQs)
* Retry Mechanisms
* Lambda Event Source Mappings
* Failure Handling Patterns
* Asynchronous Processing
* Decoupled Service Architecture

---

## Repository Structure

```text
.
├── create_drug_lambda.py
├── process_low_stock_alert_lambda.py
├── process_low_stock_eventbridge_lambda.py
├── template.yaml
├── buildspec.yml
├── pipeline-template.yaml
├── samconfig.toml
├── test_create_drug_lambda.py
└── README.md
```

---

## Future Enhancements

Planned improvements include:

* Prescription Management
* Patient Records
* Automated Notifications
* Inventory Forecasting
* Analytics Dashboards
* Advanced Reporting
* CI/CD Pipeline Enhancements
* Multi-Region Deployment Support

---

## Deployment

The platform is deployed using AWS SAM and AWS CloudFormation.

### Build

```bash
sam build
```

### Deploy

```bash
sam deploy --guided
```

### Run Tests

```bash
python3 -m unittest test_create_drug_lambda.py
```

---

## Author

**Olawale Azeez**

Cloud Engineer | Platform Engineer | DevOps Engineer

Focused on building cloud-native platforms, internal developer platforms, automation solutions, and scalable AWS infrastructure.
