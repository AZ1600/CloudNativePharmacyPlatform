# Gaming App Architecture

## Product Shape

This MVP is a regional social gaming platform for free tournaments and live competition.

Users can:

- sign up
- create gamer profiles
- choose one or more supported games
- join tournaments by region
- submit live scores
- track leaderboards
- add live stream links

## Main Services

### Auth Service

Handles sign up, login, and JWT-based access control.

### Profile Service

Stores gamer profile data:

- gamer tag
- region
- country
- timezone
- favorite games
- streaming handle

### Tournament Service

Creates and manages:

- weekly tournaments
- monthly tournaments
- game-specific tournaments
- region-scoped tournaments

### Match Service

Tracks:

- tournament fixtures
- scheduled matches
- match status
- score submissions
- result confirmation

### Leaderboard Service

Builds rankings by:

- game
- region
- time period

### Stream Service

Stores and exposes:

- live stream URL
- stream status
- stream title
- featured match streams

## AWS Mapping

- `Amazon Cognito`: user auth
- `Amazon API Gateway`: HTTP API
- `AWS Lambda`: API handlers
- `Amazon DynamoDB`: profiles, tournaments, matches
- `Amazon EventBridge`: tournament and score events
- `Amazon SQS`: async notifications or background jobs
- `Amazon CloudWatch`: logs and alarms
- `AWS X-Ray`: trace requests
- `AWS CloudTrail`: audit infrastructure activity

## Data Model

### Profiles Table

- `PK = USER#{user_id}`
- `SK = PROFILE`

Attributes:

- `gamer_tag`
- `country`
- `region`
- `timezone`
- `favorite_games`
- `stream_handle`

### Tournaments Table

- `PK = TOURNAMENT#{tournament_id}`
- `SK = METADATA`

Attributes:

- `title`
- `game`
- `region_scope`
- `start_at`
- `frequency`
- `status`

### Participants

- `PK = TOURNAMENT#{tournament_id}`
- `SK = PLAYER#{user_id}`

### Matches

- `PK = MATCH#{match_id}`
- `SK = METADATA`

Attributes:

- `tournament_id`
- `player_one`
- `player_two`
- `player_one_score`
- `player_two_score`
- `status`
- `stream_url`

## Event Flow

1. User joins tournament
2. Tournament service stores participant
3. EventBridge publishes `PlayerJoinedTournament`
4. Match generation or notification handlers can react later

1. Match score is submitted
2. Match service updates the match
3. EventBridge publishes `MatchScoreUpdated`
4. Leaderboard service can rebuild rankings asynchronously

## Recommended Next Build Steps

1. Create profile endpoint
2. Create tournament endpoint
3. Join tournament endpoint
4. Submit score endpoint
5. Read leaderboard endpoint
