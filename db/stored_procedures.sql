CREATE OR REPLACE FUNCTION flag_near_expiry()
RETURNS TABLE(batch_id INT) AS $$
BEGIN
    RETURN QUERY
    SELECT batch_id 
    FROM inventory_batches
    WHERE expirydate <= CURRENT_DATE + 3;
END;
$$ LANGUAGE plpgsql;