import streamlit as st
import re
import pandas as pd
from html import escape


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Data Analyst Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_money(value):
    """Format a number as Indian Rupees."""
    if pd.isna(value):
        value = 0

    return f"₹{value:,.2f}"


def format_number(value):
    """Format a number with commas."""
    if pd.isna(value):
        value = 0

    return f"{value:,.2f}"


# ============================================================
# LOCAL DATA ANALYST ENGINE
# ============================================================

def local_data_analyst(question, df):
    """
    100% local data analyst engine.

    No OpenAI API.
    No API credits.
    No internet required.

    Uses Python + Pandas to answer
    natural-language questions about the dataset.
    """

    if question is None or not str(question).strip():
        return "🤖 Please enter a question."

    q = str(question).lower().strip()

    # Make a copy so original dataframe is not modified
    data = df.copy()

    # ========================================================
    # PREPARE DATA
    # ===-=====================================================

    # Convert Order_Date
    if "Order_Date" in data.columns:
        data["Order_Date"] = pd.to_datetime(
            data["Order_Date"],
            errors="coerce",
            format="mixed"
        )

    # Convert numeric columns
    numeric_columns = [
        "Quantity",
        "Unit_Price",
        "Revenue",
        "Profit",
        "Customer_Satisfaction"
    ]

    for col in numeric_columns:
        if col in data.columns:
            data[col] = pd.to_numeric(
                data[col],
                errors="coerce"
            )

    # ========================================================
    # HELPER: CHECK COLUMN
    # ========================================================

    def has_column(column):
        return column in data.columns

    # ========================================================
    # HELPER: GET METRIC
    # ========================================================

    def get_metric(text):

        if "profit" in text:
            return "Profit", "profit"

        if (
            "quantity" in text
            or "units" in text
            or "selling" in text
            or "sold" in text
        ):
            return "Quantity", "quantity"

        if (
            "unit price" in text
            or "average price" in text
            or "price" in text
        ):
            return "Unit_Price", "unit price"

        return "Revenue", "revenue"

    # ========================================================
    # HELPER: FORMAT METRIC
    # ========================================================

    def metric_value(value, metric):

        if pd.isna(value):
            value = 0

        if metric == "Quantity":
            return f"{value:,.0f} units"

        if metric == "Unit_Price":
            return format_money(value)

        return format_money(value)

    # ========================================================
    # HELPER: FIND REGION
    # ========================================================

    def find_region(text):

        if not has_column("Region"):
            return None

        regions = (
            data["Region"]
            .dropna()
            .unique()
        )

        # Longest region names first
        regions = sorted(
            regions,
            key=lambda x: len(str(x)),
            reverse=True
        )

        for region in regions:

            if str(region).lower() in text:
                return region

        return None

    # ========================================================
    # HELPER: FIND PRODUCT
    # ========================================================

    def find_product(text):

        if not has_column("Product"):
            return None

        products = (
            data["Product"]
            .dropna()
            .unique()
        )

        # Longest names first
        products = sorted(
            products,
            key=lambda x: len(str(x)),
            reverse=True
        )

        for product in products:

            if str(product).lower() in text:
                return product

        return None

    # ========================================================
    # HELPER: REGION FILTER
    # ========================================================

    def apply_region_filter(frame, text):

        if "Region" not in frame.columns:
            return frame, None

        region = find_region(text)

        if region is not None:

            frame = frame[
                frame["Region"]
                .astype(str)
                .str.lower()
                == str(region).lower()
            ]

        return frame, region

    # ========================================================
    # HELPER: GROUPED RESULT
    # ========================================================

    def grouped_result(
        frame,
        group_column,
        metric,
        ascending=False,
        n=None
    ):

        if (
            group_column not in frame.columns
            or metric not in frame.columns
        ):
            return pd.Series(dtype="float64")

        result = (
            frame
            .groupby(group_column)[metric]
            .sum()
            .sort_values(
                ascending=ascending
            )
        )

        if n is not None:
            result = result.head(n)

        return result

    # ========================================================
    # METRIC DETECTION
    # ========================================================

    metric, metric_name = get_metric(q)

    # ========================================================
    # TOTAL REVENUE
    # ========================================================

    if (
        "total revenue" in q
        or "overall revenue" in q
        or q == "revenue"
        or "what is the revenue" in q
        or "how much revenue" in q
    ):

        if not has_column("Revenue"):
            return "❌ The dataset does not contain a Revenue column."

        total = data["Revenue"].sum()

        return (
            f"💰 **Total Revenue:** {format_money(total)}\n\n"
            f"Orders analyzed: **{len(data):,}**"
        )

    # ========================================================
    # TOTAL PROFIT
    # ========================================================

    if (
        "total profit" in q
        or "overall profit" in q
        or q == "profit"
        or "what is the profit" in q
        or "how much profit" in q
    ):

        if not has_column("Profit"):
            return "❌ The dataset does not contain a Profit column."

        total = data["Profit"].sum()

        return (
            f"📈 **Total Profit:** "
            f"{format_money(total)}"
        )

    # ========================================================
    # PROFIT MARGIN
    # ========================================================

    if (
        "profit margin" in q
        or q == "margin"
    ):

        if (
            not has_column("Revenue")
            or not has_column("Profit")
        ):
            return (
                "❌ Profit Margin requires "
                "Revenue and Profit columns."
            )

        revenue = data["Revenue"].sum()
        profit = data["Profit"].sum()

        margin = (
            profit / revenue * 100
            if revenue != 0
            else 0
        )

        return (
            f"📊 **Profit Margin:** "
            f"{margin:.2f}%"
        )

    # ========================================================
    # AVERAGE ORDER VALUE
    # ========================================================

    if (
        "average order value" in q
        or "average order" in q
        or "aov" in q
    ):

        if not has_column("Revenue"):
            return "❌ The dataset does not contain a Revenue column."

        # Average revenue per row/order
        aov = data["Revenue"].mean()

        return (
            f"🛒 **Average Order Value:** "
            f"{format_money(aov)}"
        )

    # ========================================================
    # TOTAL ORDERS
    # ========================================================

    if (
        "total orders" in q
        or "number of orders" in q
        or "how many orders" in q
    ):

        if "Order_ID" in data.columns:
            total_orders = data["Order_ID"].nunique()
        else:
            total_orders = len(data)

        return (
            f"🛒 **Total Orders:** "
            f"{total_orders:,}"
        )

    # ========================================================
    # TOTAL CUSTOMERS
    # ========================================================

    if (
        "total customers" in q
        or "total users" in q
        or "number of customers" in q
        or "number of users" in q
        or "unique customers" in q
    ):

        if not has_column("Customer_ID"):
            return (
                "❌ The dataset does not contain "
                "a Customer_ID column."
            )

        customers = data["Customer_ID"].nunique()

        return (
            f"👥 **Unique Customers:** "
            f"{customers:,}"
        )

    # ========================================================
    # SPECIFIC PRODUCT
    #
    # Examples:
    # profit of laptop
    # revenue from headphones
    # quantity sold for laptop
    # ========================================================

    product = find_product(q)

    if product is not None:

        product_data = data[
            data["Product"]
            .astype(str)
            .str.lower()
            == str(product).lower()
        ]

        # Product Profit
        if "profit" in q:

            if not has_column("Profit"):
                return (
                    "❌ The dataset does not contain "
                    "a Profit column."
                )

            value = product_data["Profit"].sum()

            return (
                f"📈 **Profit of {product}:** "
                f"{format_money(value)}"
            )

        # Product Revenue
        if (
            "revenue" in q
            or "sales" in q
        ):

            if not has_column("Revenue"):
                return (
                    "❌ The dataset does not contain "
                    "a Revenue column."
                )

            value = product_data["Revenue"].sum()

            return (
                f"💰 **Revenue of {product}:** "
                f"{format_money(value)}"
            )

        # Product Quantity
        if (
            "quantity" in q
            or "units" in q
            or "sold" in q
            or "selling" in q
        ):

            if not has_column("Quantity"):
                return (
                    "❌ The dataset does not contain "
                    "a Quantity column."
                )

            value = product_data["Quantity"].sum()

            return (
                f"📦 **{product} sold:** "
                f"{value:,.0f} units"
            )

        # Product Average Price
        if (
            "average price" in q
            or "unit price" in q
            or "price" in q
        ):

            if not has_column("Unit_Price"):
                return (
                    "❌ The dataset does not contain "
                    "a Unit_Price column."
                )

            value = product_data[
                "Unit_Price"
            ].mean()

            return (
                f"💵 **Average Unit Price "
                f"of {product}:** "
                f"{format_money(value)}"
            )

    # ========================================================
    # SPECIFIC REGION
    # Examples:
    # profit in south
    # revenue in west
    # ========================================================

    region = find_region(q)

    if (
        "region" in q
        and (
            "highest revenue" in q
            or "highest sales" in q
            or "top revenue" in q
            or "best revenue" in q
            or "best region" in q
        )
    ):

        result = (
            data.groupby("Region")["Revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        if not result.empty:

            best_region = result.index[0]
            best_revenue = result.iloc[0]

            return (
                f"🏆 **Highest Revenue Region:** "
                f"{best_region}\n\n"
                f"Revenue: **{format_money(best_revenue)}**"
            )

    if region is not None:

        region_data = data[
            data["Region"]
            .astype(str)
            .str.lower()
            == str(region).lower()
        ]

        # Region Profit
        if "profit" in q:

            if not has_column("Profit"):
                return (
                    "❌ The dataset does not contain "
                    "a Profit column."
                )

            value = region_data["Profit"].sum()

            return (
                f"📈 **Profit in {region}:** "
                f"{format_money(value)}"
            )

        # Region Revenue
        if (
            "revenue" in q
            or "sales" in q
        ):

            if not has_column("Revenue"):
                return (
                    "❌ The dataset does not contain "
                    "a Revenue column."
                )

            value = region_data["Revenue"].sum()

            return (
                f"💰 **Revenue in {region}:** "
                f"{format_money(value)}"
            )

    # ========================================================
    # TOP / BOTTOM N
    #
    # Examples:
    # top 3 products by profit
    # bottom 3 products by revenue
    # lowest 2 regions by sales
    # ========================================================

    n_match = re.search(
        r"(?:top|bottom|lowest|highest|best|least|most)\s+(\d+)",
        q
    )

    which_n_match = re.search(
        r"(?:which|show)\s+(\d+)\s+(?:products?|regions?)",
        q
    )

    n = None

    if n_match:
        n = int(n_match.group(1))

    elif which_n_match:
        n = int(which_n_match.group(1))

    if n is not None:

        lowest_request = (
            "bottom" in q
            or "lowest" in q
            or "least" in q
            or "worst" in q
        )

        filtered_data, selected_region = (
            apply_region_filter(
                data,
                q
            )
        )

        # ====================================================
        # PRODUCTS
        # ====================================================

        if "product" in q:

            if not has_column("Product"):
                return (
                    "❌ The dataset does not contain "
                    "a Product column."
                )

            if metric not in data.columns:
                return (
                    f"❌ The dataset does not contain "
                    f"a {metric} column."
                )

            result = grouped_result(
                filtered_data,
                "Product",
                metric,
                ascending=lowest_request,
                n=n
            )

            direction = (
                "Bottom"
                if lowest_request
                else "Top"
            )

            output = (
                f"{'📉' if lowest_request else '🏆'} "
                f"**{direction} {n} Products "
                f"by {metric_name}**"
            )

            if selected_region:
                output += (
                    f" in **{selected_region}**"
                )

            output += ":\n\n"

            for i, (name, value) in enumerate(
                result.items(),
                1
            ):

                output += (
                    f"{i}. **{name}** — "
                    f"{metric_value(value, metric)}\n"
                )

            return output

        # ====================================================
        # REGIONS
        # ====================================================

        if "region" in q:

            if not has_column("Region"):
                return (
                    "❌ The dataset does not contain "
                    "a Region column."
                )

            if metric not in data.columns:
                return (
                    f"❌ The dataset does not contain "
                    f"a {metric} column."
                )

            result = grouped_result(
                data,
                "Region",
                metric,
                ascending=lowest_request,
                n=n
            )

            direction = (
                "Bottom"
                if lowest_request
                else "Top"
            )

            output = (
                f"{'📉' if lowest_request else '🏆'} "
                f"**{direction} {n} Regions "
                f"by {metric_name}:**\n\n"
            )

            for i, (name, value) in enumerate(
                result.items(),
                1
            ):

                output += (
                    f"{i}. **{name}** — "
                    f"{metric_value(value, metric)}\n"
                )

            return output

    # ========================================================
    # MOST SELLING PRODUCT
    # ========================================================

    if (
        "most selling product" in q
        or "best selling product" in q
        or "top selling product" in q
        or "most sold product" in q
        or "highest selling product" in q
    ):

        if (
            not has_column("Product")
            or not has_column("Quantity")
        ):
            return (
                "❌ Most-selling analysis requires "
                "Product and Quantity columns."
            )

        result = (
            data
            .groupby("Product")["Quantity"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if result.empty:
            return "❌ No product data available."

        product_name = result.index[0]
        quantity = result.iloc[0]

        return (
            f"🏆 **Most Selling Product:** "
            f"{product_name}\n\n"
            f"Units sold: **{quantity:,.0f}**"
        )

    # ========================================================
    # LEAST SELLING PRODUCT
    # ========================================================

    if (
        "least selling product" in q
        or "worst selling product" in q
        or "least sold product" in q
        or "lowest selling product" in q
    ):

        if (
            not has_column("Product")
            or not has_column("Quantity")
        ):
            return (
                "❌ Least-selling analysis requires "
                "Product and Quantity columns."
            )

        result = (
            data
            .groupby("Product")["Quantity"]
            .sum()
            .sort_values()
        )

        if result.empty:
            return "❌ No product data available."

        product_name = result.index[0]
        quantity = result.iloc[0]

        return (
            f"📉 **Least Selling Product:** "
            f"{product_name}\n\n"
            f"Units sold: **{quantity:,.0f}**"
        )

    # ========================================================
    # REVENUE BY REGION
    # ========================================================

    if (
        "revenue by region" in q
        or "revenue of each region" in q
        or "sales by region" in q
        or "sales of each region" in q
    ):

        if (
            not has_column("Region")
            or not has_column("Revenue")
        ):
            return (
                "❌ Revenue by region requires "
                "Region and Revenue columns."
            )

        result = (
            data
            .groupby("Region")["Revenue"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        output = (
            "🌍 **Revenue by Region:**\n\n"
        )

        for name, value in result.items():

            output += (
                f"- **{name}:** "
                f"{format_money(value)}\n"
            )

        return output

    # ========================================================
    # PROFIT BY REGION
    # ========================================================

    if (
        "profit by region" in q
        or "profit of each region" in q
        or "profit for each region" in q
    ):

        if (
            not has_column("Region")
            or not has_column("Profit")
        ):
            return (
                "❌ Profit by region requires "
                "Region and Profit columns."
            )

        result = (
            data
            .groupby("Region")["Profit"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        output = (
            "📈 **Profit by Region:**\n\n"
        )

        for name, value in result.items():

            output += (
                f"- **{name}:** "
                f"{format_money(value)}\n"
            )

        return output

    # ========================================================
    # REVENUE BY PRODUCT
    # ========================================================

    if (
        "revenue by product" in q
        or "revenue of each product" in q
        or "sales by product" in q
        or "sales of each product" in q
    ):

        if (
            not has_column("Product")
            or not has_column("Revenue")
        ):
            return (
                "❌ Revenue by product requires "
                "Product and Revenue columns."
            )

        result = (
            data
            .groupby("Product")["Revenue"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        output = (
            "💰 **Revenue by Product:**\n\n"
        )

        for name, value in result.items():

            output += (
                f"- **{name}:** "
                f"{format_money(value)}\n"
            )

        return output

    # ========================================================
    # PROFIT BY PRODUCT
    # ========================================================

    if (
        "profit by product" in q
        or "profit of each product" in q
        or "profit for each product" in q
    ):

        if (
            not has_column("Product")
            or not has_column("Profit")
        ):
            return (
                "❌ Profit by product requires "
                "Product and Profit columns."
            )

        result = (
            data
            .groupby("Product")["Profit"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        output = (
            "📈 **Profit by Product:**\n\n"
        )

        for name, value in result.items():

            output += (
                f"- **{name}:** "
                f"{format_money(value)}\n"
            )

        return output

    # ========================================================
    # PAYMENT METHOD USERS
    # ========================================================

    if (
        "payment mode users" in q
        or "payment method users" in q
        or "users by payment" in q
        or "customers by payment" in q
        or "payment users" in q
    ):

        if (
            has_column("Payment_Method")
            and has_column("Customer_ID")
        ):

            result = (
                data
                .groupby(
                    "Payment_Method"
                )["Customer_ID"]
                .nunique()
                .sort_values(
                    ascending=False
                )
            )

            output = (
                "💳 **Users by Payment Method:**\n\n"
            )

            for mode, users in result.items():

                output += (
                    f"- **{mode}:** "
                    f"{users:,} users\n"
                )

            return output

        return (
            "❌ Payment user analysis requires "
            "Payment_Method and Customer_ID columns."
        )

    # ========================================================
    # REVENUE BY PAYMENT METHOD
    # ========================================================

    if (
        "revenue by payment" in q
        or "revenue by payment mode" in q
        or "revenue by payment method" in q
        or "sales by payment" in q
        or (
            "payment method" in q
            and (
                "most revenue" in q
                or "highest revenue" in q
                or "top revenue" in q
                or "generates the most" in q
                or "generated the most" in q
            )
        )
    ):

        if (
            not has_column("Payment_Method")
            or not has_column("Revenue")
        ):
            return (
                "❌ Payment revenue analysis requires "
                "Payment_Method and Revenue columns."
            )

        result = (
            data
            .groupby("Payment_Method")["Revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        if result.empty:
            return "❌ No payment method revenue data available."

        best_payment = result.index[0]
        best_payment_revenue = result.iloc[0]

        total_payment_revenue = result.sum()

        contribution = (
            best_payment_revenue / total_payment_revenue * 100
            if total_payment_revenue
            else 0
        )

        return (
            f"💳 **{best_payment}** generated the most revenue "
            f"with **{format_money(best_payment_revenue)}**, "
            f"accounting for **{contribution:.2f}%** "
            f"of payment-method revenue."
        )

        output = (
            "💳 **Revenue by Payment Method:**\n\n"
        )

        for mode, value in result.items():

            output += (
                f"- **{mode}:** "
                f"{format_money(value)}\n"
            )

        return output

    # ========================================================
    # PAYMENT CONTRIBUTION %
    # ========================================================

    if (
        "payment contribution" in q
        or "payment percentage" in q
        or "payment contribution percentage" in q
        or "contribution by payment" in q
    ):

        if (
            not has_column("Payment_Method")
            or not has_column("Revenue")
        ):
            return (
                "❌ Payment contribution requires "
                "Payment_Method and Revenue columns."
            )

        result = (
            data
            .groupby(
                "Payment_Method"
            )["Revenue"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        total = result.sum()

        output = (
            "📊 **Revenue Contribution "
            "by Payment Method:**\n\n"
        )

        for mode, value in result.items():

            percentage = (
                value / total * 100
                if total != 0
                else 0
            )

            output += (
                f"- **{mode}:** "
                f"{format_money(value)} "
                f"→ **{percentage:.2f}%**\n"
            )

        return output

    # ========================================================
    # MONTHLY REVENUE
    # ========================================================

    if (
        "monthly revenue" in q
        or "revenue by month" in q
        or "revenue each month" in q
        or "revenue per month" in q
    ):

        if (
            not has_column("Order_Date")
            or not has_column("Revenue")
        ):
            return (
                "❌ Monthly revenue requires "
                "Order_Date and Revenue columns."
            )

        temp = data.dropna(
            subset=["Order_Date"]
        ).copy()

        if temp.empty:
            return (
                "❌ No valid dates were found "
                "for monthly analysis."
            )

        monthly = (
            temp
            .groupby(
                temp["Order_Date"].dt.to_period("M")
            )["Revenue"]
            .sum()
        )

        output = (
            "📅 **Monthly Revenue:**\n\n"
        )

        for month, value in monthly.items():

            output += (
                f"- **{month}:** "
                f"{format_money(value)}\n"
            )

        return output

    # ========================================================
    # MONTHLY PROFIT
    # ========================================================

    if (
        "monthly profit" in q
        or "profit by month" in q
        or "profit each month" in q
        or "profit per month" in q
    ):

        if (
            not has_column("Order_Date")
            or not has_column("Profit")
        ):
            return (
                "❌ Monthly profit requires "
                "Order_Date and Profit columns."
            )

        temp = data.dropna(
            subset=["Order_Date"]
        ).copy()

        monthly = (
            temp
            .groupby(
                temp["Order_Date"].dt.to_period("M")
            )["Profit"]
            .sum()
        )

        output = (
            "📅 **Monthly Profit:**\n\n"
        )

        for month, value in monthly.items():

            output += (
                f"- **{month}:** "
                f"{format_money(value)}\n"
            )

        return output

    # ========================================================
    # MONTHLY CONTRIBUTION %
    # ========================================================

    if (
        "monthly contribution" in q
        or "monthly contribution percentage" in q
        or "monthly percentage" in q
        or "contribution percentage" in q
        or "contribution with respect to each month" in q
    ):

        if (
            not has_column("Order_Date")
            or not has_column("Revenue")
        ):
            return (
                "❌ Monthly contribution requires "
                "Order_Date and Revenue columns."
            )

        temp = data.dropna(
            subset=["Order_Date"]
        ).copy()

        monthly = (
            temp
            .groupby(
                temp["Order_Date"].dt.to_period("M")
            )["Revenue"]
            .sum()
        )

        total = monthly.sum()

        output = (
            "📊 **Monthly Revenue Contribution:**\n\n"
        )

        for month, value in monthly.items():

            percentage = (
                value / total * 100
                if total != 0
                else 0
            )

            output += (
                f"- **{month}:** "
                f"{format_money(value)} "
                f"→ **{percentage:.2f}%**\n"
            )

        return output

    # ========================================================
    # PRODUCTS ABOVE / BELOW CRITERIA
    #
    # Examples:
    # products with revenue above 1000000
    # products under profit 50000
    # products with quantity greater than 100
    # ========================================================

    criteria_match = re.search(
        r"(?:products?|items?)"
        r".*?"
        r"(revenue|profit|quantity|unit price)"
        r".*?"
        r"(above|over|greater than|more than|below|under|less than)"
        r"\s*(?:₹|rs\.?|inr)?\s*"
        r"([\d,]+(?:\.\d+)?)",
        q
    )

    if criteria_match:

        criteria_metric = criteria_match.group(1)
        operator = criteria_match.group(2)

        value = float(
            criteria_match
            .group(3)
            .replace(",", "")
        )

        column_map = {
            "revenue": "Revenue",
            "profit": "Profit",
            "quantity": "Quantity",
            "unit price": "Unit_Price"
        }

        column = column_map[
            criteria_metric
        ]

        if column not in data.columns:
            return (
                f"❌ The dataset does not contain "
                f"a {column} column."
            )

        product_values = (
            data
            .groupby("Product")[column]
            .sum()
        )

        if operator in [
            "above",
            "over",
            "greater than",
            "more than"
        ]:

            filtered = product_values[
                product_values > value
            ]

            operator_text = ">"

        else:

            filtered = product_values[
                product_values < value
            ]

            operator_text = "<"

        if filtered.empty:

            return (
                f"❌ No products found where "
                f"{criteria_metric} "
                f"{operator_text} "
                f"{format_money(value)}."
            )

        output = (
            f"🔎 **Products where "
            f"{criteria_metric} "
            f"{operator_text} "
            f"{format_money(value)}:**\n\n"
        )

        for product_name, result_value in (
            filtered.items()
        ):

            output += (
                f"- **{product_name}:** "
                f"{metric_value(result_value, column)}\n"
            )

        return output

    # ========================================================
    # AVERAGE UNIT PRICE
    # ========================================================

    if (
        "average unit price" in q
        or "average price" in q
    ):

        if (
            not has_column("Product")
            or not has_column("Unit_Price")
        ):
            return (
                "❌ Average price analysis requires "
                "Product and Unit_Price columns."
            )

        result = (
            data
            .groupby("Product")["Unit_Price"]
            .mean()
            .sort_values(
                ascending=False
            )
        )

        output = (
            "💵 **Average Unit Price by Product:**\n\n"
        )

        for product_name, value in result.items():

            output += (
                f"- **{product_name}:** "
                f"{format_money(value)}\n"
            )

        return output

    # ========================================================
    # DEFAULT RESPONSE
    # ========================================================

    return (
        "🤖 **I couldn't understand that question yet.**\n\n"
        "**Try asking:**\n\n"
        "- What is the total revenue?\n"
        "- What is the total profit?\n"
        "- What is the profit margin?\n"
        "- What is the average order value?\n"
        "- How many orders are there?\n"
        "- How many customers are there?\n"
        "- Which 3 products generated the most profit?\n"
        "- Which 3 products generated the least profit?\n"
        "- Which 5 products have the highest revenue?\n"
        "- Which 3 products generated the least profit in South?\n"
        "- What is the profit in South?\n"
        "- What is the profit of Laptop?\n"
        "- What is the revenue of Headphones?\n"
        "- What is the most selling product?\n"
        "- What is the least selling product?\n"
        "- Show revenue by region\n"
        "- Show profit by region\n"
        "- Show revenue by product\n"
        "- Show profit by product\n"
        "- Show revenue by payment method\n"
        "- How many users use each payment method?\n"
        "- What percentage of revenue comes from each payment method?\n"
        "- What is monthly revenue?\n"
        "- What is monthly profit?\n"
        "- What is each month's contribution percentage?\n"
        "- Products with revenue above 1000000\n"
        "- Products with profit below 50000\n"
        "- Products with quantity above 300\n"
    )


# ============================================================
# PROFESSIONAL UI STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       MAIN APPLICATION
       ====================================================== */

    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }


    /* ======================================================
       HERO
       ====================================================== */

    .hero-box {
        background: linear-gradient(
            135deg,
            #111827 0%,
            #1e3a8a 50%,
            #2563eb 100%
        );

        padding: 35px 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.12);
    }

    .hero-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .hero-subtitle {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .hero-text {
        font-size: 16px;
        opacity: 0.9;
    }


    /* ======================================================
       SECTION HEADERS
       ====================================================== */

    .section-title {
        font-size: 26px;
        font-weight: 750;
        color: #111827;
        margin-top: 25px;
        margin-bottom: 15px;
    }


    /* ======================================================
       KPI CARDS
       ====================================================== */

    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 5px 18px rgba(0,0,0,0.06);
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #6b7280;
    }

    div[data-testid="stMetricValue"] {
        font-weight: 800;
        color: #111827;
    }


    /* ======================================================
       DATAFRAME
       ====================================================== */

    div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 5px 18px rgba(0,0,0,0.05);
    }


    /* ======================================================
       BUTTONS
       ====================================================== */

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: none;
        padding: 10px 18px;
    }


    /* ======================================================
       TEXT INPUT
       ====================================================== */

    div[data-baseweb="input"] {
        border-radius: 12px;
    }


    /* ======================================================
       FILE UPLOADER
       ====================================================== */

    section[data-testid="stFileUploader"] {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border: 1px dashed #9ca3af;
    }


    /* ======================================================
       ALERT BOXES
       ====================================================== */

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }


    /* ======================================================
       AI ANSWER
       ====================================================== */

    .ai-answer {
        background-color: white;
        border-left: 5px solid #2563eb;
        padding: 22px;
        border-radius: 14px;
        margin-top: 15px;
        box-shadow: 0 5px 18px rgba(0,0,0,0.06);
    }


    /* ======================================================
       INSIGHT CARD
       ====================================================== */

    .insight-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }
        /* ==============================
       MODERN DASHBOARD
       ============================== */

    .dashboard-header {
        background: linear-gradient(
            135deg,
            #0f172a,
            #1d4ed8,
            #2563eb
        );
        padding: 32px;
        border-radius: 22px;
        margin-bottom: 25px;
        color: white;
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.20);
    }

    .dashboard-title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .dashboard-subtitle {
        font-size: 16px;
        opacity: 0.85;
    }

    .kpi-card {
        background: white;
        padding: 22px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
        min-height: 125px;
    }

    .kpi-icon {
        font-size: 25px;
        margin-bottom: 8px;
    }

    .kpi-label {
        color: #64748b;
        font-size: 14px;
        font-weight: 600;
    }

    .kpi-value {
        color: #0f172a;
        font-size: 28px;
        font-weight: 800;
        margin-top: 5px;
    }

    .kpi-description {
        color: #94a3b8;
        font-size: 12px;
        margin-top: 5px;
    }

    .dashboard-section {
        background: white;
        padding: 22px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 7px 20px rgba(15, 23, 42, 0.05);
        margin-top: 20px;
    }

    .section-heading {
        font-size: 21px;
        font-weight: 750;
        color: #0f172a;
        margin-bottom: 5px;
    }

    .section-description {
        font-size: 13px;
        color: #64748b;
        margin-bottom: 15px;
    }

    .highlight-card {
        background: linear-gradient(
            135deg,
            #eff6ff,
            #ffffff
        );
        border: 1px solid #dbeafe;
        padding: 20px;
        border-radius: 16px;
        min-height: 120px;
    }

    .highlight-title {
        font-size: 14px;
        color: #64748b;
        font-weight: 600;
    }

    .highlight-value {
        font-size: 23px;
        font-weight: 800;
        color: #1d4ed8;
        margin-top: 8px;
    }

    .highlight-text {
        font-size: 12px;
        color: #64748b;
        margin-top: 5px;
    }

    .status-badge {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:15px;
            ">

        <div style="
            font-size:45px;
            margin-bottom:10px;
        ">
                🤖
        </div>

        <div style="
            font-size:22px;
            font-weight:700;
        ">
            AI Data Analyst
        </div>

        <div style="
            color:#d1d5db;
            font-size:14px;
            margin-top:8px;
        ">
            Business Intelligence<br>
            powered by Natural Language
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### 🧭 Navigation")

    st.markdown(
        """
        📊 **Dashboard**

        💡 **Business Insights**

        🤖 **Ask Data Analyst**

        📈 **Product Analysis**

        🌍 **Regional Analysis**

        💳 **Payment Analysis**

        📅 **Monthly Trends**
        """
    )

    st.divider()

    st.markdown("### ⚡ Engine")

    st.success(
        "LOCAL ANALYTICS ENGINE"
    )

    st.caption(
        "No API credits required"
    )

    st.caption(
        "Powered by Python + Pandas"
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero-box">

    <div class="hero-title">
            🤖 AI Data Analyst Agent
    </div>

    <div class="hero-subtitle">
        Natural Language Business Intelligence Platform
    </div>

    <div class="hero-text">
        Ask questions. Discover insights.
        Make data-driven decisions.
    </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FILE UPLOAD
# ============================================================

st.markdown(
    '<div class="section-title">📂 Upload Your Dataset</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx"],
    help="Supported formats: CSV and XLSX"
)


# ============================================================
# MAIN APPLICATION
# ============================================================

if uploaded_file is None:

    st.info(
        "👆 Upload a CSV or Excel dataset to start analyzing your data."
    )

else:

    # ========================================================
    # LOAD DATA
    # ========================================================

    try:

        if uploaded_file.name.lower().endswith(".csv"):

            df = pd.read_csv(
                uploaded_file
            )

        else:

            df = pd.read_excel(
                uploaded_file
            )

    except Exception as e:

        st.error(
            f"❌ Could not read the uploaded file: {e}"
        )

        st.stop()


    # ========================================================
    # CLEAN COLUMN NAMES
    # ========================================================

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]


    # ========================================================
    # SUCCESS MESSAGE
    # ========================================================

    st.success(
        f"✅ File uploaded successfully: "
        f"{uploaded_file.name}"
    )


    # ========================================================
    # CHECK REQUIRED COLUMNS
    # ========================================================

    recommended_columns = [
        "Revenue",
        "Profit",
        "Product",
        "Region",
        "Quantity",
        "Customer_ID",
        "Payment_Method"
    ]

    missing_recommended = [
        column
        for column in recommended_columns
        if column not in df.columns
    ]

    if missing_recommended:

        st.warning(
            "⚠️ Some recommended columns are missing: "
            + ", ".join(missing_recommended)
        )

        st.caption(
            "The application will still analyze the "
            "columns that are available."
        )


    # ========================================================
    # AUTOMATIC DATE DETECTION
    # ========================================================

    date_columns = []

    # --------------------------------------------------------
    # Prefer Order_Date when available
    # --------------------------------------------------------

    if "Order_Date" in df.columns:

        converted = pd.to_datetime(
            df["Order_Date"],
            errors="coerce",
            format="mixed"
        )

        valid_ratio = converted.notna().mean()

        if valid_ratio >= 0.8:
            df["Order_Date"] = converted
            date_columns.append("Order_Date")


    # --------------------------------------------------------
    # Detect other genuine date/time columns
    # --------------------------------------------------------

    for column in df.columns:

        if column == "Order_Date":
            continue

        # Never convert numeric columns such as Year to dates
        if pd.api.types.is_numeric_dtype(df[column]):
            continue

        column_name = str(column).lower()

        looks_like_date = any(
            word in column_name
            for word in [
                "date",
                "time",
                "day",
                "month"
            ]
        )

        if looks_like_date:

            converted = pd.to_datetime(
                df[column],
                errors="coerce",
                format="mixed"
            )

            valid_ratio = converted.notna().mean()

            if valid_ratio >= 0.8:

                df[column] = converted
                date_columns.append(column)


    # --------------------------------------------------------
    # Keep Order_Date as the preferred date column
    # --------------------------------------------------------

    if "Order_Date" in date_columns:

        date_columns.insert(
            0,
            date_columns.pop(
                date_columns.index("Order_Date")
            )
        )


    # ========================================================
    # DATASET PREVIEW
    # ========================================================

    st.markdown(
        '<div class="section-title">📋 Dataset Preview</div>',
        unsafe_allow_html=True
    )

    st.dataframe(
        df.head(10),
        use_container_width=True
    )


    # ========================================================
    # BUSINESS PERFORMANCE
    # ========================================================

    st.markdown(
        '<div class="section-title">💼 Business Performance</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    if "Revenue" in df.columns:

        total_revenue = (
            pd.to_numeric(
                df["Revenue"],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

    else:

        total_revenue = 0


    # --------------------------------------------------------
    # Profit
    # --------------------------------------------------------

    if "Profit" in df.columns:

        total_profit = (
            pd.to_numeric(
                df["Profit"],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

    else:

        total_profit = 0


    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    if "Order_ID" in df.columns:

        total_orders = (
            df["Order_ID"]
            .nunique()
        )

    else:

        total_orders = len(df)


    # --------------------------------------------------------
    # Customers
    # --------------------------------------------------------

    if "Customer_ID" in df.columns:

        total_customers = (
            df["Customer_ID"]
            .nunique()
        )

    else:

        total_customers = 0


    # --------------------------------------------------------
    # AOV
    # --------------------------------------------------------

    average_order_value = (
        total_revenue / total_orders
        if total_orders
        else 0
    )


    # --------------------------------------------------------
    # Profit Margin
    # --------------------------------------------------------

    profit_margin = (
        total_profit / total_revenue * 100
        if total_revenue
        else 0
    )


    # ======================================
    # ATTRACTIVE BUSINESS DASHBOARD
    # ======================================

    st.markdown(
        """<div class="dashboard-header">
<div class="dashboard-title">
📊 Business Intelligence Dashboard
</div>

<div class="dashboard-subtitle">
Real-time overview of your sales, customers,
profitability and business performance
</div>
</div>""",
        unsafe_allow_html=True
    )


    # ======================================
    # CALCULATE KPIs
    # ======================================

    total_revenue = (
        df["Revenue"].sum()
        if "Revenue" in df.columns
        else 0
    )

    total_profit = (
        df["Profit"].sum()
        if "Profit" in df.columns
        else 0
    )

    total_orders = len(df)

    total_customers = (
        df["Customer_ID"].nunique()
        if "Customer_ID" in df.columns
        else 0
    )

    average_order_value = (
        total_revenue / total_orders
        if total_orders > 0
        else 0
    )

    profit_margin = (
        total_profit / total_revenue * 100
        if total_revenue != 0
        else 0
    )


# ======================================
# KPI CARDS
# ======================================

    st.markdown(
        '<div class="section-heading">💼 Key Performance Indicators</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'A quick snapshot of your business performance.'
        '</div>',
        unsafe_allow_html=True
    )


    kpi1, kpi2, kpi3 = st.columns(3)


    with kpi1:

        st.markdown(
            f"""<div class="kpi-card">

<div class="kpi-icon">💰</div>

<div class="kpi-label">
TOTAL REVENUE
</div>

<div class="kpi-value">
₹{total_revenue:,.0f}
</div>

<div class="kpi-description">
Total sales generated
</div>

</div>""",
            unsafe_allow_html=True
        )

    with kpi2:

        st.markdown(
            f"""<div class="kpi-card">

<div class="kpi-icon">📈</div>

<div class="kpi-label">
TOTAL PROFIT
</div>

<div class="kpi-value">
₹{total_profit:,.0f}
</div>

<div class="kpi-description">
Overall business profit
</div>

</div>""",
            unsafe_allow_html=True
        )


    with kpi3:

        st.markdown(
            f"""<div class="kpi-card">

<div class="kpi-icon">📊</div>

<div class="kpi-label">
PROFIT MARGIN
</div>

<div class="kpi-value">
{profit_margin:.2f}%
</div>

<div class="kpi-description">
Profit as % of revenue
</div>

</div>""",
            unsafe_allow_html=True
        )


    st.write("")


    kpi4, kpi5, kpi6 = st.columns(3)


    with kpi4:

        st.markdown(
            f"""<div class="kpi-card">

<div class="kpi-icon">🛒</div>

<div class="kpi-label">
TOTAL ORDERS
</div>

<div class="kpi-value">
{total_orders:,}
</div>

<div class="kpi-description">
Orders processed
</div>

</div>""",
            unsafe_allow_html=True
        )


    with kpi5:

        st.markdown(
            f"""<div class="kpi-card">

<div class="kpi-icon">👥</div>

<div class="kpi-label">
CUSTOMERS
</div>

<div class="kpi-value">
{total_customers:,}
</div>

<div class="kpi-description">
Unique customers
</div>

</div>""",
            unsafe_allow_html=True
        )


    with kpi6:

        st.markdown(
            f"""<div class="kpi-card">

<div class="kpi-icon">💵</div>

<div class="kpi-label">
AVERAGE ORDER VALUE
</div>

<div class="kpi-value">
₹{average_order_value:,.0f}
</div>

<div class="kpi-description">
Average revenue per order
</div>

</div>""",
            unsafe_allow_html=True
        )


    # ======================================
    # BUSINESS HIGHLIGHTS
    # ======================================

    st.markdown(
        """<div class="dashboard-section">

<div class="section-heading">
✨ Business Highlights
</div>

<div class="section-description">
Automatically generated insights from your dataset.
</div>

</div>""",
        unsafe_allow_html=True
    )


    highlight1, highlight2, highlight3, highlight4 = st.columns(4)


    # --------------------------------------
    # BEST PRODUCT
    # --------------------------------------

    if "Product" in df.columns and "Revenue" in df.columns:

        product_revenue = (
            df.groupby("Product")["Revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        best_product = product_revenue.index[0]
        best_product_revenue = product_revenue.iloc[0]

    else:

        best_product = "N/A"
        best_product_revenue = 0


    with highlight1:

        st.markdown(
            f"""<div class="highlight-card">
<div class="highlight-title">
🏆 TOP PRODUCT
</div>

<div class="highlight-value">
{best_product}
</div>
<div class="highlight-text">
Revenue: ₹{best_product_revenue:,.0f}
</div>
</div>""",
            unsafe_allow_html=True
        )


    # --------------------------------------
    # BEST REGION
    # --------------------------------------

    if "Region" in df.columns and "Revenue" in df.columns:

        region_revenue = (
            df.groupby("Region")["Revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        best_region = region_revenue.index[0]
        best_region_revenue = region_revenue.iloc[0]

    else:

        best_region = "N/A"
        best_region_revenue = 0


    with highlight2:

        st.markdown(
            f"""<div class="highlight-card">

<div class="highlight-title">
🌍 TOP REGION
</div>
<div class="highlight-value">
{best_region}
</div>

<div class="highlight-text">
Revenue: ₹{best_region_revenue:,.0f}
</div>

</div>""",
            unsafe_allow_html=True
        )


    # --------------------------------------
    # MOST SOLD PRODUCT
    # --------------------------------------

    if "Product" in df.columns and "Quantity" in df.columns:

        product_quantity = (
            df.groupby("Product")["Quantity"]
            .sum()
            .sort_values(ascending=False)
        )

        most_selling_product = product_quantity.index[0]
        most_selling_quantity = product_quantity.iloc[0]

    else:

        most_selling_product = "N/A"
        most_selling_quantity = 0


    with highlight3:

        st.markdown(
            f"""<div class="highlight-card">
<div class="highlight-title">
📦 MOST SOLD
</div>

<div class="highlight-value">
{most_selling_product}
</div>

<div class="highlight-text">
{most_selling_quantity:,.0f} units sold
</div>

</div>""",
            unsafe_allow_html=True
        )


    # --------------------------------------
    # PAYMENT METHOD
    # --------------------------------------

    if (
        "Payment_Method" in df.columns
        and "Revenue" in df.columns
    ):

        payment_revenue = (
            df.groupby("Payment_Method")["Revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        best_payment = payment_revenue.index[0]
        best_payment_revenue = payment_revenue.iloc[0]

    else:

        best_payment = "N/A"
        best_payment_revenue = 0


    with highlight4:

        st.markdown(
            f"""<div class="highlight-card">

<div class="highlight-title">
💳 TOP PAYMENT
</div>

<div class="highlight-value">
{best_payment}
</div>

<div class="highlight-text">
Revenue: ₹{best_payment_revenue:,.0f}
</div>

</div>""",
            unsafe_allow_html=True
        )


    # ======================================
    # CHART SECTION
    # ======================================

    st.markdown(
        """<div class="dashboard-section">

<div class="section-heading">
📈 Sales Performance
</div>

<div class="section-description">
Track revenue and profitability across your business.
</div>

</div>""",
        unsafe_allow_html=True
    )


    chart1, chart2 = st.columns(2)


    # ======================================
    # MONTHLY REVENUE
    # ======================================

    with chart1:

        st.subheader("📅 Revenue Trend")

        if (
            "Revenue" in df.columns
            and date_columns
        ):

            date_column = date_columns[0]

            monthly_revenue = (
                df
                .set_index(date_column)
                .resample("ME")["Revenue"]
                .sum()
            )

            if not monthly_revenue.empty:

                st.area_chart(
                    monthly_revenue,
                    use_container_width=True
                )

            else:

                st.info(
                    "Not enough date information for a trend."
                )

        else:

            st.info(
                "No date column available."
            )


    # ======================================
    # PROFIT BY PRODUCT
    # ======================================

    with chart2:

        st.subheader("📈 Profit by Product")

        if (
            "Product" in df.columns
            and "Profit" in df.columns
        ):

            product_profit_dashboard = (
                df.groupby("Product")["Profit"]
                .sum()
                .sort_values(ascending=False)
            )

            st.bar_chart(
                product_profit_dashboard,
                use_container_width=True
            )

        else:

            st.info(
                "Product or Profit column not available."
            )


    # ======================================
    # REGIONAL + PAYMENT ANALYSIS
    # ======================================

    st.markdown(
        """<div class="dashboard-section">

<div class="section-heading">
🌍 Sales Distribution
</div>
<div class="section-description">
Understand where your revenue is coming from.
</div>

</div>""",
        unsafe_allow_html=True
    )


    chart3, chart4 = st.columns(2)


    # ======================================
    # REGION REVENUE
    # ======================================

    with chart3:

        st.subheader("🌍 Revenue by Region")

        if (
            "Region" in df.columns
            and "Revenue" in df.columns
        ):

            dashboard_region_revenue = (
                df.groupby("Region")["Revenue"]
                .sum()
                .sort_values(ascending=False)
            )

            st.bar_chart(
                dashboard_region_revenue,
                use_container_width=True
            )

        else:

            st.info(
                "Region or Revenue column not available."
            )


    # ======================================
    # PAYMENT REVENUE
    # ======================================

    with chart4:

        st.subheader("💳 Revenue by Payment Method")

        if (
            "Payment_Method" in df.columns
            and "Revenue" in df.columns
        ):

            dashboard_payment_revenue = (
                df.groupby("Payment_Method")["Revenue"]
                .sum()
                .sort_values(ascending=False)
            )

            st.bar_chart(
                dashboard_payment_revenue,
                use_container_width=True
            )

        else:

            st.info(
                "Payment method data not available."
            )


    # ======================================
    # PERFORMANCE TABLE
    # ======================================

    st.markdown(
        """<div class="dashboard-section">
<div class="section-heading">
🏆 Product Performance Ranking
</div>

<div class="section-description">
Products ranked by revenue and profit.
</div>

</div>""",
        unsafe_allow_html=True
    )


    if (
        "Product" in df.columns
        and "Revenue" in df.columns
        and "Profit" in df.columns
    ):

        performance = (
            df.groupby("Product")
            .agg(
                Revenue=("Revenue", "sum"),
                Profit=("Profit", "sum"),
                Units_Sold=("Quantity", "sum")
                if "Quantity" in df.columns
                else ("Revenue", "count")
            )
            .sort_values(
                "Revenue",
                ascending=False
            )
            .reset_index()
        )

        performance["Profit Margin"] = (
            performance["Profit"]
            / performance["Revenue"]
            * 100
        ).round(2)

        performance["Revenue"] = (
            performance["Revenue"]
            .map(lambda x: f"₹{x:,.0f}")
        )

        performance["Profit"] = (
            performance["Profit"]
            .map(lambda x: f"₹{x:,.0f}")
        )

        performance["Profit Margin"] = (
            performance["Profit Margin"]
            .map(lambda x: f"{x:.2f}%")
        )

        st.dataframe(
            performance,
            use_container_width=True,
            hide_index=True
        )


    # ======================================
    # DASHBOARD FOOTER
    # ======================================

    st.markdown(
        """<div class="footer">
<div class="footer-title">
<b>© AI Data Analyst Agent</b>
</div>

<div class="footer-text">
Powered by Python + Pandas
</div>

<div class="footer-text">
Local Analytics Engine
</div>
</div>""",
        unsafe_allow_html=True
    )

    # =====================================================
    # DATASET OVERVIEW
    # =====================================================
    
    st.markdown(
        '<div class="section-title">📊 Dataset Overview</div>',
        unsafe_allow_html=True
    )
    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Rows",
            df.shape[0]
        )

    with col2:

        st.metric(
            "Columns",
            df.shape[1]
        )

    with col3:

        st.metric(
            "Duplicate Rows",
            df.duplicated().sum()
        )

    with col4:

        st.metric(
            "Missing Values",
            int(
                df.isna()
                .sum()
                .sum()
            )
        )


    # ========================================================
    # DETECTED DATE COLUMNS
    # ========================================================

    st.markdown(
        '<div class="section-title">📅 Detected Date Columns</div>',
        unsafe_allow_html=True
    )

    if date_columns:

        for column in date_columns:

            st.write(
                f"✅ **{column}**"
            )

    else:

        st.info(
            "No date columns detected."
        )


    # ========================================================
    # DATA TYPES
    # ========================================================

    st.markdown(
        '<div class="section-title">🔤 Data Types</div>',
        unsafe_allow_html=True
    )

    dtype_df = pd.DataFrame(
        {
            "Column": df.columns,
            "Data Type": [
                str(dtype)
                for dtype in df.dtypes
            ]
        }
    )

    st.dataframe(
        dtype_df,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # MISSING VALUES
    # ========================================================

    st.markdown(
        '<div class="section-title">⚠️ Missing Values</div>',
        unsafe_allow_html=True
    )

    missing_df = pd.DataFrame(
        {
            "Column": df.columns,
            "Missing Values": (
                df.isna()
                .sum()
                .values
            )
        }
    )

    if len(df) > 0:

        missing_df["Missing %"] = (
            missing_df["Missing Values"]
            / len(df)
            * 100
        ).round(2)

    else:

        missing_df["Missing %"] = 0

    st.dataframe(
        missing_df,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # NUMERICAL STATISTICS
    # ========================================================

    st.markdown(
        '<div class="section-title">📈 Numerical Statistics</div>',
        unsafe_allow_html=True
    )

    numeric_df = df.select_dtypes(
        include="number"
    )

    if not numeric_df.empty:

        st.dataframe(
            numeric_df.describe().T,
            use_container_width=True
        )

    else:

        st.info(
            "No numerical columns found."
        )


    # ========================================================
    # CATEGORICAL COLUMNS
    # ========================================================

    st.markdown(
        '<div class="section-title">🏷️ Categorical Columns</div>',
        unsafe_allow_html=True
    )

    categorical_columns = (
        df.select_dtypes(
            include="object"
        ).columns
    )

    if len(categorical_columns) > 0:

        for column in categorical_columns:

            with st.expander(
                f"📌 {column}"
            ):

                st.dataframe(
                    df[column]
                    .value_counts()
                    .head(10),
                    use_container_width=True
                )

    else:

        st.info(
            "No categorical columns found."
        )


    # ========================================================
    # MONTHLY REVENUE
    # ========================================================

    if (
        "Revenue" in df.columns
        and date_columns
    ):

        date_column = date_columns[0]

        st.markdown(
            '<div class="section-title">💰 Monthly Revenue Trend</div>',
            unsafe_allow_html=True
        )

        temp = df.dropna(
            subset=[date_column]
        ).copy()

        monthly_revenue = (
            temp
            .set_index(date_column)["Revenue"]
            .resample("ME")
            .sum()
        )

        if not monthly_revenue.empty:

            st.line_chart(
                monthly_revenue
            )

        else:

            st.info(
                "Not enough valid date data "
                "for the monthly revenue chart."
            )


    # ========================================================
    # PRODUCT ANALYSIS
    # ========================================================

    if (
        "Product" in df.columns
        and "Revenue" in df.columns
    ):

        st.markdown(
            '<div class="section-title">🛍️ Product Performance</div>',
            unsafe_allow_html=True
        )

        product_revenue = (
            df
            .groupby("Product")["Revenue"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.subheader(
            "💰 Revenue by Product"
        )

        st.bar_chart(
            product_revenue
        )


    # ========================================================
    # PRODUCT PROFIT
    # ========================================================

    if (
        "Product" in df.columns
        and "Profit" in df.columns
    ):

        product_profit = (
            df
            .groupby("Product")["Profit"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.subheader(
            "📈 Profit by Product"
        )

        st.bar_chart(
            product_profit
        )


    # ========================================================
    # REGIONAL ANALYSIS
    # ========================================================

    if (
        "Region" in df.columns
        and "Revenue" in df.columns
    ):

        st.markdown(
            '<div class="section-title">🌍 Regional Performance</div>',
            unsafe_allow_html=True
        )

        region_revenue = (
            df
            .groupby("Region")["Revenue"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.subheader(
            "💰 Revenue by Region"
        )

        st.bar_chart(
            region_revenue
        )


    # ========================================================
    # REGIONAL PROFIT
    # ========================================================

    if (
        "Region" in df.columns
        and "Profit" in df.columns
    ):

        region_profit = (
            df
            .groupby("Region")["Profit"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.subheader(
            "📈 Profit by Region"
        )

        st.bar_chart(
            region_profit
        )


    # ========================================================
    # AUTOMATIC BUSINESS INSIGHTS
    # ========================================================

    st.markdown(
        '<div class="section-title">💡 Automatic Business Insights</div>',
        unsafe_allow_html=True
    )

    insights = []


    # ========================================================
    # BEST PRODUCT BY REVENUE
    # ========================================================

    if (
        "Revenue" in df.columns
        and "Product" in df.columns
    ):

        product_revenue = (
            df
            .groupby("Product")["Revenue"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if not product_revenue.empty:

            best_product = (
                product_revenue.index[0]
            )

            best_product_revenue = (
                product_revenue.iloc[0]
            )

            revenue_percentage = (
                best_product_revenue
                / total_revenue
                * 100
                if total_revenue
                else 0
            )

            insights.append(
                f"💰 **{best_product}** generated "
                f"the highest revenue at "
                f"**{format_money(best_product_revenue)}**, "
                f"contributing "
                f" **{revenue_percentage:.2f}%** "
                f"of total revenue."
            )


    # ========================================================
    # BEST PRODUCT BY PROFIT
    # ========================================================

    if (
        "Profit" in df.columns
        and "Product" in df.columns
    ):

        product_profit = (
            df
            .groupby("Product")["Profit"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if not product_profit.empty:

            best_profit_product = (
                product_profit.index[0]
            )

            best_profit = (
                product_profit.iloc[0]
            )

            profit_percentage = (
                best_profit
                / total_profit
                * 100
                if total_profit
                else 0
            )

            insights.append(
                f"📈 **{best_profit_product}** generated "
                f"the highest profit at "
                f"**{format_money(best_profit)}**, "
                f"representing "
                f" **{profit_percentage:.2f}%** "
                f"of total profit."
            )


    # ========================================================
    # BEST REGION
    # ========================================================

    if (
        "Region" in df.columns
        and "Revenue" in df.columns
    ):

        region_revenue = (
            df
            .groupby("Region")["Revenue"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if not region_revenue.empty:

            best_region = (
                region_revenue.index[0]
            )

            best_region_revenue = (
                region_revenue.iloc[0]
            )

            insights.append(
                f"🌍 **{best_region}** is the "
                f"strongest region by revenue "
                f"with **{format_money(best_region_revenue)}**."
            )


            # Lowest region

            worst_region = (
                region_revenue.index[-1]
            )

            worst_region_revenue = (
                region_revenue.iloc[-1]
            )

            insights.append(
                f"📉 **{worst_region}** has the "
                f"lowest revenue at "
                f"**{format_money(worst_region_revenue)}**."
            )


    # ========================================================
    # MOST SELLING PRODUCT
    # ========================================================

    if (
        "Product" in df.columns
        and "Quantity" in df.columns
    ):

        product_quantity = (
            df
            .groupby("Product")["Quantity"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if not product_quantity.empty:

            most_selling = (
                product_quantity.index[0]
            )

            most_selling_quantity = (
                product_quantity.iloc[0]
            )

            insights.append(
                f"🏆 **{most_selling}** is the "
                f"most-selling product with "
                f"**{most_selling_quantity:,.0f} "
                f"units** sold."
            )

            # Least selling

            least_selling = (
                product_quantity.index[-1]
            )

            least_selling_quantity = (
                product_quantity.iloc[-1]
            )

            insights.append(
                f"⚠️ **{least_selling}** is the "
                f"least-selling product with "
                f"**{least_selling_quantity:,.0f} "
                f"units** sold."
            )


    # ========================================================
    # PAYMENT MODE INSIGHT
    # ========================================================

    if (
        "Payment_Method" in df.columns
        and "Revenue" in df.columns
    ):

        payment_revenue = (
            df
            .groupby(
                "Payment_Method"
            )["Revenue"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if not payment_revenue.empty:

            best_payment = (
                payment_revenue.index[0]
            )

            best_payment_revenue = (
                payment_revenue.iloc[0]
            )

            payment_total = (
                payment_revenue.sum()
            )

            payment_percentage = (
                best_payment_revenue
                / payment_total
                * 100
                if payment_total
                else 0
            )

            insights.append(
                f"💳 **{best_payment}** generated "
                f"the most revenue with "
                f"**{format_money(best_payment_revenue)}**, "
                f"accounting for "
                f"**{payment_percentage:.2f}%** "
                f"of payment-mode revenue."
            )

    # ========================================================
    # DISPLAY INSIGHTS
    # ========================================================

    if insights:

        for insight in insights:

            # Insight text is rendered inside an HTML card, where Markdown
            # markers are not interpreted. Escape dataset text first, then
            # convert the app's bold Markdown markers to safe HTML.
            insight_html = re.sub(
                r"\*\*(.+?)\*\*",
                r"<strong>\1</strong>",
                escape(insight)
            )

            st.markdown(
                f"""
                <div class="insight-card">
                    {insight_html}
                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.info(
            "Not enough information available "
            "to generate automatic business insights."
        )

    # ========================================================
    # ASK YOUR DATA ANALYST
    # ========================================================

    st.markdown("**Try asking:**")

    example1, example2, example3, example4 = st.columns(4)


    def set_analyst_question(question_text):
        st.session_state["analyst_question"] = question_text


    with example1:
        st.button(
            "📈 Top products",
            use_container_width=True,
            on_click=set_analyst_question,
            args=("Which 5 products have the highest revenue?",)
        )


    with example2:
        st.button(
            "🌍 Best region",
            use_container_width=True,
            on_click=set_analyst_question,
            args=("Which region has the highest revenue?",)
        )


    with example3:
        st.button(
            "💳 Payment analysis",
            use_container_width=True,
            on_click=set_analyst_question,
            args=("Which payment method generates the most revenue?",)
        )


    with example4:
        st.button(
            "📅 Monthly trends",
            use_container_width=True,
            on_click=set_analyst_question,
            args=("Show monthly revenue",)
        )

    st.caption(
        "Ask questions in natural language — no SQL required."
    )

    # ========================================================
    # QUESTION INPUT
    # ========================================================

    question = st.text_input(
        "What would you like to know?",
        placeholder="💬 e.g. Which 3 products generated the most profit?",
        label_visibility="collapsed",
        key="analyst_question"
    )

    # ========================================================
    # ANALYZE QUESTION
    # ========================================================

    if question.strip():

        with st.spinner("🔎 Analyzing your data..."):

            try:

                answer = local_data_analyst(
                    question,
                    df
                )

                st.markdown(
                    '<div class="ai-answer">',
                    unsafe_allow_html=True
                )

                st.markdown(
                    "### 💡 AI Answer"
                )

                st.markdown(answer)

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

            except Exception as e:

                st.error(
                    f"❌ Analysis failed: {e}"
                )
