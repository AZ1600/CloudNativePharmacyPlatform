# API

## Profiles

### `POST /profiles`

Create a gamer profile.

Request body:

```json
{
  "gamer_tag": "AceStriker",
  "region": "UK",
  "country": "GB",
  "timezone": "Europe/London",
  "favorite_games": ["FIFA", "COD"],
  "stream_handle": "ace_streams"
}
```

### `GET /profiles/me`

Return the authenticated user's profile.

## Tournaments

### `POST /tournaments`

Create a free tournament.

Request body:

```json
{
  "title": "Weekly FIFA London Ladder",
  "game": "FIFA",
  "region": "UK",
  "frequency": "weekly",
  "draw_at": "2026-05-01T18:00:00Z"
}
```

`draw_at` is the scheduled UTC time when the tournament draw should happen and fixtures should be generated.

### `GET /tournaments`

List tournaments, optionally filtered by game and region.

### `POST /tournaments/{tournament_id}/join`

Join a tournament.

## Matches

### `POST /matches`

Create a match inside a tournament.

Request body:

```json
{
  "tournament_id": "tournament-123",
  "player_one": "user-1",
  "player_two": "user-2"
}
```

### `GET /matches/{match_id}`

Fetch match details.

### `GET /tournaments/{tournament_id}/matches`

Fetch all generated matches for a tournament after the draw.

### `POST /matches/{match_id}/score`

Submit a score and optional stream URL.

Request body:

```json
{
  "player_one_score": 2,
  "player_two_score": 1,
  "stream_url": "https://example.com/live/abc123"
}
```

## Leaderboards

### `GET /leaderboards?game=FIFA&region=UK`

Fetch leaderboard context for a game and region.

## Authentication

All endpoints require a Cognito JWT in the `Authorization: Bearer <token>` header.
