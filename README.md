# AI Data Analyst Agent

A local business-intelligence dashboard that turns uploaded CSV or Excel data into KPIs, charts, automated insights, and answers to common business questions.

Built with Python, pandas, and Streamlit. The dashboard uses a local rule-based natural-language analytics engine, so it runs without an API key, paid model credits, or an internet connection after installation.

## Features

- Upload CSV and Excel datasets.
- Detect and prepare date columns automatically.
- Display revenue, profit, margin, orders, customers, and average order value.
- Explore revenue and profit by product, region, payment method, and month.
- Generate automatic business highlights such as top products, strongest regions, and best payment methods.
- Ask natural-language questions such as `What is the total revenue?`, `Show the top 3 products by profit`, or `Which region has the highest revenue?`

## Tech stack

- Python
- Streamlit
- pandas
- openpyxl (Excel file support)

## Run locally

1. Clone or download this repository.
2. Create and activate a virtual environment.

   ```bat
   py -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies.

   ```bat
   pip install -r requirements.txt
   ```

4. Start the dashboard.

   ```bat
   streamlit run app.py
   ```

5. Open the local address printed in the terminal, normally `http://localhost:8501`.

## Sample data

Use the included [sales_data.csv](data/sales_data.csv) file or upload your own CSV/XLSX dataset. For the full dashboard experience, include columns similar to:

```text
Order_ID, Order_Date, Customer_ID, Product, Region, Quantity,
Unit_Price, Payment_Method, Revenue, Profit, Customer_Satisfaction
```

The app gracefully handles datasets that do not contain every recommended column.

## Example questions

- What is the total revenue?
- What is the profit margin?
- Which 5 products have the highest revenue?
- Which region has the lowest sales?
- Show monthly revenue.
- Which payment method generates the most revenue?

## Project structure

```text
├── app.py                 # Streamlit dashboard and local analytics engine
├── data/sales_data.csv    # Sample dataset
├── create_dataset.py      # Sample-data generator
├── requirements.txt       # Runtime dependencies
└── README.md              # Project documentation
```

## Portfolio note

This project demonstrates data cleaning, exploratory analysis, business KPI design, dashboard development, and natural-language query handling with a local Python analytics workflow.
