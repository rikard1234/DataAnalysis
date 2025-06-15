import pandas as pd
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import pandas as pd
from typing import List, Dict
from datetime import date

app = FastAPI()

class SalesQuery(BaseModel):
    start_date: date = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: date = Field(..., description="End date in YYYY-MM-DD format")

class DaySales(BaseModel):
    date: date
    sum_price_price: float

class TotalSalesResponse(BaseModel):
    sum_per_day: List[DaySales]
    total_sales: float

class AverageSalesResponse(BaseModel):
    percentage_change: float
    total_income: float
    average_daily_income: float
    highest_daily_income: float
    income_per_day: List[Dict[str, float]]




dishes_df = pd.read_csv("data/dishes.csv")
dishes_categories_df = pd.read_csv("data/dish_categories.csv")
dishes_toppings_df = pd.read_csv("data/dishes_toppings.csv")
dishes_menu_types = pd.read_csv("data/dishes_menu_types.csv")

dishes_lookup_categories_df = pd.read_csv("data/lookup_categories.csv")
dishes_lookup_categories_df = pd.read_csv("data/lookup_sizes.csv")
dishes_lookup_categories_df = pd.read_csv("data/lookup_toppings.csv")

dishes_df_aggregated = dishes_df.groupby(["dish_id", "menu_number"]).agg(
    sum_price=("price", "sum"),
    date=("date", "max")
)


@app.get("/total_sales", response_model=TotalSalesResponse)
def total_sales(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD")
):
    try:
        # Load CSV
        dishes_df = pd.read_csv("data/dishes.csv")

        dishes_df["date"] = pd.to_datetime(dishes_df["date"]).dt.date

        filtered_df = dishes_df[
            (dishes_df["date"] > start_date) & (dishes_df["date"] < end_date)
        ]
        sum_per_day_df = (
            filtered_df.groupby("date", as_index=False)
            .agg(sum_price_price=("price", "sum"))
        )

        total_sales_value = filtered_df["price"].sum()

        return TotalSalesResponse(
            sum_per_day=sum_per_day_df.to_dict(orient="records"),
            total_sales=round(total_sales_value, 2)
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/average", response_model=AverageSalesResponse)
def average_sales(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD")
):
    try:
        df = pd.read_csv("data/dishes.csv")
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Filter by user-provided date range
        filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        # Group by date
        daily_sales = (
            filtered_df.groupby("date")["price"].sum().reset_index(name="income")
        )

        total_income = daily_sales["income"].sum()
        average_daily_income = daily_sales["income"].mean()
        highest_daily_income = daily_sales["income"].max()

        # Dummy percentage change (in real life, you'd compare to previous period)
        percentage_change = 0.0

        return AverageSalesResponse(
            percentage_change=round(percentage_change, 2),
            total_income=round(total_income, 2),
            average_daily_income=round(average_daily_income, 2),
            highest_daily_income=round(highest_daily_income, 2),
            income_per_day=[
                {"date": row["date"].isoformat(), "income": round(row["income"], 2)}
                for _, row in daily_sales.iterrows()
            ]
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    



@app.get("/most_frequent_dish_topping", response_model=MostFrequentDishToppingResponse)
def most_frequent_dish_topping():
    try:
        df = pd.read_csv("data/dishes.csv")

        # Count frequency of each (dish_id, topping_id) pair
        combo_counts = df.groupby(['dish_id', 'topping_id']).size().reset_index(name='count')

        # Find the pair with max count
        most_frequent_row = combo_counts.loc[combo_counts['count'].idxmax()]

        result = DishToppingCount(
            dish_id=int(most_frequent_row['dish_id']),
            topping_id=int(most_frequent_row['topping_id']),
            count=int(most_frequent_row['count']),
        )

        return MostFrequentDishToppingResponse(dish_topping=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/top_toppings", response_model=TopToppingsResponse)
def top_toppings(limit: int = Query(3, description="Number of top toppings to return")):
    try:
        df = pd.read_csv("data/dishes.csv")

        topping_counts = df['topping_id'].value_counts().head(limit)

        toppings_list = [
            ToppingCount(topping_id=int(tid), count=int(cnt))
            for tid, cnt in topping_counts.items()
        ]

        return TopToppingsResponse(toppings=toppings_list)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
