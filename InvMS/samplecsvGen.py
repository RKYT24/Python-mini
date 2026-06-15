import csv
import random
from datetime import datetime, timedelta

categories = [
    "Electronics", "Furniture", "Stationery", "Tools",
    "Food", "Medical", "Clothing", "Automotive"
]

suppliers = [
    "TechSource", "FurniCo", "PaperPlus", "BuildPro",
    "HealthSupply", "SafeWear", "AutoParts Ltd",
    "Global Traders"
]

warehouses = [
    "Warehouse-A", "Warehouse-B", "Warehouse-C",
    "Warehouse-D", "Warehouse-E"
]

statuses = ["Active", "Low Stock", "Out of Stock"]

products = [
    "Wireless Mouse", "Mechanical Keyboard", "Monitor",
    "Office Chair", "Notebook", "Hammer",
    "Safety Gloves", "Coffee Beans", "First Aid Kit",
    "USB Hub", "Speaker", "Headphones",
    "Desk Lamp", "Tool Box", "Printer Paper",
    "Medical Mask", "Jacket", "Car Battery"
]

def random_date():
    start = datetime(2025, 1, 1)
    end = datetime(2026, 6, 1)
    return (start + timedelta(
        days=random.randint(0, (end - start).days)
    )).strftime("%Y-%m-%d")

with open("inventory_500.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "ProductID",
        "SKU",
        "ProductName",
        "Category",
        "Supplier",
        "Warehouse",
        "Quantity",
        "ReorderLevel",
        "UnitCost",
        "SellingPrice",
        "LastRestockDate",
        "Status"
    ])

    for i in range(1, 15001):
        category = random.choice(categories)
        supplier = random.choice(suppliers)
        warehouse = random.choice(warehouses)

        quantity = random.randint(0, 1000)
        reorder_level = random.randint(10, 100)

        if quantity == 0:
            status = "Out of Stock"
        elif quantity < reorder_level:
            status = "Low Stock"
        else:
            status = "Active"

        unit_cost = round(random.uniform(1.0, 500.0), 2)
        selling_price = round(unit_cost * random.uniform(1.2, 2.5), 2)

        writer.writerow([
            1000 + i,
            f"SKU-{i:04d}",
            f"{random.choice(products)} {i}",
            category,
            supplier,
            warehouse,
            quantity,
            reorder_level,
            unit_cost,
            selling_price,
            random_date(),
            status
        ])

print("inventory_500.csv generated successfully!")