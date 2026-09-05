import datetime
import hashlib
import hmac
import json
import os
import platform
import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import requests
from loguru import logger

from app.config import config
from app.utils import utils

_SALT = "WexAuto_Security_Salt_2026_x89"
_CACHE_FILENAME = ".wex_license.cache"
_DEFAULT_VERIFY_URL = "https://raw.githubusercontent.com/Wex-DE/AI-Short-Video-Generator/main/userverify.txt"


class LicenseStatus(str, Enum):
    ACTIVE = "active"
    UNVERIFIED = "unverified"
    EXPIRED = "expired"
    BANNED = "banned"
    NETWORK_ERROR = "network_error"


@dataclass
class LicenseCheckResult:
    status: LicenseStatus
    device_id: str
    is_valid: bool
    message: str
    days_remaining: Optional[int] = None
    plan: Optional[str] = None
    expires_at: Optional[str] = None


def get_device_id() -> str:
    """
    Generates a deterministic, unique, and tamper-resistant Hardware Device ID.
    Uses Windows MachineGuid (or Motherboard UUID / CPU identifier).
    """
    raw_ids = []

    # 1. Windows MachineGuid from Registry
    if platform.system() == "Windows":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            ) as key:
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                if guid:
                    raw_ids.append(str(guid).strip())
        except Exception:
            pass

    # 2. System UUID via PowerShell as secondary fallback
    if platform.system() == "Windows" and not raw_ids:
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"],
                text=True,
                timeout=3,
                stderr=subprocess.DEVNULL,
            ).strip()
            if out:
                raw_ids.append(out)
        except Exception:
            pass

    # 3. CPU and Node information
    try:
        raw_ids.append(platform.processor() or platform.machine())
        import uuid
        raw_ids.append(str(uuid.getnode()))
    except Exception:
        pass

    combined_hardware_string = ":".join(raw_ids) if raw_ids else f"fallback-{platform.node()}"
    hashed = hashlib.sha256(f"{_SALT}:{combined_hardware_string}".encode("utf-8")).hexdigest()
    return f"0x{hashed[:10].upper()}"


def _get_cache_path() -> str:
    return os.path.join(utils.root_dir(), "storage", _CACHE_FILENAME)


def _load_license_cache(device_id: str) -> Optional[dict]:
    cache_path = _get_cache_path()
    if not os.path.isfile(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        signature = data.get("sig", "")
        payload = data.get("payload", {})
        expected_sig = hmac.new(
            _SALT.encode("utf-8"),
            json.dumps(payload, sort_keys=True).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(signature, expected_sig):
            if payload.get("device_id") == device_id:
                cache_time = payload.get("cached_at", 0)
                if time.time() - cache_time < 86400:
                    return payload
    except Exception as e:
        logger.warning(f"Failed to read license cache: {e}")
    return None


def _save_license_cache(device_id: str, plan: str, expires_at: Optional[str], days_remaining: Optional[int]) -> None:
    try:
        cache_path = _get_cache_path()
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        payload = {
            "device_id": device_id,
            "plan": plan,
            "expires_at": expires_at,
            "days_remaining": days_remaining,
            "cached_at": time.time(),
        }
        signature = hmac.new(
            _SALT.encode("utf-8"),
            json.dumps(payload, sort_keys=True).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"payload": payload, "sig": signature}, f)
    except Exception as e:
        logger.warning(f"Failed to save license cache: {e}")


def _get_activation_file_path(device_id: str) -> str:
    return os.path.join(utils.root_dir(), "storage", f".act_{device_id[2:]}.dat")


def _get_or_set_first_activation_date(device_id: str) -> datetime.date:
    """Tracks local first activation date securely for relative durations (30d, 60d)."""
    act_file = _get_activation_file_path(device_id)
    today = datetime.date.today()
    if os.path.isfile(act_file):
        try:
            with open(act_file, "r", encoding="utf-8") as f:
                content = json.load(f)
            stored_date_str = content.get("activated_on")
            sig = content.get("sig")
            expected_sig = hmac.new(_SALT.encode(), f"{device_id}:{stored_date_str}".encode(), hashlib.sha256).hexdigest()
            if hmac.compare_digest(sig, expected_sig):
                return datetime.date.fromisoformat(stored_date_str)
        except Exception:
            pass

    # First time activation
    try:
        sig = hmac.new(_SALT.encode(), f"{device_id}:{today.isoformat()}".encode(), hashlib.sha256).hexdigest()
        os.makedirs(os.path.dirname(act_file), exist_ok=True)
        with open(act_file, "w", encoding="utf-8") as f:
            json.dump({"activated_on": today.isoformat(), "sig": sig}, f)
    except Exception as e:
        logger.warning(f"Failed to record activation date: {e}")
    return today


def parse_verification_text(content: str) -> dict:
    """
    Parses userverify.txt lines.
    Format per line:
    <device_id>, <duration_or_date>, <status>
    Examples:
    0x8F3A19C42B, 30d, verified
    0x1234567890, 60d, ban
    0xABCDEF1234, 2026-12-31, verified
    """
    records = {}
    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            dev_id = parts[0].upper()
            if not dev_id.startswith("0X") and not dev_id.startswith("0x"):
                dev_id = f"0X{dev_id}"
            plan = parts[1]
            status = parts[2].lower() if len(parts) >= 3 else "verified"
            records[dev_id] = {
                "plan": plan,
                "status": status,
            }
    return records


def get_verification_url() -> str:
    configured = str(config.app.get("license_verification_url", "") or "").strip()
    return configured or _DEFAULT_VERIFY_URL


def check_device_license(custom_content: Optional[str] = None) -> LicenseCheckResult:
    """
    Evaluates license validity for the current machine.
    """
    device_id = get_device_id()

    content = custom_content
    fetch_error = None
    if content is None:
        url = get_verification_url()
        local_userverify = os.path.join(utils.root_dir(), "userverify.txt")
        if os.path.isfile(local_userverify):
            try:
                with open(local_userverify, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Error reading local userverify.txt: {e}")

        if content is None:
            try:
                cache_bust_url = f"{url}?_t={int(time.time())}" if "?" not in url else f"{url}&_t={int(time.time())}"
                headers = {"User-Agent": "WexAuto-License-Checker/1.0", "Cache-Control": "no-cache"}
                resp = requests.get(cache_bust_url, headers=headers, timeout=6)
                if resp.status_code == 200:
                    content = resp.text
                else:
                    fetch_error = f"HTTP {resp.status_code}"
            except Exception as e:
                fetch_error = str(e)

    # Fallback to cache if network fails
    if content is None:
        cached = _load_license_cache(device_id)
        if cached:
            days_rem = cached.get("days_remaining")
            plan = cached.get("plan", "Standard")
            exp = cached.get("expires_at")
            return LicenseCheckResult(
                status=LicenseStatus.ACTIVE,
                device_id=device_id,
                is_valid=True,
                message=f"License verified via offline cache ({days_rem} days remaining)",
                days_remaining=days_rem,
                plan=plan,
                expires_at=exp,
            )
        return LicenseCheckResult(
            status=LicenseStatus.NETWORK_ERROR,
            device_id=device_id,
            is_valid=False,
            message=f"Unable to connect to verification server. Please check your internet connection. ({fetch_error})",
        )

    records = parse_verification_text(content)
    dev_entry = records.get(device_id.upper())

    if not dev_entry:
        return LicenseCheckResult(
            status=LicenseStatus.UNVERIFIED,
            device_id=device_id,
            is_valid=False,
            message="Device is not activated. Please send your Device Code to the administrator.",
        )

    status = dev_entry.get("status", "verified")
    plan = dev_entry.get("plan", "30d")

    # Check Ban
    if status in ["ban", "banned", "suspended", "blocked"]:
        return LicenseCheckResult(
            status=LicenseStatus.BANNED,
            device_id=device_id,
            is_valid=False,
            message="This device has been suspended or banned by the administrator.",
            plan=plan,
        )

    today = datetime.date.today()

    # Lifetime license
    if plan.lower() in ["lifetime", "unlimited", "forever", "perm"]:
        _save_license_cache(device_id, plan="Lifetime", expires_at="Lifetime", days_remaining=9999)
        return LicenseCheckResult(
            status=LicenseStatus.ACTIVE,
            device_id=device_id,
            is_valid=True,
            message="Lifetime license active.",
            days_remaining=9999,
            plan="Lifetime",
            expires_at="Lifetime",
        )

    # Exact Date Format (YYYY-MM-DD)
    date_match = re.match(r"^\d{4}-\d{2}-\d{2}$", plan)
    if date_match:
        try:
            exp_date = datetime.date.fromisoformat(plan)
            diff_days = (exp_date - today).days
            if diff_days >= 0:
                _save_license_cache(device_id, plan=f"Fixed ({plan})", expires_at=plan, days_remaining=diff_days)
                return LicenseCheckResult(
                    status=LicenseStatus.ACTIVE,
                    device_id=device_id,
                    is_valid=True,
                    message=f"License active until {plan} ({diff_days} days left).",
                    days_remaining=diff_days,
                    plan="Standard",
                    expires_at=plan,
                )
            else:
                return LicenseCheckResult(
                    status=LicenseStatus.EXPIRED,
                    device_id=device_id,
                    is_valid=False,
                    message=f"License expired on {plan}. Please renew your subscription.",
                    days_remaining=0,
                    plan="Expired",
                    expires_at=plan,
                )
        except Exception:
            pass

    # Relative Days Format (e.g. 30d, 60d, 90d, 365d)
    day_match = re.match(r"^(\d+)\s*d(ays?)?$", plan.lower())
    if day_match:
        total_days = int(day_match.group(1))
        first_act_date = _get_or_set_first_activation_date(device_id)
        expiry_date = first_act_date + datetime.timedelta(days=total_days)
        diff_days = (expiry_date - today).days

        if diff_days >= 0:
            exp_str = expiry_date.isoformat()
            _save_license_cache(device_id, plan=f"{total_days} Days Plan", expires_at=exp_str, days_remaining=diff_days)
            return LicenseCheckResult(
                status=LicenseStatus.ACTIVE,
                device_id=device_id,
                is_valid=True,
                message=f"License active ({diff_days} days remaining).",
                days_remaining=diff_days,
                plan=f"{total_days} Days Plan",
                expires_at=exp_str,
            )
        else:
            return LicenseCheckResult(
                status=LicenseStatus.EXPIRED,
                device_id=device_id,
                is_valid=False,
                message=f"Subscription expired ({total_days} days limit exceeded). Please renew.",
                days_remaining=0,
                plan=f"{total_days} Days Plan",
                expires_at=expiry_date.isoformat(),
            )

    return LicenseCheckResult(
        status=LicenseStatus.ACTIVE,
        device_id=device_id,
        is_valid=True,
        message="License active.",
        days_remaining=30,
        plan="Standard",
        expires_at="Active",
    )
