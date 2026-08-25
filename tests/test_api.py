import json
import os
import unittest

import httpx


os.environ.setdefault("PASS24_PHONE", "masked-phone")
os.environ.setdefault("PASS24_PASSWORD", "masked-password")

from pass24_skill.api import Pass24Client, client as shared_client
from pass24_skill.config import settings


class LoginPayloadTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.request: httpx.Request | None = None

        async def handler(request: httpx.Request) -> httpx.Response:
            self.request = request
            return httpx.Response(200, json={"body": "masked-token"})

        self.client = Pass24Client()
        await self.client._client.aclose()
        self.client._client = httpx.AsyncClient(
            base_url="https://pass24.invalid/v1",
            transport=httpx.MockTransport(handler),
        )

    async def asyncTearDown(self) -> None:
        await self.client.close()

    async def test_login_uses_phone_key(self) -> None:
        await self.client._login()

        self.assertIsNotNone(self.request)
        assert self.request is not None
        self.assertEqual(self.request.url.path, "/v1/auth/login")
        payload = json.loads(self.request.content)
        self.assertEqual(
            payload,
            {
                "phone": settings.pass24_phone,
                "password": settings.pass24_password,
            },
        )
        self.assertNotIn("email", payload)


def tearDownModule() -> None:
    import asyncio

    asyncio.run(shared_client.close())


if __name__ == "__main__":
    unittest.main()
