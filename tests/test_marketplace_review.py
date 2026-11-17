from pathlib import Path

from src.marketplace_review import BuyerUpdate, SellerAsset, review_listing


def test_caption_with_safety_signal_is_held_before_order_handoff() -> None:
    asset = SellerAsset("seller-17", Path("listing.jpg"), "Vintage item, stolen from a museum")
    buyer = BuyerUpdate("buyer-42", "Can you ship tomorrow?")

    handoff = review_listing(asset, buyer, "img-123")

    assert handoff.decision == "hold"
    assert handoff.asset_id == "img-123"
    assert handoff.seller_id == "seller-17"
