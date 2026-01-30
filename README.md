# Eco-Retail: AI-Driven Dynamic Pricing Engine 🍎📉

> **Turning Perishable Waste into Profitable Value through Intelligent Decision Automation.**

Eco-Retail is an end-to-end decision intelligence platform designed to minimize perishable inventory waste and maximize revenue recovery. By integrating batch-level tracking with machine learning demand forecasting, the system automates pricing actions to ensure products are sold before they expire.

---

## 🏗️ System Architecture

Eco-Retail moves beyond static reporting by implementing a **closed-loop architecture**. This ensures that every data point—from a POS transaction to an expiry date—results in an automated business decision.


### The Data-to-Decision Pipeline:
1.  **Ingestion:** Captures real-time sales and batch-specific inventory data (FIFO/FEFO).
2.  **Engineering:** Transforms raw data into "Inventory Pressure" features and temporal lags.
3.  **Forecasting:** A Gradient Boosted model predicts demand for the remaining shelf-life of each batch.
4.  **Optimization:** The Pricing Engine calculates the optimal markdown required to clear stock.
5.  **Execution:** Prices are served via REST API to digital price tags or POS systems.
6.  **Learning:** Post-pricing sales data is fed back into the pipeline to refine price elasticity models.

---

## ⚙️ Core Modules

### 1. Batch-Level Inventory Intelligence
Standard systems track products; Eco-Retail tracks **batches**. This allows the system to differentiate between "Milk" arriving today and "Milk" expiring tomorrow.
* **FEFO Logic:** Prioritizes First-Expiring-First-Out movement.
* **Expiry Risk Scoring:** Calculates the probability of a batch becoming waste based on current velocity.

### 2. Predictive Demand Modeling
The engine treats demand forecasting as a supervised learning problem.
* **Feature Engineering:** Includes rolling sales averages, price-point history, and seasonal trends.
* **Model:** Optimized Regressors (XGBoost/LightGBM) provide short-term (24-48hr) volume predictions.

### 3. Dynamic Pricing Engine
The "Action" layer that bridges the gap between analytics and operations.
* **Context-Aware Markdowns:** Instead of flat discounts, markdowns are scaled based on the gap between *Current Stock* and *Predicted Demand*.
* **Explainability:** Generates decision logs for every price change to ensure transparency for store managers.

---

## Project Setup and Execution

Follow the steps below to prepare your environment and run the application.

### 1. Configure the Virtual Environment
Create and activate a virtual environment to keep your dependencies isolated.

Windows:

```bash
python -m venv venv
.\venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Required Packages
With the virtual environment active, install all necessary libraries:

```bash
pip install -r requirements.txt
```

### 3. Run the Project
Launch the application by running the main script:

```bash
python main.py
```

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.9+ |
| **Data Processing** | Pandas, SQLAlchemy |
| **Machine Learning** | Scikit-learn, XGBoost |
| **API Framework** | FastAPI |
| **Database** | PostgreSQL (Relational Batch Tracking) |
| **Monitoring** | Streamlit (Business Dashboard) |

---

## 📈 Future Roadmap
**Phase 1:** Advanced demand forecasting using Deep Learning (LSTMs).
**Phase 2:** Real-time data streaming (Kafka) for instantaneous pricing updates.
**Phase 3:** Reinforcement Learning (RL) for automated price-elasticity discovery.

---

## 🚀 Key Business Impact

* **Revenue Recovery:** Captures value from aging inventory that would otherwise be a 100% loss.
* **Waste Reduction:** Drastically reduces the environmental footprint of perishable goods.
* **Operational Autonomy:** Reduces the manual labor involved in checking dates and applying manual discount stickers.

---

## 💡 Project Philosophy
> **"Prediction without action has zero business value."**
> This project is designed to demonstrate how ML models can be operationalized into a proactive, self-healing retail ecosystem.

---
