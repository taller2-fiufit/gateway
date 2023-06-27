# API architecture

The whole API consists of multiple services:

- [Gateway](#gateway)
- [Users service](#users-service)
- [Trainings service](#trainings-service)
- [Targets service](#targets-service)
- [Metrics service](#metrics-service)

Each of these services don't know about each other, and accept requests from the *gateway* only.
You can see the OpenAPI documentation of the whole API at [gateway-megaredhand.cloud.okteto.net/docs](https://gateway-megaredhand.cloud.okteto.net/docs)

[Architecture Diagram](https://drive.google.com/file/d/1biSGY30BKVZ7lzDXBeCEgCB6vgVUsaGZ/view?usp=sharing)

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

This service is responsible for managing Kinetix Users.
It's mainly responsible for the lifecycle of the User entity, managing authentication and authorization, both for regular Users and Admins.
It uses a *PostgreSQL* database to store this information and sends messages to an AWS-SQS queue to notify the metrics service of important events.

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

This service is responsible for asynchronously receiving events from other Kinetix services and storing them for later retrieval. It also produces the business metrics consumed by the Backoffice.
It uses a *PostgreSQL* database to store this information and an AWS-SQS queue to handle event processing.
