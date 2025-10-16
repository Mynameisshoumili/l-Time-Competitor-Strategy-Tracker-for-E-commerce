import json
import pandas as pd
from db import Session, ProductSnapshot
import os

def save_snapshot_to_db(platform: str, product_id: str, snapshot: dict) -> int:
    with Session() as s:
        obj = ProductSnapshot(
            platform=platform,
            product_id=product_id,
            title=snapshot.get("title"),
            price=snapshot.get("price"),
            list_price=snapshot.get("list_price"),
            discount_pct=snapshot.get("discount_pct"),
            currency=snapshot.get("currency", "INR"),
            promotions=snapshot.get("promotions"),
            raw=snapshot.get("raw")
        )
        s.add(obj)
        s.commit()
        s.refresh(obj)
        return obj.id

def append_to_csv(out_csv: str, platform: str, product_id: str, snapshot: dict):
    df = pd.DataFrame([{
        "platform": platform,
        "product_id": product_id,
        "title": snapshot.get("title"),
        "price": snapshot.get("price"),
        "list_price": snapshot.get("list_price"),
        "discount_pct": snapshot.get("discount_pct"),
        "promotions": json.dumps(snapshot.get("promotions")),
        "scraped_at": pd.Timestamp.now().isoformat(),
        "raw": json.dumps(snapshot.get("raw"))
    }])
    header = not os.path.exists(out_csv)
    df.to_csv(out_csv, mode="a", header=header, index=False)