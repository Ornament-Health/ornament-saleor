import json
import logging
import os
import string
import secrets
from datetime import datetime
from itertools import chain, groupby
from typing import Optional
from dataclasses import dataclass

from django.db import connection
from django.conf import settings
from django.core.management.base import BaseCommand
from slugify import slugify
import requests

## sku_product_id_local_provider_id_price_amount.json
# select pp.sku, pp2.id as product_id, glppv.local_provider_id from geo_local_provider_product_variant glppv
# join geo_local_provider glp on glp.id = glppv.local_provider_id
# join product_productvariant pp on glppv.product_variant_id = pp.id
# join product_product pp2 on pp2.id = pp.product_id
# order by pp2.id;

logger = logging.getLogger(__name__)

BIOMARKERS_URL = "https://api.ornament.health/thesaurus-api/public/v1.1/biomarkers"
MEDICAL_EXAMS_URL = (
    "https://api.ornament.health/thesaurus-api/public/v1.0/medical-exams"
)
POPULATE_DB_PATH = os.path.join(
    settings.PROJECT_ROOT, "saleor", "ornament", "vendors", "kdl", "sql"
)

attributes_ids = {
    "kdl_biomaterials": 5000,
    "kdl_preparation": 10000,
    "kdl_max_duration": 15000,
    "kdl_duration_unit": 20000,
    "sex": 25000,
    "age_from": 30000,
    "age_to": 35000,
    "biomarkers": 40000,
    "medical_exams": 50000,
}


@dataclass
class AttributeSQL:
    assignedproductattribute: str
    assignedproductattributevalue: str
    attributevalue: Optional[str] = None


@dataclass
class ProductsSQL:
    products: str
    biomaterials: Optional[AttributeSQL] = None
    preparation: Optional[AttributeSQL] = None
    max_duration: Optional[AttributeSQL] = None
    duration_unit: Optional[AttributeSQL] = None
    age_from: Optional[AttributeSQL] = None
    age_to: Optional[AttributeSQL] = None
    sex: Optional[AttributeSQL] = None
    biomarkers: Optional[AttributeSQL] = None
    medical_exams: Optional[AttributeSQL] = None


class Command(BaseCommand):
    help = "Populate DB with prod data from saleor 2"

    def execute_sql_from_file(self, cursor, filename):
        path = os.path.join(POPULATE_DB_PATH, filename)
        with open(path, "r") as f:
            cursor.execute(f.read())
            logger.debug(f"Successfully executed {filename}")

    def execute_sql_from_str(self, cursor, sql_str, info):
        cursor.execute(sql_str)
        logger.debug(f"Successfully executed {info}")

    def get_biomarkers_attributes_sql(self):
        resp = requests.post(
            BIOMARKERS_URL,
            json={
                "lang": "EN",
            },
        )
        data = resp.json()

        ids = [b["id"] for b in data["biomarkers"]]
        sql_str = 'insert into attribute_attributevalue (id, "name", attribute_id, slug, sort_order, value) values'

        for id in ids:
            sql_str += "\n"
            sql_str += f"({attributes_ids['biomarkers'] + id}, '{id}', {attributes_ids['biomarkers']}, '{id}', {id + 1}, ''),"

        return sql_str[:-1] + ";"

    def get_medical_exams_attributes_sql(self):
        resp = requests.post(
            MEDICAL_EXAMS_URL,
            json={},
        )
        data = resp.json()

        ids = set(
            chain(
                *[
                    [m_["examTypeObjectId"] for m_ in m["objects"]]
                    for m in data["exams"]
                ]
            )
        )

        sql_str = 'insert into attribute_attributevalue (id, "name", attribute_id, slug, sort_order, value) values'

        for id in ids:
            sql_str += "\n"
            sql_str += f"({attributes_ids['medical_exams'] + id}, '{id}', {attributes_ids['medical_exams']}, '{id}', {id + 1}, ''),"

        return sql_str[:-1] + ";"

    def random_string(self, size):
        letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        return "".join(secrets.choice(letters) for _ in range(size))

    def get_attributes_by_key(
        self, lab_meta: dict, key: str, product_id: int, id: int, ornament: bool = False
    ):
        attributes = []
        node = "ornament" if ornament else "lab"

        if attr_by_id := (lab_meta.get("details", {}).get(node, {}).get(key)):
            attributes.append({"product_id": product_id, "id": id, "value": attr_by_id})

        return attributes

    def text_attributes_sql(self, attributes: list, start_id: int) -> AttributeSQL:
        attributevalue_sql = "insert into attribute_attributevalue (id,name,attribute_id,slug,sort_order,value,plain_text) values"
        assignedproductattribute_sql = "insert into attribute_assignedproductattribute (id,product_id,assignment_id) values"
        assignedproductattributevalue_sql = "insert into attribute_assignedproductattributevalue (id,sort_order,assignment_id,value_id,product_id) values"

        for num, attr in enumerate(attributes, start_id):
            attributevalue_sql += "\n"
            assignedproductattribute_sql += "\n"
            assignedproductattributevalue_sql += "\n"

            value = attr["value"].replace("\n", ", ")
            slug = f'{attr["product_id"]}_{attr["id"]}'

            attributevalue_sql += (
                f"""({num}, '{value}', {attr["id"]}, '{slug}', 0, '', '{value}'),"""
            )
            assignedproductattribute_sql += (
                f"""({num}, {attr["product_id"]}, {start_id}),"""
            )
            assignedproductattributevalue_sql += (
                f"""({num}, 0, {num}, {num}, {attr["product_id"]}),"""
            )

        attributevalue_sql = attributevalue_sql[:-1] + ";"
        assignedproductattribute_sql = assignedproductattribute_sql[:-1] + ";"
        assignedproductattributevalue_sql = assignedproductattributevalue_sql[:-1] + ";"

        return AttributeSQL(
            attributevalue=attributevalue_sql,
            assignedproductattribute=assignedproductattribute_sql,
            assignedproductattributevalue=assignedproductattributevalue_sql,
        )

    def rich_text_attributes_sql(self, attributes: list, start_id: int) -> AttributeSQL:
        attributevalue_sql = "insert into attribute_attributevalue (id,name,attribute_id,slug,sort_order,value,rich_text) values"
        assignedproductattribute_sql = "insert into attribute_assignedproductattribute (id,product_id,assignment_id) values"
        assignedproductattributevalue_sql = "insert into attribute_assignedproductattributevalue (id,sort_order,assignment_id,value_id,product_id) values"

        now = datetime.now()
        tsnow = now.timestamp()

        for num, attr in enumerate(attributes, start_id):
            attributevalue_sql += "\n"
            assignedproductattribute_sql += "\n"
            assignedproductattributevalue_sql += "\n"

            name = attr["value"][:50] + "..."
            value = {
                "time": tsnow,
                "blocks": [
                    {
                        "id": self.random_string(10),
                        "data": {"text": attr["value"]},
                        "type": "paragraph",
                    }
                ],
                "version": "2.24.3",
            }
            slug = f'{attr["product_id"]}_{attr["id"]}'

            attributevalue_sql += f"""({num}, '{name}', {attr["id"]}, '{slug}', 0, '', '{json.dumps(value, ensure_ascii=False)}'),"""
            assignedproductattribute_sql += (
                f"""({num}, {attr["product_id"]}, {start_id}),"""
            )
            assignedproductattributevalue_sql += (
                f"""({num}, 0, {num}, {num}, {attr["product_id"]}),"""
            )

        attributevalue_sql = attributevalue_sql[:-1] + ";"
        assignedproductattribute_sql = assignedproductattribute_sql[:-1] + ";"
        assignedproductattributevalue_sql = assignedproductattributevalue_sql[:-1] + ";"

        return AttributeSQL(
            attributevalue=attributevalue_sql,
            assignedproductattribute=assignedproductattribute_sql,
            assignedproductattributevalue=assignedproductattributevalue_sql,
        )

    def numeric_attributes_sql(self, attributes: list, start_id: int) -> AttributeSQL:
        attributevalue_sql = "insert into attribute_attributevalue (id,name,attribute_id,slug,sort_order,value) values"
        assignedproductattribute_sql = "insert into attribute_assignedproductattribute (id,product_id,assignment_id) values"
        assignedproductattributevalue_sql = "insert into attribute_assignedproductattributevalue (id,sort_order,assignment_id,value_id,product_id) values"

        for num, attr in enumerate(attributes, start_id):
            attributevalue_sql += "\n"
            assignedproductattribute_sql += "\n"
            assignedproductattributevalue_sql += "\n"

            value = attr["value"]
            slug = f'{attr["product_id"]}_{attr["id"]}'

            attributevalue_sql += (
                f"""({num}, '{value}', {attr["id"]}, '{slug}', 0, ''),"""
            )
            assignedproductattribute_sql += (
                f"""({num}, {attr["product_id"]}, {start_id}),"""
            )
            assignedproductattributevalue_sql += (
                f"""({num}, 0, {num}, {num}, {attr["product_id"]}),"""
            )

        attributevalue_sql = attributevalue_sql[:-1] + ";"
        assignedproductattribute_sql = assignedproductattribute_sql[:-1] + ";"
        assignedproductattributevalue_sql = assignedproductattributevalue_sql[:-1] + ";"

        return AttributeSQL(
            attributevalue=attributevalue_sql,
            assignedproductattribute=assignedproductattribute_sql,
            assignedproductattributevalue=assignedproductattributevalue_sql,
        )

    def sex_attributes_sql(self, attributes: list, start_id: int) -> AttributeSQL:
        assignedproductattribute_sql = "insert into attribute_assignedproductattribute (id,product_id,assignment_id) values"
        assignedproductattributevalue_sql = "insert into attribute_assignedproductattributevalue (id,sort_order,assignment_id,value_id,product_id) values"

        for num, attr in enumerate(attributes, start_id):
            assignedproductattribute_sql += "\n"
            assignedproductattributevalue_sql += "\n"

            value_id = 25001 if attr["value"] == "F" else 25000

            assignedproductattribute_sql += (
                f"""({num}, {attr["product_id"]}, {start_id}),"""
            )
            assignedproductattributevalue_sql += (
                f"""({num}, 0, {num}, {value_id}, {attr["product_id"]}),"""
            )

        assignedproductattribute_sql = assignedproductattribute_sql[:-1] + ";"
        assignedproductattributevalue_sql = assignedproductattributevalue_sql[:-1] + ";"

        return AttributeSQL(
            assignedproductattribute=assignedproductattribute_sql,
            assignedproductattributevalue=assignedproductattributevalue_sql,
        )

    def list_attributes_sql(self, attributes: list, start_id: int) -> AttributeSQL:
        assignedproductattribute_sql = "insert into attribute_assignedproductattribute (id,product_id,assignment_id) values"
        assignedproductattributevalue_sql = "insert into attribute_assignedproductattributevalue (id,sort_order,assignment_id,value_id,product_id) values"

        i = start_id

        for num, attr in enumerate(attributes, start_id):
            assignedproductattribute_sql += "\n"
            assignedproductattribute_sql += (
                f"""({num}, {attr["product_id"]}, {start_id}),"""
            )

            for sort_order, list_value in enumerate(set(attr["value"])):
                assignedproductattributevalue_sql += "\n"

                i += 1
                value_id = start_id + list_value

                assignedproductattributevalue_sql += (
                    f"""({i}, {sort_order}, {num}, {value_id}, {attr["product_id"]}),"""
                )

        assignedproductattribute_sql = assignedproductattribute_sql[:-1] + ";"
        assignedproductattributevalue_sql = assignedproductattributevalue_sql[:-1] + ";"

        return AttributeSQL(
            assignedproductattribute=assignedproductattribute_sql,
            assignedproductattributevalue=assignedproductattributevalue_sql,
        )

    def migrate_products(self):
        path = os.path.join(
            POPULATE_DB_PATH, "source_data_json", "product_product.json"
        )

        with open(path, "r") as data:
            rows = json.load(data)
            now = datetime.now()
            tsnow = now.timestamp()

            attributes_biomaterials = []
            attributes_preparation = []
            attributes_max_duration = []
            attributes_duration_unit = []
            attributes_sex = []
            attributes_age_from = []
            attributes_age_to = []
            attributes_biomarkers = []
            attributes_medical_exams = []

            products_sql = 'insert into product_product (id,"name",description,product_type_id,category_id,seo_description,seo_title,weight,metadata,private_metadata,slug,default_variant_id,description_plaintext,rating,search_document,search_vector,search_index_dirty,tax_class_id,external_reference, created_at, updated_at) values'

            for r in rows:
                id = r["id"]
                name = r["name"]
                description = {
                    "time": tsnow,
                    "blocks": [
                        {
                            "id": self.random_string(10),
                            "data": {"text": r["description"]},
                            "type": "header",
                        }
                    ],
                    "version": "2.24.3",
                }
                lab_meta = json.loads(r["meta"])

                attributes_biomaterials += self.get_attributes_by_key(
                    lab_meta,
                    "biomaterials",
                    id,
                    attributes_ids["kdl_biomaterials"],
                )
                attributes_preparation += self.get_attributes_by_key(
                    lab_meta, "preparation", id, attributes_ids["kdl_preparation"]
                )
                attributes_max_duration += self.get_attributes_by_key(
                    lab_meta,
                    "MaxDuration",
                    id,
                    attributes_ids["kdl_max_duration"],
                )
                attributes_duration_unit += self.get_attributes_by_key(
                    lab_meta,
                    "DurationUnit",
                    id,
                    attributes_ids["kdl_duration_unit"],
                )
                attributes_sex += self.get_attributes_by_key(
                    lab_meta, "sex", id, attributes_ids["sex"], True
                )
                attributes_age_from += self.get_attributes_by_key(
                    lab_meta, "ageFrom", id, attributes_ids["age_from"], True
                )
                attributes_age_to += self.get_attributes_by_key(
                    lab_meta, "ageTo", id, attributes_ids["age_to"], True
                )
                attributes_biomarkers += self.get_attributes_by_key(
                    lab_meta, "biomarkers", id, attributes_ids["biomarkers"], True
                )
                attributes_medical_exams += self.get_attributes_by_key(
                    lab_meta,
                    "medical_exams",
                    id,
                    attributes_ids["medical_exams"],
                    True,
                )

                if lab_description := (
                    lab_meta.get("details", {}).get("lab", {}).get("description")
                ):
                    blocks = lab_description.split("\n")
                    for block in blocks:
                        description["blocks"].append(
                            {
                                "id": self.random_string(10),
                                "data": {"text": block},
                                "type": "paragraph",
                            }
                        )
                product_type_id = r["product_type_id"]
                category_id = r["category_id"]
                seo_description = "''"
                seo_title = "''"
                weight = "NULL"
                metadata = "{}"
                private_metadata = r["private_meta"]
                slug = slugify(r["name"], lowercase=True)
                default_variant_id = "NULL"
                description_plaintext = r["description"]
                rating = 0
                search_document = "''"
                search_vector = "NULL"
                search_index_dirty = "true"
                tax_class_id = "NULL"
                external_reference = "NULL"
                created_at = now
                updated_at = now

                products_sql += "\n"
                products_sql += f"""({id}, '{name}', '{json.dumps(description, ensure_ascii=False)}', {product_type_id}, {category_id}, {seo_description}, {seo_title}, {weight}, '{metadata}', '{private_metadata}', '{slug}', {default_variant_id}, '{description_plaintext}', {rating}, {search_document}, {search_vector}, {search_index_dirty}, {tax_class_id}, {external_reference}, '{created_at}', '{updated_at}'),"""

            products_sql = products_sql[:-1] + ";"
            biomaterials = None
            preparation = None
            max_duration = None
            duration_unit = None
            age_from = None
            age_to = None
            sex = None
            biomarkers = None
            medical_exams = None

            if attributes_biomaterials:
                biomaterials = self.text_attributes_sql(
                    attributes_biomaterials,
                    attributes_ids["kdl_biomaterials"],
                )

            if attributes_preparation:
                preparation = self.rich_text_attributes_sql(
                    attributes_preparation,
                    attributes_ids["kdl_preparation"],
                )

            if attributes_max_duration:
                max_duration = self.numeric_attributes_sql(
                    attributes_max_duration,
                    attributes_ids["kdl_max_duration"],
                )

            if attributes_duration_unit:
                duration_unit = self.numeric_attributes_sql(
                    attributes_duration_unit,
                    attributes_ids["kdl_duration_unit"],
                )

            if attributes_age_from:
                age_from = self.numeric_attributes_sql(
                    attributes_age_from, attributes_ids["age_from"]
                )

            if attributes_age_to:
                age_to = self.numeric_attributes_sql(
                    attributes_age_to, attributes_ids["age_to"]
                )

            if attributes_sex:
                sex = self.sex_attributes_sql(attributes_sex, attributes_ids["sex"])

            if attributes_biomarkers:
                biomarkers = self.list_attributes_sql(
                    attributes_biomarkers, attributes_ids["biomarkers"]
                )

            if attributes_medical_exams:
                medical_exams = self.list_attributes_sql(
                    attributes_medical_exams, attributes_ids["medical_exams"]
                )

            return ProductsSQL(
                products=products_sql,
                biomaterials=biomaterials,
                preparation=preparation,
                max_duration=max_duration,
                duration_unit=duration_unit,
                age_from=age_from,
                age_to=age_to,
                sex=sex,
                biomarkers=biomarkers,
                medical_exams=medical_exams,
            )

    def get_productchannellisting_sql(self):
        path = os.path.join(
            POPULATE_DB_PATH,
            "source_data_json",
            "sku_product_id_local_provider_id_price_amount.json",
        )

        with open(path, "r") as data:
            rows = json.load(data)
            now = datetime.now()
            sql_str = "insert into product_productchannellisting (published_at,is_published,channel_id,product_id,discounted_price_amount,currency,visible_in_listings,available_for_purchase_at) values"

            for r in rows:
                published_at = now
                is_published = "true"
                channel_id = r["local_provider_id"]
                product_id = r["product_id"]
                discounted_price_amount = "NULL"
                currency = "'RUB'"
                visible_in_listings = "true"
                available_for_purchase_at = now

                sql_str += "\n"
                sql_str += f"""('{published_at}', {is_published}, {channel_id}, {product_id}, {discounted_price_amount}, {currency}, {visible_in_listings}, '{available_for_purchase_at}'),"""

            return sql_str[:-1] + ";"

    def get_productvariant_sql(self):
        path = os.path.join(
            POPULATE_DB_PATH,
            "source_data_json",
            "sku_product_id_local_provider_id_price_amount.json",
        )

        with open(path, "r") as data:
            rows = json.load(data)
            now = datetime.now()
            sql_str = 'insert into product_productvariant (id, sku, "name", product_id, track_inventory, weight, metadata, private_metadata, sort_order, is_preorder, preorder_end_date, preorder_global_threshold, quantity_limit_per_customer, created_at, updated_at, external_reference) values'

            id = 1
            inserted_variants = []

            for product_id, group in groupby(rows, lambda x: x["product_id"]):
                id = id
                sku = f'KDL-{list(group)[0]["sku"]}'
                name = "'KDL'"
                product_id = product_id
                track_inventory = "false"
                weight = "NULL"
                metadata = "'{}'"
                private_metadata = "'{}'"
                sort_order = "NULL"
                is_preorder = "false"
                preorder_end_date = "NULL"
                preorder_global_threshold = "NULL"
                quantity_limit_per_customer = "NULL"
                created_at = now
                updated_at = now
                external_reference = "NULL"

                sql_str += "\n"
                sql_str += f"""({id}, '{sku}', {name}, {product_id}, {track_inventory}, {weight}, {metadata}, {private_metadata}, {sort_order}, {is_preorder}, {preorder_end_date}, {preorder_global_threshold}, {quantity_limit_per_customer}, '{created_at}', '{updated_at}', {external_reference}),"""

                inserted_variants.append({"id": id, "product_id": product_id})

                id += 1

            with open(
                os.path.join(
                    POPULATE_DB_PATH,
                    "source_data_json",
                    "inserted_variants.json",
                ),
                "w",
            ) as inserted_variants_file:
                inserted_variants_file.write(json.dumps(inserted_variants))

            return sql_str[:-1] + ";"

    def get_productvariantchannellisting_sql(self):
        path = os.path.join(
            POPULATE_DB_PATH,
            "source_data_json",
            "sku_product_id_local_provider_id_price_amount.json",
        )

        with open(path, "r") as data:
            rows = json.load(data)
            sql_str = "insert into product_productvariantchannellisting (currency, price_amount, channel_id, variant_id, cost_price_amount, preorder_quantity_threshold, discounted_price_amount) values"

            with open(
                os.path.join(
                    POPULATE_DB_PATH,
                    "source_data_json",
                    "inserted_variants.json",
                ),
                "r",
            ) as data_variants:
                variants = json.load(data_variants)
                variants = {d["product_id"]: d["id"] for d in variants}

            for r in rows:
                currency = "RUB"
                price_amount = r["price_amount"]
                channel_id = r["local_provider_id"]
                variant_id = variants.get(r["product_id"])
                cost_price_amount = "NULL"
                preorder_quantity_threshold = "NULL"
                discounted_price_amount = r["price_amount"]

                sql_str += "\n"
                sql_str += f"""('{currency}', {price_amount}, {channel_id}, {variant_id}, {cost_price_amount}, {preorder_quantity_threshold}, {discounted_price_amount}),"""

            return sql_str[:-1] + ";"

    def get_warehouse_stock_sql(self):
        path = os.path.join(
            POPULATE_DB_PATH,
            "source_data_json",
            "inserted_variants.json",
        )

        with open(path, "r") as data:
            rows = json.load(data)
            sql_str = "insert into warehouse_stock (quantity, product_variant_id, warehouse_id, quantity_allocated) values"

            for r in rows:
                quantity = 1
                product_variant_id = r["id"]
                warehouse_id = "'2e83f67b-a080-4710-9ee8-4bf3bc0e0b58'"
                quantity_allocated = 0

                sql_str += "\n"
                sql_str += f"""({quantity}, {product_variant_id}, {warehouse_id}, {quantity_allocated}),"""

            return sql_str[:-1] + ";"

    def insert_products_with_attributes(self, cursor):
        products = self.migrate_products()

        self.execute_sql_from_str(cursor, products.products, "products")

        self.execute_sql_from_str(
            cursor,
            products.biomaterials.attributevalue,
            "biomaterials.attributevalue",
        )
        self.execute_sql_from_str(
            cursor,
            products.biomaterials.assignedproductattribute,
            "biomaterials.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.biomaterials.assignedproductattributevalue,
            "biomaterials.assignedproductattributevalue",
        )

        self.execute_sql_from_str(
            cursor,
            products.preparation.attributevalue,
            "preparation.attributevalue",
        )
        self.execute_sql_from_str(
            cursor,
            products.preparation.assignedproductattribute,
            "preparation.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.preparation.assignedproductattributevalue,
            "preparation.assignedproductattributevalue",
        )

        self.execute_sql_from_str(
            cursor,
            products.max_duration.attributevalue,
            "max_duration.attributevalue",
        )
        self.execute_sql_from_str(
            cursor,
            products.max_duration.assignedproductattribute,
            "max_duration.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.max_duration.assignedproductattributevalue,
            "max_duration.assignedproductattributevalue",
        )

        self.execute_sql_from_str(
            cursor,
            products.duration_unit.attributevalue,
            "duration_unit.attributevalue",
        )
        self.execute_sql_from_str(
            cursor,
            products.duration_unit.assignedproductattribute,
            "duration_unit.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.duration_unit.assignedproductattributevalue,
            "duration_unit.assignedproductattributevalue",
        )

        self.execute_sql_from_str(
            cursor, products.age_from.attributevalue, "age_from.attributevalue"
        )
        self.execute_sql_from_str(
            cursor,
            products.age_from.assignedproductattribute,
            "age_from.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.age_from.assignedproductattributevalue,
            "age_from.assignedproductattributevalue",
        )

        self.execute_sql_from_str(
            cursor, products.age_to.attributevalue, "age_to.attributevalue"
        )
        self.execute_sql_from_str(
            cursor,
            products.age_to.assignedproductattribute,
            "age_to.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.age_to.assignedproductattributevalue,
            "age_to.assignedproductattributevalue",
        )

        self.execute_sql_from_str(
            cursor,
            products.sex.assignedproductattribute,
            "sex.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.sex.assignedproductattributevalue,
            "sex.assignedproductattributevalue",
        )

        self.execute_sql_from_str(
            cursor,
            products.biomarkers.assignedproductattribute,
            "biomarkers.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.biomarkers.assignedproductattributevalue,
            "biomarkers.assignedproductattributevalue",
        )

        self.execute_sql_from_str(
            cursor,
            products.medical_exams.assignedproductattribute,
            "medical_exams.assignedproductattribute",
        )
        self.execute_sql_from_str(
            cursor,
            products.medical_exams.assignedproductattributevalue,
            "medical_exams.assignedproductattributevalue",
        )

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.execute_sql_from_file(cursor, "1_channel_channel.sql")
            self.execute_sql_from_file(cursor, "2_product_category.sql")
            self.execute_sql_from_file(cursor, "3_attribute_attribute.sql")
            self.execute_sql_from_file(cursor, "4_attribute_attributeproduct.sql")
            self.execute_sql_from_str(
                cursor,
                self.get_biomarkers_attributes_sql(),
                "attribute_attributevalue biomarkers",
            )
            self.execute_sql_from_str(
                cursor,
                self.get_medical_exams_attributes_sql(),
                "attribute_attributevalue medical_exams",
            )
            self.execute_sql_from_file(cursor, "5_attribute_attributevalue_sex.sql")

            self.insert_products_with_attributes(cursor)

            self.execute_sql_from_str(
                cursor, self.get_productchannellisting_sql(), "productchannellisting"
            )
            self.execute_sql_from_str(
                cursor, self.get_productvariant_sql(), "productvariant"
            )
            self.execute_sql_from_str(
                cursor,
                self.get_productvariantchannellisting_sql(),
                "productvariantchannellisting",
            )
            self.execute_sql_from_file(cursor, "6_tax_taxconfiguration.sql")
            self.execute_sql_from_file(cursor, "7_ornament_geo_city.sql")
            self.execute_sql_from_str(
                cursor, self.get_warehouse_stock_sql(), "warehouse_stock"
            )
            self.execute_sql_from_file(cursor, "8_kdl_kdldiscount.sql")
            self.execute_sql_from_file(cursor, "9_permission_permission.sql")
