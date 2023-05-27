import logging


def get_uvicorn_logger() -> logging.Logger:
    logger = logging.getLogger("uvicorn")
    logger.disabled = False
    return logger


def debug(msg: str) -> None:
    get_uvicorn_logger().debug(msg)


def info(msg: str) -> None:
    get_uvicorn_logger().info(msg)


def warn(msg: str) -> None:
    get_uvicorn_logger().warn(msg)


def error(msg: str) -> None:
    get_uvicorn_logger().error(msg)


# disable /health endpoint logging
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.args is None or len(record.args) < 3:
            return True

        if not isinstance(record.args, tuple):
            return True

        return record.args[2] != "/health"


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
