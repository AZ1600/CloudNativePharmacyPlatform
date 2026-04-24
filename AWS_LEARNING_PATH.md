# AWS Step-By-Step With Your App

This repo is already a strong fit for `AWS SAM + CloudFormation + Lambda + API Gateway`.

That matters because `Elastic Beanstalk` is best for:

- a Flask, Django, Express, Spring Boot, or container web app
- a long-running worker process
- an app you want hosted on EC2 under the hood

Your current repo is not that kind of app yet. It is a `serverless microservice`, so the right move is:

1. learn the AWS delivery workflow with this app first
2. add CI/CD and observability to this app
3. then, if you have a separate web app later, deploy that one with Elastic Beanstalk

## What You Have Now

This project now demonstrates:

- `CloudFormation` through `template.yaml`
- `Lambda + API Gateway`
- `DynamoDB`
- `SQS + DLQ`
- `SNS`
- `Kinesis`
- `EventBridge`
- `X-Ray tracing`
- `CodeBuild + CodePipeline` infrastructure in `pipeline-template.yaml`

## Step 1. Understand The Flow

When a client calls `POST /drugs`:

1. API Gateway sends the request to `create_drug_lambda.py`
2. Lambda validates the JWT claims and request body
3. Lambda stores the drug in DynamoDB
4. If stock is low, Lambda publishes the same business event to:
   - `SQS` for durable queue-based processing
   - `SNS` for fan-out notifications
   - `EventBridge` for event routing
   - `Kinesis` for streaming analytics or downstream consumers

Use this mental model:

- `SQS` = queue and retry
- `SNS` = broadcast
- `EventBridge` = event routing
- `Kinesis` = streaming data pipeline

## Step 2. Deploy The App Manually First

Install the basics:

```bash
aws --version
sam --version
python3 --version
```

Configure credentials:

```bash
aws configure
```

Run tests:

```bash
python3 -m unittest test_create_drug_lambda.py
```

Build:

```bash
sam build
```

Deploy:

```bash
sam deploy --guided
```

Use values like:

- Stack name: `multi-tenant-pharmacy-api`
- Region: your preferred AWS region
- `UserPoolIssuer`: your Cognito issuer URL
- `UserPoolAudience`: your Cognito app client ID
- `StageName`: `prod`

## Step 3. Test The API

Get the stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name multi-tenant-pharmacy-api \
  --query "Stacks[0].Outputs"
```

Send a healthy stock request:

```bash
curl -X POST "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/prod/drugs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "drug_name": "Paracetamol 500mg",
    "batch_number": "BATCH-001",
    "quantity": 150,
    "reorder_level": 20,
    "expiry_date": "2027-12-31",
    "supplier": "Acme Pharma"
  }'
```

Send a low-stock request:

```bash
curl -X POST "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/prod/drugs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "drug_name": "Amoxicillin 250mg",
    "batch_number": "BATCH-LOW-001",
    "quantity": 10,
    "reorder_level": 20,
    "expiry_date": "2027-12-31",
    "supplier": "Acme Pharma"
  }'
```

For the low-stock request, you should see these booleans set to `true`:

- `low_stock_event_sent`
- `sns_event_sent`
- `eventbridge_event_sent`
- `kinesis_event_sent`

## Step 4. Verify The Messaging Services

Check the SQS queue:

```bash
aws sqs get-queue-attributes \
  --queue-url YOUR_LOW_STOCK_QUEUE_URL \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible
```

Read the Lambda logs:

```bash
aws logs tail /aws/lambda/multi-tenant-pharmacy-api-CreateDrugFunction --follow
aws logs tail /aws/lambda/multi-tenant-pharmacy-api-ProcessLowStockAlertFunction --follow
aws logs tail /aws/lambda/multi-tenant-pharmacy-api-ProcessLowStockEventBridgeFunction --follow
```

Read the Kinesis stream metadata:

```bash
aws kinesis describe-stream-summary \
  --stream-name multi-tenant-pharmacy-api-low-stock-stream
```

Read the SNS topic list:

```bash
aws sns list-topics
```

## Step 5. Observe, Trace, And Audit

### CloudWatch

Use CloudWatch Logs to inspect:

- request validation failures
- Lambda errors
- queue consumer activity
- business events like low stock detections

Useful commands:

```bash
aws logs describe-log-groups
aws logs tail /aws/lambda/multi-tenant-pharmacy-api-CreateDrugFunction --since 30m
```

### X-Ray

`Tracing: Active` is already enabled in the SAM template.

What to do:

1. open the X-Ray console
2. invoke the API a few times
3. inspect the service map
4. confirm the request path from API Gateway into Lambda
5. compare fast and slow requests

### CloudTrail

Use CloudTrail to answer:

- who deployed a stack
- who changed IAM permissions
- who invoked infrastructure APIs

Examples:

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateStack
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateStack
```

## Step 6. Add CI/CD Automation

This repo now includes:

- `buildspec.yml`
- `pipeline-template.yaml`

Deploy the pipeline stack:

```bash
aws cloudformation deploy \
  --template-file pipeline-template.yaml \
  --stack-name pharmacy-api-pipeline \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    RepositoryId=YOUR_GITHUB_ORG/YOUR_REPO \
    BranchName=main \
    ConnectionArn=YOUR_CODESTAR_CONNECTION_ARN \
    StackName=multi-tenant-pharmacy-api \
    UserPoolIssuer=YOUR_USER_POOL_ISSUER \
    UserPoolAudience=YOUR_USER_POOL_AUDIENCE \
    StageName=prod
```

How the pipeline works:

1. GitHub push triggers CodePipeline
2. CodePipeline sends the source to CodeBuild
3. CodeBuild runs unit tests
4. CodeBuild runs `sam build`
5. CodeBuild runs `sam deploy`
6. CloudFormation updates the stack automatically

## Step 7. IAM Security Best Practices In This Project

Practice these immediately:

- create a separate IAM user or role for deployment work
- avoid using the root account
- enable MFA
- keep Lambda policies least-privilege
- prefer role-based access instead of long-lived access keys
- rotate secrets and never hardcode credentials in code
- use CloudTrail to audit IAM and deployment activity

In this app, look at `CreateDrugFunction` in `template.yaml` and ask:

- does it only have the permissions it needs?
- can any wildcard policy be tightened later?
- which permissions belong in the app role versus the pipeline role?

## Step 8. Where Elastic Beanstalk Fits

Use Elastic Beanstalk for your next app if you have:

- a Flask or Django API
- a Node.js or Java web app
- a Dockerized app running continuously

The flow would be:

1. package the web app
2. create an Elastic Beanstalk application
3. create an environment
4. connect CodePipeline to build and deploy the app bundle
5. observe EC2 instances, logs, scaling, and IAM instance profiles

For this specific repo, do not force Elastic Beanstalk onto the Lambda app. It is better to master the serverless path here, then use EB with a separate web app.

## Step 9. Best Order To Learn Today

If we do this together in one sitting, use this order:

1. run unit tests locally
2. deploy the SAM stack
3. hit the API with a healthy-stock request
4. hit the API with a low-stock request
5. inspect SQS, SNS, EventBridge, and Kinesis behavior
6. inspect CloudWatch logs
7. inspect X-Ray traces
8. inspect CloudTrail events
9. deploy the CI/CD pipeline
10. push a small code change and watch the pipeline redeploy

## Step 10. What To Say In An Interview Or Exam

You can explain your app like this:

`I built a serverless pharmacy inventory microservice on AWS using SAM and CloudFormation. The API writes inventory data to DynamoDB and emits low-stock events to SQS, SNS, EventBridge, and Kinesis for different integration patterns. I enabled tracing with X-Ray, logging with CloudWatch, auditing with CloudTrail, and automated deployment with CodePipeline and CodeBuild.`
