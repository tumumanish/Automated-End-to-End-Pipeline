"""
Unit tests for the warehouse loader components.
Tests dimension loaders' data extraction logic without a database.
"""

import pandas as pd
import pytest
from unittest.mock import MagicMock

from src.warehouse.dimensions.dim_customer import CustomerDimensionLoader
from src.warehouse.dimensions.dim_product import ProductDimensionLoader
from src.warehouse.dimensions.dim_location import LocationDimensionLoader
from src.warehouse.facts.fact_transactions import FactTransactionsLoader


class TestCustomerDimensionLoader:
    """Test customer dimension extraction."""

    def setup_method(self):
        self.mock_loader = MagicMock()
        self.dim = CustomerDimensionLoader(loader=self.mock_loader)

    def _make_txn_df(self):
        return pd.DataFrame({
            "customer_id": ["CUST-1001", "CUST-1002", "CUST-1001"],
            "location": ["Hyderabad", "Mumbai", "Hyderabad"],
        })

    def test_extract_unique_customers(self):
        """Should extract only unique customer_ids."""
        df = self._make_txn_df()
        result = self.dim.extract_customers(df)
        assert len(result) == 2
        assert set(result["customer_id"]) == {"CUST-1001", "CUST-1002"}

    def test_extract_adds_segment(self):
        """Should derive a segment for each customer."""
        df = self._make_txn_df()
        result = self.dim.extract_customers(df)
        assert "segment" in result.columns
        assert all(s in ["Consumer", "Corporate", "Home Office"] for s in result["segment"])

    def test_extract_adds_region_from_location(self):
        """Should map the first location as the customer's region."""
        df = self._make_txn_df()
        result = self.dim.extract_customers(df)
        assert "region" in result.columns

    def test_extract_empty_df(self):
        """Should return empty DataFrame when no customer_id column."""
        result = self.dim.extract_customers(pd.DataFrame({"x": [1, 2]}))
        assert result.empty


class TestProductDimensionLoader:
    """Test product dimension extraction."""

    def setup_method(self):
        self.mock_loader = MagicMock()
        self.dim = ProductDimensionLoader(loader=self.mock_loader)

    def test_extract_unique_products(self):
        df = pd.DataFrame({
            "product_id": ["PROD-001", "PROD-002", "PROD-001"],
            "unit_price": [45000, 22000, 45000],
        })
        result = self.dim.extract_products(df)
        assert len(result) == 2

    def test_extract_enriches_from_catalogue(self):
        df = pd.DataFrame({
            "product_id": ["PROD-001"],
            "unit_price": [45000],
        })
        result = self.dim.extract_products(df)
        assert result.iloc[0]["product_name"] == "Laptop"
        assert result.iloc[0]["category"] == "Electronics"
        assert result.iloc[0]["subcategory"] == "Computers"


class TestLocationDimensionLoader:
    """Test location dimension extraction."""

    def setup_method(self):
        self.mock_loader = MagicMock()
        self.dim = LocationDimensionLoader(loader=self.mock_loader)

    def test_extract_unique_locations(self):
        df = pd.DataFrame({"location": ["Hyderabad", "Mumbai", "Hyderabad"]})
        result = self.dim.extract_locations(df)
        assert len(result) == 2

    def test_extract_enriches_with_state(self):
        df = pd.DataFrame({"location": ["Hyderabad"]})
        result = self.dim.extract_locations(df)
        assert result.iloc[0]["state"] == "Telangana"
        assert result.iloc[0]["region"] == "South"
        assert result.iloc[0]["country"] == "India"

    def test_extract_generates_location_id(self):
        df = pd.DataFrame({"location": ["Mumbai"]})
        result = self.dim.extract_locations(df)
        assert result.iloc[0]["location_id"] == "LOC-MUMBAI"


class TestFactTransactionsLoader:
    """Test fact transaction key resolution."""

    def setup_method(self):
        self.mock_loader = MagicMock()
        self.fact = FactTransactionsLoader(loader=self.mock_loader)

    def test_resolve_date_keys(self):
        df = pd.DataFrame({"transaction_date": ["2024-06-15"]})
        keys = self.fact._resolve_date_keys(df)
        assert keys.iloc[0] == 20240615

    def test_load_empty_df(self):
        result = self.fact.load(pd.DataFrame(), "batch_001")
        assert result["loaded"] == 0
        assert result["skipped"] == 0
