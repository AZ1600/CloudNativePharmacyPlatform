# Gaming Tournament Platform

A social competitive gaming platform MVP where users can:

- sign up and create gamer profiles
- choose games like FIFA, COD, and MK
- join free tournaments
- track live scores
- stream matches
- compete on regional and global leaderboards

## MVP Scope

This version focuses on:

- profiles
- free tournaments
- scheduled draws and fixtures
- live score updates
- leaderboard views
- stream metadata

This version does not yet include:

- payments
- wallets
- prize payouts
- betting

## Project Structure

- `docs/architecture.md`: system design
- `docs/api.md`: API shape
- `docs/data-model.md`: core entities and table design
- `backend/`: AWS SAM backend
- `tests/`: test placeholders

## Suggested Build Order

1. Auth and profiles
2. Tournament creation and join flow
3. Match scheduling and score submission
4. Leaderboards
5. Streaming metadata and featured streams

## Current Backend Endpoints

- `POST /profiles`
- `GET /profiles/me`
- `POST /tournaments`
- `GET /tournaments`
- `POST /tournaments/{tournament_id}/join`
- `GET /tournaments/{tournament_id}/matches`
- `POST /matches`
- `GET /matches/{match_id}`
- `POST /matches/{match_id}/score`
- `GET /leaderboards`

## Current Domain Events

- `TournamentCreated`
- `PlayerJoinedTournament`
- `MatchScoreUpdated`
- `FixturesGenerated`
