import sqlite3
import pandas as pd
import logging

logging.basicConfig(
    filename="logs/Vendor_Sales_Summary.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)   
def ingest_db(df, table_name, conn):
    df.to_sql(
        name=table_name,
        con=conn,
        if_exists="replace",
        index=False
    )

    logging.info(f"{table_name} table successfully saved into the database.")

    

def create_vendor_summary(conn):
    Vendor_Sales_Summary = pd.read_sql_query("""WITH FreightSummary AS(
select 
VendorNumber , SUM(Freight) as FreightCost
from vendor_invoice
group BY VendorNumber
),

PurchaseSummary AS (
SELECT
p.VendorNumber,
p.VendorName,
p.Brand,
p.Description,
p.PurchasePrice,
pp.Volume,
pp.Price as ActualPrice,
sum(p.Quantity) as TotalPurchasesQuantity,
sum(p.Dollars) as TotalPurchasesDollars
from purchases p
join purchase_prices pp
on p.Brand = pp.Brand
where p.purchaseprice > 0
group by p.VendorNumber,p.VendorName,p.Brand ,p.Description,p.PurchasePrice,pp.Price,pp.Volume
),

SalesSummary AS (
select 
VendorNo,
Brand,
sum(SalesQuantity) as TotalSalesQuantity,
sum(SalesDollars) as TotalSalesDollars,
sum(SalesPrice) as TotalSalesPrice,
sum(ExciseTax) as TotalExciseTax
from sales
group by VendorNO, Brand 
)

Select 
ps.VendorNumber,
ps.VendorName,
ps.Brand,
ps.Description,
ps.PurchasePrice,
ps.ActualPrice,
ps.Volume,
ps.TotalPurchasesQuantity,
ps.TotalPurchasesDollars,
ss.TotalSalesQuantity,
ss.TotalSalesDollars,
ss.TotalSalesPrice,
ss.TotalExciseTax,
fs.FreightCost

from PurchaseSummary ps
left join SalesSummary ss
on ps.VendorNumber = ss.VendorNo
and ps.Brand = ss.Brand
left join FreightSummary fs
on ps.VendorNumber = fs.VendorNumber
order by ps.TotalPurchasesDollars desc""",conn)
    return Vendor_Sales_Summary
    
  


def clean_data(df):
    """
    Clean the vendor sales summary dataset
    and create business KPIs.
    """

    # Data Type Conversion
    df['Volume'] = df['Volume'].astype(float)

    # Fill Missing Values
    df.fillna(0, inplace=True)

    # Remove Extra Spaces
    df['VendorName'] = df['VendorName'].str.strip()
    df['Description'] = df['Description'].str.strip()

    # Feature Engineering
    df['GrossProfit'] = (
        df['TotalSalesDollars'] -
        df['TotalPurchasesDollars']
    )

    df['ProfitMargin'] = (
        df['GrossProfit'] /
        df['TotalSalesDollars']
    ) * 100

    df['StockTurnover'] = (
        df['TotalSalesQuantity'] /
        df['TotalPurchasesQuantity']
    )

    df['SalesToPurchasesRatio'] = (
        df['TotalSalesDollars'] /
        df['TotalPurchasesDollars']
    )

    return df



if __name__ == "__main__":

    # Create Database Connection
    conn = sqlite3.connect("inventory.db")

    logging.info("Creating Vendor Sales Summary...")

    summary_df = create_vendor_summary(conn)

    logging.info("Cleaning Vendor Sales Summary...")

    clean_df = clean_data(summary_df)

    logging.info("Saving Data into Database...")

    ingest_db(
        clean_df,
        "vendor_sales_summary",
        conn
    )

    logging.info("Vendor Sales Summary saved successfully.")

    conn.close()

    logging.info("Database connection closed.")