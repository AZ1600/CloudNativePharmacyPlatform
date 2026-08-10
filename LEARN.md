# Learning Journal

This document records what I learned while improving the Cloud Native Pharmacy Platform.

## Project Goal

The project demonstrates a cloud-native pharmacy inventory platform using:

- Python and AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB
- Amazon SQS
- Amazon SNS
- Amazon EventBridge
- Amazon Kinesis
- AWS SAM and CloudFormation
- React, TypeScript, and Vite
- GitHub Actions

## Development Without AWS Access

Most development and validation can be completed locally without AWS credentials.

Local validation includes:

- Python linting with Ruff
- Python unit tests
- Test coverage reporting
- CloudFormation and SAM validation with `cfn-lint`
- React linting
- TypeScript compilation
- Production frontend builds
- Local frontend testing with mock inventory data

AWS access is only required when deploying or testing against real AWS services.

## Git and Pull Request Workflow

Each improvement is developed on a separate branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c feature-branch-name