import pandas as pd
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import pandas as pd
from typing import List, Dict
from datetime import date
class SalesQuery(BaseModel):
    start_date: date = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: date = Field(..., description="End date in YYYY-MM-DD format")

class DaySalesValue(BaseModel):
    date: date
    income: float

class DaySalesAmount(BaseModel):
    date: date
    amount: float

class TotalSalesResponse(BaseModel):
    total_sales: float

class AverageSalesResponse(BaseModel):
    percentage_change: float
    total_income: float
    average_daily_income: float
    highest_daily_income: float
    income_per_day: List[DaySalesValue]  

    
class TopUnintsResponse(BaseModel):
    top_product_id: List
    top_quantity: List
    top_percentage: List


class TotalSalesCountResponse(BaseModel):
    count_per_day: List[DaySalesAmount] 


class TopProduct(BaseModel):
    product_id: int
    count: int
    percentage: float

class TopUnitsResponse(BaseModel):
    tops: List[TopProduct]

class DishToppingCount(BaseModel):
    dish_id: int
    topping_id: int
    count: int

class MostFrequentDishToppingResponse(BaseModel):
    dish_topping: DishToppingCount

class ToppingCount(BaseModel):
    topping_id: int
    count: int

class TopToppingsResponse(BaseModel):
    toppings: List[ToppingCount]


def most_frequent_dish_topping():
    try:
        dishes_df = pd.read_csv("data/dishes.csv")  
        toppings_df = pd.read_csv("data/dishes_toppings.csv")  

        dishes_df["date"] = pd.to_datetime(dishes_df["date"]).dt.date

        merged_df = toppings_df.merge(
            dishes_df[["order_item_id", "dish_id", "date"]],
            on="order_item_id",
            how="left"
        )


        combo_counts = (
            merged_df.groupby(['dish_id', 'topping_id'])
            .size()
            .reset_index(name='count')
        )
        print(combo_counts)
        most_frequent_row = combo_counts.loc[combo_counts['count'].idxmax()]
        print(most_frequent_row)
        result = DishToppingCount(
            dish_id=int(most_frequent_row['dish_id']),
            topping_id=int(most_frequent_row['topping_id']),
            count=int(most_frequent_row['count'])
        )

        print(result)

        return MostFrequentDishToppingResponse(dish_topping=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    


most_frequent_dish_topping()