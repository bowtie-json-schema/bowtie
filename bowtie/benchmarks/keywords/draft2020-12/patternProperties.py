import string
import random

max_num = 100000


def get_benchmark():
    max_num_properties = 1000000
    benchmarks = []

    num_properties = 1000

    while num_properties <= max_num_properties:
        property_value_pairs = [(_random_string(), random.randint(0, max_num)) for _ in range(num_properties)]

        invalid_at_first = [(_random_string(), "string")] + property_value_pairs[1:]
        invalid_at_middle = (
                property_value_pairs[:num_properties // 2] + [(_random_string(), "string")] + property_value_pairs[num_properties // 2:-1]
        )
        invalid_at_last = property_value_pairs[1:] + [(_random_string(), "string")]
        valid = property_value_pairs

        benchmarks.append(dict(
            name=f"patternProperties_{num_properties}",
            description=(
                "A benchmark for measuring performance of the "
                "implementation for the patternProperties keyword."
            ),
            schema=dict(
                type="object",
                patternProperties={
                    "^[a-z]+$": {"type": "integer"}
                }
            ),
            tests=[
                dict(description="Invalid Property at first", instance=_get_instance_object(invalid_at_first)),
                dict(description="Invalid Property at middle", instance=_get_instance_object(invalid_at_middle)),
                dict(description="Invalid Property at last", instance=_get_instance_object(invalid_at_last)),
                dict(description="Valid", instance=_get_instance_object(valid)),
            ],
        ))

        num_properties *= 10

    return benchmarks


def _get_instance_object(property_value_pairs):
    return {
        key:value for key, value in property_value_pairs
    }


def _random_string():
    string_size = 100
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(string_size))
