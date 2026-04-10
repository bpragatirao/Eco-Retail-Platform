-- ============================================================================
-- Eco-Retail Platform — Database Schema (v2.0)
-- Supports PostgreSQL and SQLite
-- ============================================================================

-- ── Products ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,           -- e.g. 'dairy', 'produce', 'bakery'
    base_price DECIMAL(10,2) NOT NULL,
    unit TEXT DEFAULT 'unit',         -- e.g. 'kg', 'litre', 'unit'
    min_margin DECIMAL(4,2) DEFAULT 0.10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

-- ── Inventory Batches ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory_batches (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    remaining_quantity INTEGER NOT NULL,
    expiry_date DATE NOT NULL,
    arrival_date DATE DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'active',     -- 'active', 'sold_out', 'expired', 'wasted'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX IF NOT EXISTS idx_batches_product ON inventory_batches(product_id);
CREATE INDEX IF NOT EXISTS idx_batches_expiry ON inventory_batches(expiry_date);
CREATE INDEX IF NOT EXISTS idx_batches_status ON inventory_batches(status);

-- ── Transactions ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    batch_id INTEGER,
    quantity_sold INTEGER NOT NULL,
    sale_price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),
    discount_pct DECIMAL(5,2) DEFAULT 0.0,
    sale_date DATE DEFAULT CURRENT_DATE,
    sale_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (batch_id) REFERENCES inventory_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_product ON transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(sale_date);

-- ── Pricing History ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pricing_history (
    pricing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    batch_id INTEGER,
    original_price DECIMAL(10,2) NOT NULL,
    dynamic_price DECIMAL(10,2) NOT NULL,
    discount_pct DECIMAL(5,2) DEFAULT 0.0,
    waste_risk_score DECIMAL(5,2),
    reason TEXT,                      -- e.g. 'near_expiry', 'overstock', 'low_demand'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (batch_id) REFERENCES inventory_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_pricing_product ON pricing_history(product_id);

-- ── Waste Log ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS waste_log (
    waste_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    quantity_wasted INTEGER NOT NULL,
    value_lost DECIMAL(10,2) NOT NULL,
    waste_date DATE DEFAULT CURRENT_DATE,
    reason TEXT DEFAULT 'expired',    -- 'expired', 'damaged', 'recalled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (batch_id) REFERENCES inventory_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_waste_product ON waste_log(product_id);
CREATE INDEX IF NOT EXISTS idx_waste_date ON waste_log(waste_date);
