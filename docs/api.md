# API architecture

The whole API consists of multiple services:

- [Gateway](#gateway)
- [Users service](#users-service)
- [Trainings service](#trainings-service)
- [Targets service](#targets-service)
- [Metrics service](#metrics-service)

Each of these services don't know about each other, and accept requests from the *gateway* only.
You can see the OpenAPI documentation of the whole API at [gateway-megaredhand.cloud.okteto.net/docs](https://gateway-megaredhand.cloud.okteto.net/docs)

## Gateway

The purpose of this gateway is to provide a single entry point to the API.

Among its features, it provides:

- service management
- token invalidation on logout
- client request forwarding to services

For this, it uses a PostgreSQL database to store information on each service.
It also stores invalidated tokens, and blocks any request using one of these.

## Users service

[Link to repo](https://github.com/taller2-fiufit/svc-users)

...info about users service...

## Trainings service

[Link to repo](https://github.com/taller2-fiufit/svc-trainings)

This service is responsible for managing trainers' trainings.
Along with this, it also manages the favoriting and scoring of these.
It uses a *PostgreSQL* database to store this information, and sends messages to an AWS-SQS queue to notify the metrics service of important events.

## Targets service

[Link to repo](https://github.com/taller2-fiufit/svc-targets)

This service is responsible for managing athletes' targets.
Along with this, it also receives reports from the app regarding training metrics collected from users (distance ran, calories burned, etc.), that it uses to update their progress on each target.
It uses a *PostgreSQL* database to store this information.

## Metrics service

[Link to repo](https://github.com/taller2-fiufit/svc-metrics)

...info about metrics service...
