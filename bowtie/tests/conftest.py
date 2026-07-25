import asyncio

import pytest

from bowtie._containers import chosen_engine


@pytest.fixture(scope="module")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def engine():
    return chosen_engine()
