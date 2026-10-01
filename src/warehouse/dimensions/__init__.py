"""
Package: warehouse.dimensions
Dimension table loaders for the star schema.
"""

from src.warehouse.dimensions.dim_date import DateDimensionLoader
from src.warehouse.dimensions.dim_customer import CustomerDimensionLoader
from src.warehouse.dimensions.dim_product import ProductDimensionLoader
from src.warehouse.dimensions.dim_location import LocationDimensionLoader

__all__ = [
    "DateDimensionLoader",
    "CustomerDimensionLoader",
    "ProductDimensionLoader",
    "LocationDimensionLoader",
]
