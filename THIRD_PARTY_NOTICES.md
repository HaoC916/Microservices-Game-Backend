# Third-Party Notices

## Nakama
- Name: Nakama
- Source: https://github.com/heroiclabs/nakama
- Notes:
  - We deploy official Nakama Docker images.
  - We do not vendor or redistribute Nakama source code in this repository.

## PostgreSQL (Runtime Dependency)
- Name: PostgreSQL Docker image
- Source: https://hub.docker.com/_/postgres
- Notes:
  - The baseline stack uses `postgres:12.2-alpine` as the runtime database service.

## Deprecated / Previously Considered
- Teeworlds was evaluated in an earlier scaffold and is now kept only under `infra/deprecated/teeworlds/` for project history.
