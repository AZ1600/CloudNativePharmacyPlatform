# Deploy To AWS

This project uses AWS SAM to deploy:

- `create_drug_lambda.py` as a Lambda function
- `process_low_stock_alert_lambda.py` as an SQS consumer Lambda
- `process_low_stock_eventbridge_lambda.py` as an EventBridge consumer Lambda
- a DynamoDB table for tenant-scoped inventory data
- an API Gateway HTTP API
- a JWT authorizer that works with Cognito
- an SQS queue with a dead-letter queue for low-stock events
- EventBridge publishing for low-stock events

## 1. Prerequisites

Install or confirm access to:

- AWS CLI
- AWS SAM CLI
- an AWS account
- a Cognito User Pool
- a Cognito App Client

Check the tools:

```bash
aws --version
sam --version
```

Configure AWS credentials if needed:

```bash
aws configure
```

## 2. Cognito Setup

Your authenticated users need these custom claims in their token:

- `custom:role`
- `custom:hospital_id` or `custom:tenant_id`

For your current code, this is enough:

- `custom:role = HospitalAdmin` or `Pharmacist`
- `custom:hospital_id = hosp_001`

For the cleaner SaaS model later, also add:

- `custom:tenant_id = tenant_001`

Your Cognito issuer format looks like this:

```text
https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_example
```

Your audience is the Cognito App Client ID.

## 3. Build The App

From the project folder:

```bash
sam build
```

Run the unit tests:

```bash
python3 -m unittest test_create_drug_lambda.py
```

## 4. Deploy The Stack

Run the guided deployment once:

```bash
sam deploy --guided
```

Use values like:

- Stack Name: `multi-tenant-pharmacy-api`
- AWS Region: your preferred region
- Parameter `UserPoolIssuer`: your Cognito issuer URL
- Parameter `UserPoolAudience`: your Cognito app client ID
- Parameter `StageName`: `prod`
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save arguments to configuration file: `Y`

## 5. Test The API

After deploy, SAM prints the API URL. You can also get outputs with:

```bash
aws cloudformation describe-stacks \
  --stack-name multi-tenant-pharmacy-api \
  --query "Stacks[0].Outputs"
```

Call the endpoint with a valid JWT:

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

If `quantity <= reorder_level`, the API stores the drug and publishes a low-stock event to both SQS and EventBridge.

## 6. Test The Event-Driven Flow

Use a payload that triggers the low-stock path:

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

You should see `"low_stock_event_sent": true` and `"eventbridge_event_sent": true` in the API response.

Check the consumer Lambda logs:

```bash
aws logs tail /aws/lambda/multi-tenant-pharmacy-api-ProcessLowStockAlertFunction --follow
```

Check the EventBridge consumer logs:

```bash
aws logs tail /aws/lambda/multi-tenant-pharmacy-api-ProcessLowStockEventBridgeFunction --follow
```

Check the queue attributes:

```bash
aws sqs get-queue-attributes \
  --queue-url YOUR_LOW_STOCK_QUEUE_URL \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible
```

If processing keeps failing, SQS moves the message to the dead-letter queue after 3 receives.

## 7. Common Problems

`403 Unauthorized`

- The JWT is missing `custom:role`
- The role is not `HospitalAdmin` or `Pharmacist`
- The request is using the wrong Cognito user pool or app client

`400 Missing tenant identifier`

- Add `custom:hospital_id` now, or `custom:tenant_id` for the newer SaaS shape

`500 Database operation failed`

- Confirm Lambda has the right `TABLE_NAME`
- Confirm the stack deployed successfully
- Check CloudWatch logs for the function

`low_stock_event_sent` is `false`

- The created drug did not meet the condition `quantity <= reorder_level`
- Confirm the Lambda has the right `LOW_STOCK_QUEUE_URL`

Messages are stuck or reappearing in the queue

- Check the consumer Lambda CloudWatch logs
- Confirm the queue visibility timeout is longer than the function runtime
- Check the dead-letter queue for failed events

## 8. Why This Matters For The Exam

This extension gives you hands-on practice with:

- synchronous versus asynchronous patterns
- loose coupling with SQS
- routed events with EventBridge
- retries and dead-letter queues
- Lambda event source mappings
- failure handling in event-driven systems

Those are all common DVA-C02 exam themes.

## 9. SQS Vs EventBridge

Use `SQS` when you want:

- a queue that buffers messages
- retry behavior with a dead-letter queue
- consumers to process work at their own pace
- protection against traffic spikes

Use `EventBridge` when you want:

- event routing to multiple targets
- filtering with rules
- looser publish/subscribe architecture
- easy fan-out without changing the producer

For this project:

- SQS is the better fit for reliable background processing
- EventBridge is the better fit when many downstream services may care about low-stock events

## 10. SaaS Design Notes

The function stores items with:

- `PK = TENANT#{tenant_id}`
- `SK = DRUG#{drug_id}`

That gives you logical isolation per hospital or tenant while keeping one shared platform table. This is the pattern you will reuse for patients, prescriptions, invoices, and analytics-ready entities.
