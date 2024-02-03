# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, DataValidationError, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a product from the database"""
        product = ProductFactory()
        app.logger.info(f"Testing Read a product: {product}")
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        found = Product.find(product.id)
        self.assertEqual(found.id, product.id)
        self.assertEqual(found.name, product.name)
        self.assertEqual(found.description, product.description)
        self.assertEqual(found.price, product.price)
        self.assertEqual(found.available, product.available)
        self.assertEqual(found.category, product.category)

    def test_update_a_product(self):
        """It should Update a product that exists in the database"""
        # Create initial product
        product = ProductFactory()
        app.logger.info(f"Testing Update a product: {product}")
        product.id = None
        product.create()
        original_id = product.id
        original_description = product.description
        self.assertIsNotNone(product.id)
        app.logger.info(f"Creating product: {product}")

        # Updating description
        product.description = "Testing"
        product.update()

        self.assertEqual(original_id, product.id)
        self.assertNotEqual(original_description, "Testing")
        self.assertEqual(product.description, "Testing")

        # Fetch all products with new description
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "Testing")

    def test_update_invalid_id(self):
        """It should raise an error when trying to update with invalid ID"""
        # Create initial product
        product = ProductFactory()
        app.logger.info(f"Testing Update a product with invalid ID: {product}")
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        self.assertEqual(len(Product.all()), 1)

        # Update with invalid ID
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_delete_a_product(self):
        """It should Delete a product that exists in the database"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)

        # Delete product
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should list all products in the database"""
        self.assertEqual(len(Product.all()), 0)

        # Creating 5 records and adding to database
        for _ in range(5):
            ProductFactory().create()

        self.assertEqual(len(Product.all()), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        # Creating 5 records and adding to database
        for _ in range(5):
            ProductFactory().create()

        products = Product.all()
        name = products[0].name
        count = len([product for product in products if product.name == name])

        # Find all instances of product
        found_list = Product.find_by_name(name)
        self.assertEqual(found_list.count(), count)
        for product in found_list:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find a Product by Availability"""
        # Creating 10 records and adding to database
        for _ in range(10):
            ProductFactory().create()
        products = Product.all()

        # Get available to search for
        available = products[0].available
        count = len([product for product in products if product.available == available])

        # Check found list for availability
        found_list = Product.find_by_availability(available)
        self.assertEqual(found_list.count(), count)
        for product in found_list:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find a Product by Category"""
        # Creating 10 records and adding to database
        for _ in range(10):
            ProductFactory().create()
        products = Product.all()

        # Get category to search for
        category = products[0].category
        count = len([product for product in products if product.category == category])

        # Check found list for category
        found_list = Product.find_by_category(category)
        self.assertEqual(found_list.count(), count)
        for product in found_list:
            self.assertEqual(product.category, category)

    def test_find_by_price(self):
        """It should Find a Product by Price"""
        # Creating 10 records and adding to database
        for _ in range(10):
            ProductFactory().create()
        products = Product.all()

        # Get price to search for
        price = products[0].price
        count = len([product for product in products if product.price == price])

        # Check found list for price
        found_list = Product.find_by_price(price)
        self.assertEqual(found_list.count(), count)
        for product in found_list:
            self.assertEqual(product.price, price)

    def test_find_by_string_price(self):
        """It should Find a Product by passing in Price as a string"""
        # Creating 10 records and adding to database
        for _ in range(10):
            ProductFactory().create()
        products = Product.all()

        # Get price to search for
        price = products[0].price
        count = len([product for product in products if product.price == price])
        str_price = str(price)
        self.assertIsInstance(str_price, str)

        # Check found list for price
        found_list = Product.find_by_price(str_price)
        self.assertEqual(found_list.count(), count)
        for product in found_list:
            self.assertEqual(product.price, price)
            self.assertIsInstance(product.price, Decimal)
