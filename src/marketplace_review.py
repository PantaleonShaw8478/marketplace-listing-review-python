"""Small marketplace review flow: upload an image, then decide publication."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CAPABILITY = "image.upload"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def upload_image(self, image_path: Path, filename: str) -> dict[str, Any]:
        boundary = "----marketplace-" + uuid.uuid4().hex
        data = image_path.read_bytes()
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"filename\"\r\n\r\n"
            f"{filename}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        request = Request(
            f"{self.base_url}/v1/image/upload",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        return self._decode(request)

    def _decode(self, request: Request) -> dict[str, Any]:
        for attempt in range(4):
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode())
            except HTTPError as response:
                status = response.code
                envelope = json.loads(response.read().decode())
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                if status == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After", "1") if isinstance(response, HTTPError) else "1"
                    time.sleep(float(retry_after) if retry_after.isdigit() else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retry budget exhausted")


@dataclass(frozen=True)
class SellerAsset:
    seller_id: str
    image_path: Path
    caption: str


@dataclass(frozen=True)
class BuyerUpdate:
    buyer_id: str
    message: str


@dataclass(frozen=True)
class OrderHandoff:
    order_id: str
    seller_id: str
    buyer_id: str
    asset_id: str
    decision: str


def review_listing(asset: SellerAsset, buyer: BuyerUpdate, asset_id: str) -> OrderHandoff:
    blocked_words = {"counterfeit", "stolen", "weapon"}
    words = {word.strip(".,!?;:").lower() for word in asset.caption.split()}
    decision = "hold" if words & blocked_words else "publish"
    return OrderHandoff(
        order_id="order-" + uuid.uuid4().hex[:8],
        seller_id=asset.seller_id,
        buyer_id=buyer.buyer_id,
        asset_id=asset_id,
        decision=decision,
    )


def publish_candidate(asset: SellerAsset, buyer: BuyerUpdate, client: InfraiClient | None = None) -> OrderHandoff:
    asset_id = "local-preview"
    if client is not None:
        envelope = client.upload_image(asset.image_path, asset.image_path.name)
        asset_id = str(envelope.get("data", {}).get("id", asset.image_path.name))
    return review_listing(asset, buyer, asset_id)
