import asyncio
import logging
from contextlib import asynccontextmanager
from time import monotonic

logger = logging.getLogger()

class Identity:
    def __init__(self, proxy, email=None, script_id=None):
        self.proxy = proxy
        self.email = email
        self.script_id = script_id
        self.last_used = None


class IdentityPool:
    def __init__(self, cooldown: float, proxies_file: str):
        """
        Initialize a pool of proxies to be used for requests.
        :param cooldown: in seconds, the time to wait before reusing a proxy.
        """
        available_proxies = []

        try:
            with open(proxies_file) as f:
                for line in f:
                    elems = line.strip().split(";")
                    available_proxies.append(elems)
        except FileNotFoundError:
            logger.error("File with proxies not found. Will use direct connection")
        self._total_identities = len(available_proxies)
        self._identities = asyncio.Queue()
        for triplet in available_proxies:
            self._identities.put_nowait(Identity(triplet[0], triplet[1], triplet[2]))
        self.cooldown = cooldown

    @asynccontextmanager
    async def get_identity(self) -> str | None:
        identity = await self._identities.get()
        if identity.last_used:
            await asyncio.sleep(self.cooldown - (monotonic() - identity.last_used))
        try:
            yield identity
        finally:
            identity.last_used = monotonic()
            self._identities.put_nowait(identity)

    @property
    def total_identities(self):
        return self._total_identities

