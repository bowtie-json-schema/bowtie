import aiodocker
import pytest_asyncio


@pytest_asyncio.fixture
async def docker():
    docker = aiodocker.Docker()
    yield docker
    await docker.close()
