CREATE TABLE inventory_batches (
    batch_id SERIAL PRIMARY KEY,
    product_id INT,
    quantity INT,
    expirydate DATE,
    arrival_date DATE
);

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    product_id INT,
    quantity_sold INT,
    sale_date DATE,
    price DECIMAL(10,2)
);
