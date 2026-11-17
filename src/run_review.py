from pathlib import Path

from marketplace_review import BuyerUpdate, InfraiClient, SellerAsset, publish_candidate


def main() -> None:
    asset = SellerAsset("seller-17", Path("sample-listing.jpg"), "Blue ceramic mug, handmade in a small batch")
    buyer = BuyerUpdate("buyer-42", "Please confirm the handle is intact.")
    key = __import__("os").environ.get("INFRAI_API_KEY")
    client = InfraiClient(key) if key and asset.image_path.exists() else None
    handoff = publish_candidate(asset, buyer, client)
    print(f"{handoff.decision}: {handoff.order_id} for {handoff.buyer_id}")


if __name__ == "__main__":
    main()
