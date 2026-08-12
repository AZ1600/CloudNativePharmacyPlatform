# Engineering Learning Journal

This journal explains what I learned while building and improving the Cloud-Native Pharmacy Inventory Platform. It records the reasoning behind the implementation, not only the finished feature list.

## 1. Start with a thin, complete workflow

The most useful early product slice is:

1. Authenticate a pharmacy operator.
2. Resolve their tenant from verified token claims.
3. Read that tenant's inventory.
4. Add a medicine batch.
5. identify low stock and emit an event.
6. Show the saved result in the dashboard.

A UI that looks complete but cannot finish this sequence is still a prototype. Connecting the add-medicine modal taught me to trace a feature across React state, API types, HTTP requests, Lambda validation, DynamoDB records, and the refreshed interface.

## 2. API contracts must be explicit

The backend originally returned `id`, while the frontend expected `drug_id`. Both sides compiled independently, but live records would have an undefined ID.

The lesson is that shared meaning matters more than local type safety. A production project should add one of the following:

- an OpenAPI specification used to generate types;
- shared schema validation;
- consumer-driven contract tests; or
- integration tests that exercise the deployed boundary.

For now, the documented response contract and frontend mapping both use `id`.

## 3. Tenant isolation belongs at every layer

The platform reads `custom:tenant_id` or `custom:hospital_id` from verified Cognito JWT claims. It does not accept a tenant ID from the request body. DynamoDB keys then scope every inventory query to that tenant.

This provides logical isolation, but production confidence also requires negative tests:

- Tenant A cannot read Tenant B records.
- Tenant A cannot create or update a Tenant B record.
- Missing or unrecognised roles are denied.
- Logs and events do not expose data across tenants.

Authentication proves identity. Authorisation decides what that identity may do. Tenant filtering must never rely on the frontend.

## 4. Validation must protect the domain

HTML form validation improves usability, but the backend remains the security boundary. The create Lambda now checks:

- required fields;
- non-empty medicine and batch names;
- non-negative whole-number quantities;
- a valid ISO `YYYY-MM-DD` expiry date; and
- an expiry date in the future.

Future validation should include field-length limits, normalised batch identifiers, duplicate-batch protection, approved units of measure, and tenant-specific medicine catalogues.

## 5. Distributed side effects change error handling

The current create path writes DynamoDB and then publishes the same low-stock fact to several AWS services. If publication fails after the write, returning HTTP 500 is misleading: part of the request already succeeded. Retrying may create another record and duplicate events.

The production lesson is to make the database write the source of truth and publish asynchronously. Strong options include:

- DynamoDB Streams;
- a transactional outbox record written with the medicine;
- idempotency keys for POST requests; and
- event consumers that ignore previously processed event IDs.

EventBridge can act as the main router, with SQS queues attached where buffered, retryable delivery is needed. Every event should include an event ID, schema version, timestamp, tenant ID, and correlation ID.

## 6. Mock data must never look like live clinical data

Mock inventory is useful for local development and screenshots. Silently falling back to realistic mock quantities after a production API failure is dangerous because an operator may assume the information is current.

The dashboard therefore labels its data source. A stronger production version should replace the table with a blocking error state whenever live data cannot be loaded, while enabling mock mode only through an explicit development setting.

## 7. Accessible modals need more than visual styling

The add-medicine dialog includes labelled controls, an alert region, Escape handling, disabled submitting controls, and responsive styling. A fully accessible modal should also:

- trap keyboard focus inside the dialog;
- restore focus to the opening button;
- prevent background content from being announced or focused;
- prevent background scrolling; and
- be tested using keyboard-only navigation and a screen reader.

Accessibility is an acceptance criterion, not a final cosmetic pass.

## 8. CI should validate what is deployed

Running only one backend test before deployment creates false confidence. CodeBuild now runs the complete Python test suite and validates the frontend lint and production build before `sam deploy`.

GitHub Actions already checks Python style, backend tests, coverage, CloudFormation templates, ESLint, and the frontend build. The next delivery improvements are:

- a coverage threshold;
- dependency and secret scanning;
- separate build and deployment jobs;
- immutable build artifacts;
- staging smoke tests;
- a manual production approval; and
- rollback alarms.

## 9. Error details belong in logs

Returning raw AWS exception messages can expose internal resource details. The API now sends stable public messages and records exceptions in CloudWatch logs.

The next step is structured logging with correlation IDs and CloudWatch metrics for:

- API errors by route and status;
- rejected authorisation attempts;
- low-stock event publication failures;
- DLQ depth;
- Lambda duration and throttling; and
- DynamoDB throttling or system errors.

Logs should provide operational evidence without containing secrets or unnecessary sensitive data.

## 10. Local development without AWS credentials

Most work can be validated locally because AWS SDK clients are mocked in unit tests.

```bash
python3 -m unittest discover --pattern "test_*.py" --verbose

cd frontend
npm ci
npm run lint
npm run build
```

Infrastructure can be checked with:

```bash
cfn-lint template.yaml
cfn-lint pipeline-template.yaml
sam validate --lint
sam build
```

AWS credentials are required only for deployment and real integration testing.

## 11. Git and pull-request workflow

Each coherent improvement should be developed on its own branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c descriptive-feature-name
```

Before opening a pull request:

```bash
git diff --check
python3 -m unittest discover --pattern "test_*.py" --verbose
cd frontend && npm run lint && npm run build
```

The developer should review the diff, choose the commit boundaries, push the branch, open the pull request, and merge only after CI and review pass.

## 12. Screenshot plan

Screenshots should be captured after the interface states are stable. A useful repository gallery will include:

1. Desktop inventory dashboard.
2. Add-medicine dialog with realistic but fictional values.
3. Successful medicine creation.
4. Low-stock and out-of-stock filtering.
5. Mobile layout.
6. Optional AWS architecture or CloudFormation deployment output with identifiers redacted.

Images should use consistent dimensions, contain no real credentials or patient data, and remain compressed enough for a fast repository landing page.

## 13. Next engineering sequence

The recommended next steps are:

1. Add frontend component and API tests.
2. Add idempotency and duplicate-batch protection.
3. Move event delivery to DynamoDB Streams or a transactional outbox.
4. Add paginated inventory reads.
5. Implement Cognito login, refresh, logout, and session-expiry handling.
6. Add stock adjustments, audit history, expiry warnings, and quarantine states.
7. Tighten CORS and deployment IAM.
8. Add observability, backup, recovery, and security controls.

The broader lesson is to improve the platform in vertical slices: finish the user experience, API contract, persistence, events, tests, and operations for one workflow before expanding the feature list.
