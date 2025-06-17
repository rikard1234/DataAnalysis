import pandas as pd
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import pandas as pd
from typing import List, Dict
from datetime import date
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
from dotenv import load_dotenv
from fastapi.openapi.docs import get_swagger_ui_html
import logging
from fastapi_camelcase import CamelModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SalesQuery(CamelModel):
    start_date: date = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: date = Field(..., description="End date in YYYY-MM-DD format")

class DaySalesValue(CamelModel):
    date: date
    income: float

class DaySalesAmount(CamelModel):
    date: date
    amount: float

class TotalSalesResponse(CamelModel):
    total_sales: float 



class AverageSalesResponse(CamelModel):
    percentage_change: float
    total_income: float
    average_daily_income: float
    highest_daily_income: float
    income_per_day: List[DaySalesValue]  

    
class TopUnintsResponse(CamelModel):
    top_product_id: List
    top_quantity: List
    top_percentage: List


class TotalSalesCountResponse(CamelModel):
    count_per_day: List[DaySalesAmount] 


class TopProduct(CamelModel):
    product_id: int
    count: int
    percentage: float

class TopUnitsResponse(CamelModel):
    tops: List[TopProduct]

class DishToppingCount(CamelModel):
    dish_id: int
    topping_id: int
    count: int

class MostFrequentDishToppingResponse(CamelModel):
    dish_topping: DishToppingCount

class ToppingCount(CamelModel):
    topping_id: int
    count: int

class TopToppingsResponse(CamelModel):
    toppings: List[ToppingCount]


load_dotenv(".env.development.deploy")

security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.environ.get("API_USERNAME", "")
    correct_password = os.environ.get("API_PASSWORD", "")
    if not correct_username:
        logger.warning("API_USERNAME not set in environment variables")
    else:
        logger.info(f"API_USERNAME loaded: {correct_username}")

    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


app = FastAPI(dependencies=[Depends(authenticate)])

#
@app.get("/")
def root():
    return {"message": "Welcome to the Data Analysis Service API. Please use the endpoints with proper credentials."}


@app.get("/docs", include_in_schema=False)
async def get_documentation(credentials: HTTPBasicCredentials = Depends(authenticate)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")


@app.get("/restaurants/{restaurantId}/total-sales-value", 
         response_model=TotalSalesResponse, 
         summary="Total sales")
def totalSales(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD")
):
    try:
        logger.info(f"API_USERNAME loaded: {os.environ.get('API_USERNAME', '')}")
        dishes_df = pd.read_csv("data/dishes.csv")

        dishes_df["date"] = pd.to_datetime(dishes_df["date"]).dt.date

        filtered_df = dishes_df[
            (dishes_df["date"] >= start_date) & (dishes_df["date"] <= end_date)
        ]

        total_sales_value = filtered_df["price"].sum()

        return TotalSalesResponse(
            total_sales=round(total_sales_value, 2)
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/restaurants/{restaurantId}/average-sales", 
         response_model=AverageSalesResponse, 
         summary="Average sales",)
def averageSales(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD")
):
    try:
        df = pd.read_csv("data/dishes.csv")
        df["date"] = pd.to_datetime(df["date"]).dt.date

        filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        daily_sales = (
            filtered_df.groupby("date")["price"].sum().reset_index(name="income")
        )

        total_income = daily_sales["income"].sum()
        average_daily_income = daily_sales["income"].mean()
        highest_daily_income = daily_sales["income"].max()

        percentage_change = 0.0

        return AverageSalesResponse(
            percentageChange=round(percentage_change, 2),
            totalIncome=round(total_income, 2),
            averageDailyIncome=round(average_daily_income, 2),
            highestDailyIncome=round(highest_daily_income, 2),
            incomePerDay=[
                DaySalesValue(date=row["date"], income=round(row["income"], 2))
                for _, row in daily_sales.iterrows()
            ]
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/restaurants/{restaurantId}/top-by-units", 
         response_model=TopUnitsResponse, 
         summary = "Top by units")
def topByUnits(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD")
):
    try:
        df = pd.read_csv("data/dishes.csv")
        df["date"] = pd.to_datetime(df["date"]).dt.date

        filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        total_sales = len(filtered_df)

        top_products_df = (
            filtered_df.groupby("dish_id")
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
            .head(3)
        )

        top_products_df["percentage"] = round(100 * top_products_df["count"] / total_sales, 2)

        top_products_list = [
            TopProduct(
                product_id=int(row["dish_id"]),
                count=int(row["count"]),
                percentage=float(row["percentage"])
            )
            for _, row in top_products_df.iterrows()
        ]

        return TopUnitsResponse(tops=top_products_list)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@app.get("/restaurants/{restaurantId}/total-sales-count", 
         response_model = TotalSalesCountResponse, 
         summary = "Total sales count")
def totalSalesCount(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD")
    ):

    try:
        df = pd.read_csv("data/dishes.csv")
        df["date"] = pd.to_datetime(df["date"]).dt.date

        filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        daily_amount = (
            filtered_df.groupby("date")["price"].count().reset_index(name="amount")
        )
        return TotalSalesCountResponse(
            count_per_day=[
                DaySalesAmount(date=row["date"], amount=round(row["amount"], 2))
                for _, row in daily_amount.iterrows()
            ]
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

    
@app.get("/restaurants/{restaurantId}/most-frequent-dish-topping", 
         response_model = MostFrequentDishToppingResponse, 
         summary = "Most frequent dish topping combo")
def mostFrequentDishTopping(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD")
    ):
    try:
        dishes_df = pd.read_csv("data/dishes.csv")  
        toppings_df = pd.read_csv("data/dishes_toppings.csv")  

        dishes_df["date"] = pd.to_datetime(dishes_df["date"]).dt.date

        merged_df = toppings_df.merge(
            dishes_df[["order_item_id", "dish_id", "date"]],
            on="order_item_id",
            how="left"
        )

        filtered_df = merged_df[
            (merged_df["date"] >= start_date) & (merged_df["date"] <= end_date)
        ]

        combo_counts = (
            filtered_df.groupby(['dish_id', 'topping_id'])
            .size()
            .reset_index(name='count')
        )
        
        most_frequent_row = combo_counts.loc[combo_counts['count'].idxmax()]

        result = DishToppingCount(
            dish_id=int(most_frequent_row['dish_id']),
            topping_id=int(most_frequent_row['topping_id']),
            count=int(most_frequent_row['count'])
        )

        return MostFrequentDishToppingResponse(dish_topping=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/restaurants/{restaurantId}/top-toppings", 
         response_model = TopToppingsResponse, 
         summary = "Top toppings")
def topToppings(
    start_date: date = Query(None, description="Start date in YYYY-MM-DD"),
    end_date: date = Query(None, description="End date in YYYY-MM-DD"),
    limit: int = Query(3, description="Number of top toppings to return")
):
    try:
        order_items_df = pd.read_csv("data/dishes.csv") 
        toppings_df = pd.read_csv("data/dishes_toppings.csv") 

        order_items_df["date"] = pd.to_datetime(order_items_df["date"]).dt.date

        merged_df = toppings_df.merge(order_items_df[["order_item_id", "date"]], on="order_item_id", how="left")

        if start_date and end_date:
            filtered_df = merged_df[(merged_df["date"] >= start_date) & (merged_df["date"] <= end_date)]
        else:
            filtered_df = merged_df

        topping_counts = filtered_df['topping_id'].value_counts().head(limit)

        toppings_list = [
            ToppingCount(topping_id=int(tid), count=int(cnt))
            for tid, cnt in topping_counts.items()
        ]

        return TopToppingsResponse(toppings=toppings_list)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
