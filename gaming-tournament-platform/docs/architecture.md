# Architecture

## Product Overview

The platform is a free social gaming tournament app for players competing in games like:

- FIFA
- Call of Duty
- Mortal Kombat

Users can:

- sign up
- create gamer profiles
- join region-based tournaments
- submit and view live scores
- stream their matches
- climb leaderboards

## Core Services

### Auth Service

Handles sign up, login, and token-based access control.

### Profile Service

Stores:

- gamer tag
- avatar
- country
- region
- timezone
- favorite games
- stream handle

### Tournament Service

Handles:

- create tournament
- join tournament
- tournament region scope
- weekly and monthly tournament types
- scheduled draw time
- fixture generation

### Match Service

Handles:

- match creation
- player pairing
- match status
- score updates
- stream URL attachment

### Leaderboard Service

Builds:

- global rankings
- regional rankings
- game-specific rankings
- weekly/monthly rankings

### Stream Service

Stores:

- live stream link
- stream status
- match-to-stream association

## AWS Mapping

- `Amazon Cognito`: authentication
- `Amazon API Gateway`: HTTP API
- `AWS Lambda`: backend handlers
- `Amazon DynamoDB`: profiles, tournaments, matches
- `Amazon EventBridge`: domain events
- `Amazon SQS`: async jobs and notifications
- `Amazon CloudWatch`: logs and metrics
- `AWS X-Ray`: tracing
- `AWS CloudTrail`: audit trail

## Event Flow Examples

### Tournament Join

1. User joins tournament
2. Tournament record is updated
3. EventBridge publishes `PlayerJoinedTournament`
4. Matchmaking or notifications can react asynchronously

### Scheduled Draw

1. Tournament is created with a `draw_at` time
2. Players join until draw time
3. A scheduled Lambda checks for due tournaments
4. Fixtures are generated automatically
5. Tournament status moves from `OPEN` to `DRAWN`
6. EventBridge publishes `FixturesGenerated`

### Match Score Update

1. Player submits score
2. Match record updates
3. EventBridge publishes `MatchScoreUpdated`
4. Match score consumer processes the event asynchronously
5. Leaderboard recalculation or notifications can build on that later
