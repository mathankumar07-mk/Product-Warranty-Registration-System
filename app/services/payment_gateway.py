"""Payment-gateway abstraction.

Only an explicitly labelled sandbox adapter ships locally. A real gateway
must implement :class:`PaymentGateway` and verify webhooks with its own
signature scheme; the sandbox never claims to move real money.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class GatewayCharge:
    transaction_id: str
    success: bool


class PaymentGateway:
    name = "base"

    def charge(self, order_id: int, amount: Decimal, method: str) -> GatewayCharge:
        raise NotImplementedError

    def refund(self, transaction_id: str, amount: Decimal) -> bool:
        raise NotImplementedError

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        raise NotImplementedError


class SandboxGateway(PaymentGateway):
    """Labelled test adapter for local development only."""

    name = "sandbox"

    def charge(self, order_id: int, amount: Decimal, method: str, *, success: bool = True) -> GatewayCharge:
        import time

        return GatewayCharge(transaction_id=f"SANDBOX-{order_id}-{int(time.time())}", success=success)

    def refund(self, transaction_id: str, amount: Decimal) -> bool:
        return True

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        secret = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
        if not secret:
            # No shared secret configured: only accept explicitly labelled
            # sandbox payloads, never real-gateway claims.
            return signature == "sandbox"
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


def get_gateway() -> PaymentGateway:
    return SandboxGateway()
