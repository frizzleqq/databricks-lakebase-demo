# Databricks notebook source
# Makes a handful of inserts/updates to the sync_bakehouse copies of
# sales_customers and sales_transactions, so the next TRIGGERED sync has real
# Change Data Feed changes to pick up. sales_franchises is SNAPSHOT mode and
# doesn't need this -- every run already re-copies it in full.

# COMMAND ----------
dbutils.widgets.text("catalog", "lake_dev")
dbutils.widgets.text("schema", "sync_bakehouse")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------
from pyspark.sql import Row

# COMMAND ----------
# Insert a couple of new customers.
customers_tbl = f"{catalog}.{schema}.sales_customers"
existing_max_id = spark.table(customers_tbl).selectExpr("max(customerID) as m").collect()[0]["m"]

new_customers = spark.createDataFrame(
    [
        Row(
            customerID=existing_max_id + 1,
            first_name="Ada",
            last_name="Lovelace",
            email_address="ada.lovelace@example.com",
            phone_number=None,
            address=None,
            city="London",
            state=None,
            country="United Kingdom",
            continent="Europe",
            postal_zip_code=None,
            gender="Female",
        ),
        Row(
            customerID=existing_max_id + 2,
            first_name="Alan",
            last_name="Turing",
            email_address="alan.turing@example.com",
            phone_number=None,
            address=None,
            city="Manchester",
            state=None,
            country="United Kingdom",
            continent="Europe",
            postal_zip_code=None,
            gender="Male",
        ),
    ],
    schema=spark.table(customers_tbl).schema,
)
new_customers.write.mode("append").saveAsTable(customers_tbl)

# Update an existing customer's city, to produce an `update` change too.
spark.sql(f"""
    UPDATE {customers_tbl}
    SET city = 'Updated City'
    WHERE customerID = (SELECT min(customerID) FROM {customers_tbl})
""")

# COMMAND ----------
# Insert a couple of new transactions.
transactions_tbl = f"{catalog}.{schema}.sales_transactions"
existing_max_tx = spark.table(transactions_tbl).selectExpr("max(transactionID) as m").collect()[0]["m"]

new_transactions = spark.createDataFrame(
    [
        Row(
            transactionID=existing_max_tx + 1,
            customerID=existing_max_id + 1,
            franchiseID=1,
            dateTime=None,
            product="Croissant",
            quantity=2,
            unitPrice=3.5,
            totalPrice=7.0,
            paymentMethod="Cash",
            cardNumber=None,
        ),
        Row(
            transactionID=existing_max_tx + 2,
            customerID=existing_max_id + 2,
            franchiseID=1,
            dateTime=None,
            product="Baguette",
            quantity=1,
            unitPrice=2.0,
            totalPrice=2.0,
            paymentMethod="Card",
            cardNumber=None,
        ),
    ],
    schema=spark.table(transactions_tbl).schema,
)
new_transactions.write.mode("append").saveAsTable(transactions_tbl)

# COMMAND ----------
print(f"customers: {spark.table(customers_tbl).count()} rows")
print(f"transactions: {spark.table(transactions_tbl).count()} rows")
