"""
Seed the database with realistic synthetic retail data.
Generates products, inventory batches, transactions, pricing history, and waste logs.
"""

import random
from datetime import date, timedelta, datetime
from db.models import (
    init_db, get_session,
    Product, InventoryBatch, Transaction, PricingHistory, WasteLog
)
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Product Catalog ──────────────────────────────────────────────────────────
PRODUCTS = [
    # (name, category, base_price, unit, min_margin)
    ("Amul Toned Milk 1L", "dairy", 56.0, "litre", 0.08),
    ("Mother Dairy Curd 400g", "dairy", 35.0, "unit", 0.10),
    ("Britannia Cheese Slices", "dairy", 120.0, "pack", 0.12),
    ("Fresh Paneer 200g", "dairy", 80.0, "unit", 0.10),

    ("Banana (Dozen)", "produce", 40.0, "dozen", 0.15),
    ("Tomato 1kg", "produce", 30.0, "kg", 0.20),
    ("Spinach Bunch", "produce", 25.0, "bunch", 0.18),
    ("Apple Shimla 1kg", "produce", 160.0, "kg", 0.12),
    ("Onion 1kg", "produce", 35.0, "kg", 0.20),
    ("Capsicum Green 500g", "produce", 45.0, "kg", 0.15),

    ("Harvest Gold Bread", "bakery", 45.0, "loaf", 0.10),
    ("Chocolate Muffin (2pc)", "bakery", 60.0, "pack", 0.15),
    ("Croissant Butter", "bakery", 50.0, "unit", 0.12),

    ("Chicken Breast 500g", "meat", 220.0, "pack", 0.10),
    ("Fish Fillet 300g", "meat", 280.0, "pack", 0.08),

    ("Orange Juice 1L", "beverages", 90.0, "litre", 0.12),
    ("Lassi Mango 200ml", "beverages", 25.0, "unit", 0.15),

    ("Greek Yogurt 150g", "dairy", 65.0, "unit", 0.10),
    ("Mixed Salad Pack", "produce", 70.0, "pack", 0.12),
    ("Whole Wheat Wrap (4pc)", "bakery", 55.0, "pack", 0.10),
]


def seed_products(session) -> list:
    """Insert products and return the list of product objects."""
    products = []
    for name, category, base_price, unit, min_margin in PRODUCTS:
        p = Product(
            name=name,
            category=category,
            base_price=base_price,
            unit=unit,
            min_margin=min_margin,
        )
        session.add(p)
        products.append(p)
    session.flush()
    logger.info(f"Seeded {len(products)} products")
    return products


def seed_inventory(session, products) -> list:
    """Generate inventory batches for each product (3-5 batches each)."""
    batches = []
    today = date.today()

    for product in products:
        num_batches = random.randint(3, 5)
        for i in range(num_batches):
            # Arrival: 1-14 days ago
            arrival = today - timedelta(days=random.randint(1, 14))

            # Expiry depends on category
            shelf_life = {
                "dairy": (5, 15),
                "produce": (3, 10),
                "bakery": (2, 7),
                "meat": (3, 7),
                "beverages": (14, 60),
            }
            min_life, max_life = shelf_life.get(product.category, (7, 30))
            expiry = arrival + timedelta(days=random.randint(min_life, max_life))

            quantity = random.randint(20, 150)
            # Some batches mostly sold, some barely touched
            sold_ratio = random.uniform(0.1, 0.95)
            remaining = max(1, int(quantity * (1 - sold_ratio)))

            # Mark expired batches
            status = "expired" if expiry < today else "active"

            batch = InventoryBatch(
                product_id=product.product_id,
                quantity=quantity,
                remaining_quantity=remaining,
                expiry_date=expiry,
                arrival_date=arrival,
                status=status,
            )
            session.add(batch)
            batches.append(batch)

    session.flush()
    logger.info(f"Seeded {len(batches)} inventory batches")
    return batches


def seed_transactions(session, products, batches) -> list:
    """Generate 60 days of transaction history."""
    transactions = []
    today = date.today()

    for day_offset in range(60):
        sale_date = today - timedelta(days=day_offset)
        weekday = sale_date.weekday()

        # More transactions on weekends
        base_tx_count = random.randint(15, 40)
        if weekday >= 5:
            base_tx_count = int(base_tx_count * 1.4)

        for _ in range(base_tx_count):
            product = random.choice(products)
            batch = random.choice([b for b in batches if b.product_id == product.product_id])

            qty = random.randint(1, 8)
            discount = 0.0

            # Simulate dynamic pricing — more discounts on items near expiry
            days_left = (batch.expiry_date - sale_date).days
            if days_left <= 2:
                discount = random.uniform(0.20, 0.45)
            elif days_left <= 5:
                discount = random.uniform(0.05, 0.20)

            sale_price = round(product.base_price * (1 - discount), 2)

            tx = Transaction(
                product_id=product.product_id,
                batch_id=batch.batch_id,
                quantity_sold=qty,
                sale_price=sale_price,
                original_price=product.base_price,
                discount_pct=round(discount * 100, 1),
                sale_date=sale_date,
            )
            session.add(tx)
            transactions.append(tx)

    session.flush()
    logger.info(f"Seeded {len(transactions)} transactions across 60 days")
    return transactions


def seed_pricing_history(session, products, batches):
    """Generate pricing adjustment history."""
    records = []
    today = date.today()

    for day_offset in range(30):
        adj_date = today - timedelta(days=day_offset)

        for product in random.sample(products, k=min(8, len(products))):
            product_batches = [b for b in batches if b.product_id == product.product_id]
            if not product_batches:
                continue
            batch = random.choice(product_batches)
            days_left = (batch.expiry_date - adj_date).days

            # Compute waste risk score
            stock_ratio = batch.remaining_quantity / max(batch.quantity, 1)
            expiry_urgency = max(0, 1 - (days_left / 10))
            waste_risk = round(min(100, (stock_ratio * 40 + expiry_urgency * 60)), 1)

            discount = 0.0
            reason = "normal"
            if waste_risk > 70:
                discount = random.uniform(0.25, 0.45)
                reason = "near_expiry"
            elif waste_risk > 40:
                discount = random.uniform(0.10, 0.25)
                reason = "overstock"
            elif waste_risk > 20:
                discount = random.uniform(0.02, 0.10)
                reason = "low_demand"

            dynamic_price = round(product.base_price * (1 - discount), 2)

            record = PricingHistory(
                product_id=product.product_id,
                batch_id=batch.batch_id,
                original_price=product.base_price,
                dynamic_price=dynamic_price,
                discount_pct=round(discount * 100, 1),
                waste_risk_score=waste_risk,
                reason=reason,
                created_at=datetime.combine(adj_date, datetime.min.time()),
            )
            session.add(record)
            records.append(record)

    session.flush()
    logger.info(f"Seeded {len(records)} pricing history records")


def seed_waste_log(session, products, batches):
    """Generate waste records for expired batches."""
    waste_entries = []
    today = date.today()

    for batch in batches:
        if batch.expiry_date < today and batch.remaining_quantity > 0:
            product = next(p for p in products if p.product_id == batch.product_id)
            entry = WasteLog(
                product_id=product.product_id,
                batch_id=batch.batch_id,
                quantity_wasted=batch.remaining_quantity,
                value_lost=round(batch.remaining_quantity * product.base_price, 2),
                waste_date=batch.expiry_date,
                reason="expired",
            )
            session.add(entry)
            waste_entries.append(entry)

    session.flush()
    logger.info(f"Seeded {len(waste_entries)} waste log entries")


def run_seed():
    """Run the full seeding pipeline."""
    logger.info("Initializing database...")
    init_db()

    session = get_session()
    try:
        # Clear existing data
        session.query(WasteLog).delete()
        session.query(PricingHistory).delete()
        session.query(Transaction).delete()
        session.query(InventoryBatch).delete()
        session.query(Product).delete()
        session.commit()

        logger.info("Seeding fresh data...")
        products = seed_products(session)
        batches = seed_inventory(session, products)
        seed_transactions(session, products, batches)
        seed_pricing_history(session, products, batches)
        seed_waste_log(session, products, batches)
        session.commit()
        logger.info("Database seeding complete!")

    except Exception as e:
        session.rollback()
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
