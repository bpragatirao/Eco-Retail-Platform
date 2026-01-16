from ml.predict_demand import predict_demand
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def dynamic_price(stock, days_to_expiry, base_price):

    today = datetime.today().weekday()
    predicted_demand = predict_demand(today)
    if days_to_expiry < 3 and predicted_demand < stock:
        discount = min(0.3, (stock - predicted_demand) / stock)
        final_price = base_price * (1 - discount)
    else:
        final_price = base_price

    price = round(final_price, 2)
    logger.info(f"Final price computed: {price}")
    return price
