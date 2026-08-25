"""Асинхронный клиент для Pass24 Mobile API."""
import logging
from datetime import date, datetime
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class Pass24Error(Exception):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


class Pass24Client:
    def __init__(self) -> None:
        self._token: str | None = None
        self._client = httpx.AsyncClient(
            base_url=settings.pass24_base_url,
            timeout=15.0,
            verify=False,  # у них протухший wildcard-сертификат
        )
        # Runtime-конфиг: заполняется из .env или auto-discovery при старте
        self.address_id: int = settings.pass24_address_id
        self.tenant_id: int = settings.pass24_tenant_id
        self.vehicle_type: int = settings.pass24_vehicle_type

    async def _login(self) -> None:
        resp = await self._client.post(
            "/auth/login",
            # Current Mobile API expects `phone`; older versions used `email`.
            json={"phone": settings.pass24_phone, "password": settings.pass24_password},
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("body")
        if not token or isinstance(token, dict):
            raise Pass24Error("Не удалось получить токен авторизации")
        self._token = token
        self._client.headers["Authorization"] = f"Bearer {self._token}"
        logger.info("Pass24: авторизация успешна")

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self._token:
            await self._login()
        resp = await self._client.request(method, path, **kwargs)
        if resp.status_code == 401:
            self._token = None
            await self._login()
            resp = await self._client.request(method, path, **kwargs)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            err = data["error"]
            raise Pass24Error(err.get("message", "Ошибка API"), err.get("code"))
        return data

    async def discover_config(self) -> dict:
        """Получить address_id, tenant_id, vehicle_type из истории пропусков."""
        data = await self._request("GET", "/passes", params={"page": 1})
        collection = data.get("body", {}).get("collection") or []
        if not collection:
            raise Pass24Error(
                "История пропусков пуста — не удалось определить address_id и tenant_id.\n"
                "Создайте хотя бы один пропуск через приложение Pass24, "
                "затем перезапустите бота."
            )
        p = collection[0]
        vehicle_type = settings.pass24_vehicle_type
        if p.get("guestType") == 2:
            vt = (p.get("guestData") or {}).get("vehicleType")
            if vt:
                vehicle_type = vt
        return {
            "address_id": p["address"]["id"],
            "tenant_id": p["tenant"]["id"],
            "vehicle_type": vehicle_type,
        }

    async def create_pass(self, plate: str, brand: str) -> dict:
        """Создать одноразовый пропуск на сегодня для ТС."""
        today = date.today()
        starts_at = datetime(today.year, today.month, today.day, 0, 0, 0)
        expires_at = datetime(today.year, today.month, today.day, 23, 59, 59)

        payload = {
            "addressId": self.address_id,
            "tenantId": self.tenant_id,
            "durationType": 1,
            "guestType": 2,
            "startsAt": starts_at.strftime("%Y-%m-%d %H:%M:%S"),
            "expiresAt": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            "guestData": {
                "vehicleType": self.vehicle_type,
                "plateNumber": plate,
                "typePlateNumber": "external",
                "name": f"{plate} — {brand}",
            },
            "comment": f"{plate} — {brand}",
        }
        data = await self._request("POST", "/passes", json=payload)
        return data.get("data") or data.get("body") or data

    async def get_active_passes(self) -> list[dict]:
        """Список пропусков (последние 20)."""
        data = await self._request("GET", "/passes", params={"page": 1})
        body = data.get("body", {})
        if isinstance(body, dict):
            return (body.get("collection") or [])[:20]
        return []

    async def delete_pass(self, pass_id: int) -> None:
        """Удалить пропуск по ID."""
        await self._request("DELETE", f"/passes/{pass_id}")

    async def get_pass_events(self, pass_id: int) -> list[dict]:
        """Получить события пропуска."""
        data = await self._request("GET", f"/passes/{pass_id}/events")
        body = data.get("body", {})
        if isinstance(body, dict):
            return body.get("collection") or []
        return []

    async def close(self) -> None:
        await self._client.aclose()


client = Pass24Client()
