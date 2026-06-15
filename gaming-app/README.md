# Gaming App MVP

This folder contains a starter backend design for a free competitive gaming platform where users can:

- sign up and create gamer profiles
- select games like FIFA, COD, and MK
- create or join free tournaments
- track live scores
- view leaderboards by game and region
- attach stream links for live matches

## MVP Scope

This first version does not handle:

- payments
- cash prizes
- withdrawals
- wallets

That keeps the product focused on social competition, live scores, and ranking.

## Core Services

- Auth
- Profiles
- Tournaments
- Matches
- Leaderboards
- Streams

## API Endpoints

- `POST /profiles`
- `GET /profiles/me`
- `POST /tournaments`
- `GET /tournaments`
- `POST /tournaments/{tournament_id}/join`
- `POST /matches/{match_id}/score`
- `GET /leaderboards`

## Files

- `template.yaml`: SAM template for the gaming backend
- `handlers/`: Lambda handlers
- `docs/architecture.md`: architecture and service design
