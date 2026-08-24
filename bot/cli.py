"""CLI wrapper for Pass24 actions used by Hermes skills."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _load_env() -> None:
    env_file = os.getenv("PASS24_ENV_FILE", "").strip()
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv(Path.cwd() / ".env")

def _json_print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _format_pass(pass_obj: dict[str, Any]) -> dict[str, Any]:
    guest = pass_obj.get("guestData") or {}
    return {
        "id": pass_obj.get("id"),
        "plate": guest.get("plateNumber"),
        "brand": pass_obj.get("comment"),
        "startsAt": pass_obj.get("startsAt"),
        "expiresAt": pass_obj.get("expiresAt"),
        "status": pass_obj.get("status"),
    }


async def _ensure_runtime_config(client: Any) -> None:
    if client.address_id and client.tenant_id:
        return
    discovered = await client.discover_config()
    client.address_id = discovered["address_id"]
    client.tenant_id = discovered["tenant_id"]
    client.vehicle_type = discovered["vehicle_type"]


async def _create(args: argparse.Namespace) -> int:
    from .api import client
    from .parser import parse_input

    try:
        if args.plate and args.brand:
            plate, brand = args.plate.strip().upper(), args.brand.strip()
        else:
            parsed = parse_input(args.text or "")
            if not parsed:
                _json_print({
                    "ok": False,
                    "error": "Не понял номер и марку. Пример: А123ВО77 Toyota",
                })
                return 2
            plate, brand = parsed

        await _ensure_runtime_config(client)
        pass_obj = await client.create_pass(plate, brand)
        _json_print({"ok": True, "action": "create", "pass": _format_pass(pass_obj)})
        return 0
    except Exception as exc:
        _json_print({"ok": False, "action": "create", "error": str(exc)})
        return 1
    finally:
        await client.close()


async def _list(args: argparse.Namespace) -> int:
    del args
    from .api import client

    try:
        today = date.today().isoformat()
        passes = await client.get_active_passes()
        today_passes = [
            _format_pass(p)
            for p in passes
            if str(p.get("startsAt") or "").startswith(today)
        ]
        _json_print({"ok": True, "action": "list", "passes": today_passes})
        return 0
    except Exception as exc:
        _json_print({"ok": False, "action": "list", "error": str(exc)})
        return 1
    finally:
        await client.close()


async def _cancel(args: argparse.Namespace) -> int:
    from .api import client

    try:
        await client.delete_pass(int(args.pass_id))
        _json_print({"ok": True, "action": "cancel", "pass_id": int(args.pass_id)})
        return 0
    except Exception as exc:
        _json_print({"ok": False, "action": "cancel", "error": str(exc)})
        return 1
    finally:
        await client.close()


async def _discover(args: argparse.Namespace) -> int:
    del args
    from .api import client

    try:
        discovered = await client.discover_config()
        _json_print({"ok": True, "action": "discover", "config": discovered})
        return 0
    except Exception as exc:
        _json_print({"ok": False, "action": "discover", "error": str(exc)})
        return 1
    finally:
        await client.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pass24 vehicle pass helper")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a vehicle pass for today")
    create.add_argument("text", nargs="?", help="Plate and brand, e.g. 'А123ВО77 Toyota'")
    create.add_argument("--plate", help="Vehicle plate")
    create.add_argument("--brand", help="Vehicle brand/model")
    create.set_defaults(func=_create)

    list_cmd = sub.add_parser("list", help="List today's passes")
    list_cmd.set_defaults(func=_list)

    cancel = sub.add_parser("cancel", help="Cancel/delete pass by id")
    cancel.add_argument("pass_id", type=int)
    cancel.set_defaults(func=_cancel)

    discover = sub.add_parser("discover", help="Discover address/tenant config")
    discover.set_defaults(func=_discover)

    return parser


def _missing_required_env() -> list[str]:
    required = ["PASS24_PHONE", "PASS24_PASSWORD"]
    return [name for name in required if not os.getenv(name, "").strip()]


def main() -> int:
    _load_env()
    parser = _build_parser()
    args = parser.parse_args()
    missing = _missing_required_env()
    if missing:
        _json_print({
            "ok": False,
            "error": "Pass24 credentials are not configured",
            "missing": missing,
        })
        return 2
    try:
        return asyncio.run(args.func(args))
    except Exception as exc:
        _json_print({"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
