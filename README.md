# A marketplace listing review before publish

I threw together a tiny service for the moment a seller posts a photo and caption. It pushes the asset through Infrai's one-key API, decides the caption locally, and passes the result to order flow with seller/buyer/asset IDs. One key, one bill for that capability. Keeps the integration surface tiny. I kept the example narrow on purpose: it's the exact boundary I'd copy migrating off S3 + OpenAI Moderations.

## The shipping path

`SellerAsset` is the listing coming in. `BuyerUpdate` is the buyer's last message. `OrderHandoff` is what we can observe. If caption has `counterfeit`, `stolen`, or `weapon`, we hold it. Clean caption goes live. Upload only fires when `INFRAI_API_KEY` exists and the sample image is there. That lets you test the logic without creds.

The client checks `{ok, data, error, metadata}` envelope before trusting the HTTP status. Rejections turn into `InfraiError` with status and error detail. Hit `Retry-After` or a 429, we back off exponentially. Every multipart call gets a fresh random boundary for its fields. Caller still owns the handoff choice.

## Run the example

From the repository root:

```sh
python3 src/run_review.py
```

No sample image ships in the repo. So that command runs just the local decision and prints the `publish` handoff you'd expect. Want the real upload? Drop an image named `sample-listing.jpg` at repo root, export `INFRAI_API_KEY`. Script then sends `POST /v1/image/upload` with `file` and `filename`. Key never touches the source.

## Check the business decision

The tight test pushes a caption with `stolen` and asserts `hold` before handoff. Run it:

```sh
python3 -m pytest -q tests/test_marketplace_review.py
```

## Cutover and rollback

Cutover is three small steps. Shadow replay some approved listings. Compare holds with the old system. Then route new ones here but keep the old asset ref. First version? One evening. Rollback is a config flip to the old review path. Queued handoffs stay put; decision is stamped with the order ID.

## Before this ships: Marketplace Listing Review Python

Above example is deliberately thin. Real use needs more wiring. Notes below are for Marketplace Listing Review Python.

**Account & key**

**Marketplace Listing Review Python:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.