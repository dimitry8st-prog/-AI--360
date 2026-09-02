"""Redis sliding-window limiter. If Redis is down, allow and log — core functions stay available."""

from app.core.logging import get_logger

logger = get_logger("rate_limit")


def parse_rate(spec: str) -> tuple[int, int]:
    count_s, period = spec.strip().lower().split("/", 1)
    count = int(count_s)
    window = {"second": 1, "minute": 60, "hour": 3600}.get(period, 60)
    return count, window


async def allow_request(redis, *, key: str, spec: str) -> bool:
    limit, window = parse_rate(spec)
    if redis is None:
        logger.warning("rate_limit_skipped", key=key, reason="redis_unavailable")
        return True
    try:
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, window)
        if current > limit:
            logger.warning("rate_limit_exceeded", key=key, current=current, limit=limit)
            return False
        return True
    except Exception:
        logger.warning("rate_limit_error", key=key)
        return True
