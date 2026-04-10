# 🍎 Eco-Retail — Intelligent Dynamic Pricing Platform

> **Turning Perishable Waste into Profitable Value**
> 
> An AI-driven dynamic pricing engine that reduces perishable food waste and optimizes retail revenue through batch-level inventory tracking, ML demand forecasting, and multi-factor waste risk scoring.

---

## ⚡ Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/your-username/eco-retail-platform.git
cd eco-retail-platform

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env if needed (SQLite is the default — no DB setup required)

# 5. Seed the database with synthetic data
python -m db.seed

# 6. Train the ML model
python -m ml.train_model

# 7. Launch the dashboard
python -m api.app
# Visit http://localhost:8000
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Dashboard (HTML/CSS/JS)               │
│   Overview · Pricing Simulator · Inventory · Analytics   │
└──────────────────────┬──────────────────────────────────┘
                       │ fetch()
┌──────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                        │
│   /api/products · /api/inventory · /api/price/calculate  │
│   /api/alerts · /api/analytics/waste · /api/analytics/   │
└────┬─────────────────┬──────────────────────┬───────────┘
     │                 │                      │
┌────▼────┐    ┌───────▼───────┐    ┌────────▼────────┐
│   DB    │    │  ML Engine    │    │  AI Pricing     │
│ SQLAlch │    │  RandomForest │    │  Multi-tier     │
│  ORM    │    │  Multi-feat   │    │  Waste Risk     │
└─────────┘    └───────────────┘    └─────────────────┘
```

---

## 📂 Project Structure

```
eco-retail-platform/
├── api/                    # FastAPI backend
│   ├── app.py              # Main API application (8 endpoints)
│   └── schemas.py          # Pydantic request/response models
├── ai/                     # AI decision-making layer
│   ├── pricing_engine.py   # Multi-tier dynamic pricing
│   └── waste_risk.py       # Waste risk scoring (0-100)
├── ml/                     # Machine learning
│   ├── train_model.py      # Multi-feature model training + evaluation
│   └── predict_demand.py   # Demand prediction with caching
├── db/                     # Database layer
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schema.sql          # SQL schema (5 tables)
│   └── seed.py             # Synthetic data generator
├── etl/                    # ETL pipeline
│   └── pipeline.py         # Extract → Transform → Load features
├── dashboard/              # Frontend
│   └── static/
│       ├── index.html      # Dashboard UI
│       ├── styles.css       # Design system (dark glassmorphism)
│       └── app.js          # Dashboard logic & Chart.js
├── tests/                  # Pytest suite
│   ├── test_waste_risk.py  # Waste risk scoring tests
│   └── test_api.py         # API integration tests
├── config.py               # Centralized configuration
├── .env.example            # Environment template
├── requirements.txt        # Dependencies (pinned)
├── pyproject.toml          # Python packaging
└── README.md               # This file
```

---

## 🧪 Key Features

### 🤖 AI Dynamic Pricing
- **Multi-tier discount strategy**: Critical (>70 risk) → aggressive discount, Warning (40-70) → moderate, Safe (<40) → maintain price
- **Waste risk scoring**: 4-factor composite score (expiry urgency, stock surplus, category perishability, inventory utilization)
- **Margin floor protection**: Never discounts below configurable minimum margin

### 📊 ML Demand Forecasting
- **Multi-feature model**: day of week, month, weekend flag, week of year, category, base price
- **Evaluation metrics**: MAE, RMSE, R² score with train/test split
- **Model versioning**: Timestamped saves with metadata JSON

### ✨ Premium Dashboard
- Dark mode with glassmorphism design
- Animated metric counters
- Interactive pricing simulator
- Real-time inventory with risk status
- Revenue trend & category charts
- Near-expiry alert system

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📡 API Documentation

Start the server and visit: **http://localhost:8000/docs**

FastAPI auto-generates interactive Swagger documentation for all endpoints.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9+ |
| Backend | FastAPI + Uvicorn |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy 2.0 |
| ML/AI | Scikit-learn, Pandas |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Testing | Pytest |

---

## 💡 Business Problem

Retailers lose billions annually because static pricing cannot adapt to the ticking clock of expiration dates. **Eco-Retail** solves this by:

1. **Tracking** inventory at the batch level (FIFO/FEFO)
2. **Predicting** demand using ML models
3. **Scoring** waste risk across multiple factors
4. **Adjusting** prices automatically as products approach expiry
5. **Learning** from sales conversion to refine future pricing

> *"Prediction without action has zero business value."*
> Eco-Retail doesn't just predict waste — it prevents it.
