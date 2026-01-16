print("Project: ECO-Retail Platform")
print() 

from ai.pricing_engine import dynamic_price
from ml.predict_demand import predict_demand
from datetime import datetime
from dashboard import run_dashboard
import subprocess
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

today = datetime.today().weekday()
print("Predicted demand:", predict_demand(today))

price = dynamic_price(
    stock=50,
    days_to_expiry=2,
    base_price=60.0,
)

print(f"Recommended price: ₹{price}")
# def run_dashboard(price):
#     subprocess.run([
#         sys.executable,
#         "-m",
#         "streamlit",
#         "run",
#         "eco-retail-platform/dashboard/app_streamlit.py"
#     ])

logger.info("Pipeline execution complete")
run_dashboard(price)