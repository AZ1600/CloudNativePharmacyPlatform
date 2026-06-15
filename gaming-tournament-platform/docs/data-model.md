# Data Model

## Single Table Design

Primary keys:

- `PK`
- `SK`

Secondary index:

- `GSI1PK`
- `GSI1SK`

## Profile Item

- `PK = USER#{user_id}`
- `SK = PROFILE`

Attributes:

- `gamer_tag`
- `country`
- `region`
- `timezone`
- `favorite_games`
- `stream_handle`

## Tournament Item

- `PK = TOURNAMENT#{tournament_id}`
- `SK = METADATA`

Attributes:

- `title`
- `game`
- `region`
- `frequency`
- `draw_at`
- `status`
- `fixtures_generated`

GSI:

- `GSI1PK = GAME#{game}#REGION#{region}`
- `GSI1SK = TOURNAMENT#{title}`

## Tournament Participant Item

- `PK = TOURNAMENT#{tournament_id}`
- `SK = PLAYER#{user_id}`

Attributes:

- `user_id`
- `joined_at`

## Match Item

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

GSI:

- `GSI1PK = TOURNAMENT#{tournament_id}`
- `GSI1SK = MATCH#{match_id}`
