import asyncio

import aiodocker
import pytest
import pytest_asyncio


@pytest.fixture(scope="module")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def docker():
    docker = aiodocker.Docker()
    yield docker
    await docker.close()
