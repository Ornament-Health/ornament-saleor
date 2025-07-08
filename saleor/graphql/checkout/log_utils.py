import logging
import traceback
import json
from functools import wraps

logger = logging.getLogger(__name__)


def serialize_result(log_prefix: str, result) -> str:
    try:
        # Saleor mutations often return a Graphene ObjectType with __dict__
        result_dict = {
            k: v for k, v in result.__dict__.items()
            if not k.startswith("_") and not callable(v)
        }
        return json.dumps(result_dict, indent=2, default=str)
    except Exception as e:
        logger.warning(f"{log_prefix} - Could not serialize result: %s", e)
        return str(result)


def safe_serialize(log_prefix: str, data):
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        logger.warning(f"{log_prefix} Could not serialize input data: %s", e)
        return str(data)


def log_mutation(log_prefix: str):
    def decorator(func):
        @wraps(func)
        def wrapper(cls, *args, **kwargs):
            input_str = safe_serialize(log_prefix=log_prefix, data=kwargs)
            logger.info(f"{log_prefix} - Input: {input_str}")

            try:
                result = func(cls, *args, **kwargs)

                result_str = serialize_result(log_prefix=log_prefix, result=result)
                logger.info(f"{log_prefix} - Success result_str = {result_str}")

                return result
            except Exception as e:
                logger.error(f"{log_prefix} - Error: %s", e)
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

        return wrapper
    return decorator
