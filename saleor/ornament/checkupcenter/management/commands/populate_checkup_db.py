import json
import logging
import os
from datetime import datetime
from itertools import chain, groupby
from typing import Optional
from dataclasses import dataclass

from django.db import connection
from django.conf import settings
from django.core.management.base import BaseCommand
from slugify import slugify
import requests

from saleor.ornament.vendors.utils import random_string


logger = logging.getLogger(__name__)

attributes_ids = {
    "sex": 1,
    "age_from": 5000,
    "age_to": 10000,
    "biomarkers": 15000,
    "medical_exams": 25000,
}

BIOMARKERS_URL = "https://api.ornament.health/thesaurus-api/public/v1.1/biomarkers"
MEDICAL_EXAMS_URL = (
    "https://api.ornament.health/thesaurus-api/public/v1.0/medical-exams"
)
POPULATE_DB_PATH = os.path.join(
    settings.PROJECT_ROOT, "saleor", "ornament", "checkupcenter", "sql"
)


@dataclass
class AttributeSQL:
    assignedproductattribute: str
    assignedproductattributevalue: str
    attributevalue: Optional[str] = None


@dataclass
class ProductsSQL:
    products: str
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

    def get_attributes_by_key(
        self, lab_meta: dict, key: str, product_id: int, id: int, ornament: bool = False
    ):
        attributes = []
        node = "ornament" if ornament else "lab"

        if attr_by_id := (lab_meta.get("details", {}).get(node, {}).get(key)):
            attributes.append({"product_id": product_id, "id": id, "value": attr_by_id})

        return attributes

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

            value_id = 2 if attr["value"] == "F" else 1

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
        now = datetime.now()
        tsnow = now.timestamp()

        products_path = os.path.join(
            POPULATE_DB_PATH, "source_data_json", "product_product.json"
        )
        products_translations_path = os.path.join(
            POPULATE_DB_PATH, "source_data_json", "product_producttranslation.json"
        )
        products_translations = {}

        with open(products_translations_path, "r") as data:
            rows = json.load(data)
            rows.sort(key=lambda x: x["name"])

            for name, group in groupby(rows, lambda x: x["name"]):
                products_translations[name] = {}

                for translation in group:
                    lang = translation["language_code"]
                    products_translations[name][lang] = {}
                    products_translations[name][lang]["title"] = translation[
                        "description"
                    ]
                    products_translations[name][lang]["description"] = translation[
                        "description_json"
                    ]

        with open(products_path, "r") as data:
            rows = json.load(data)
            now = datetime.now()

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
                            "id": random_string(10),
                            "data": {
                                "text": products_translations.get(name, {})
                                .get("en", {})
                                .get("title", "")
                            },
                            "type": "header",
                        }
                    ],
                    # TODO::ornament move to settings
                    "version": "2.24.3",
                }

                en_lab_description_json = json.loads(
                    products_translations.get(name, {})
                    .get("en", {})
                    .get("description", "{}")
                )
                en_lab_description = (
                    en_lab_description_json.get("details", {})
                    .get("lab", {})
                    .get("description")
                )

                if en_lab_description:
                    blocks = en_lab_description.split("\n")
                    for block in blocks:
                        description["blocks"].append(
                            {
                                "id": random_string(10),
                                "data": {"text": block.replace('"', "“")},
                                "type": "paragraph",
                            }
                        )

                lab_meta = json.loads(r["meta"])

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

                product_type_id = r["product_type_id"]
                category_id = r["category_id"]
                seo_description = "''"
                seo_title = "''"
                weight = "NULL"
                metadata = "{}"
                private_metadata = r["private_meta"]
                slug = slugify(r["name"], lowercase=True)
                default_variant_id = "NULL"
                description_plaintext = en_lab_description
                description_plaintext = "''"
                rating = 0
                search_document = "''"
                search_vector = "NULL"
                search_index_dirty = "true"
                tax_class_id = "NULL"
                external_reference = "NULL"
                created_at = now
                updated_at = now

                products_sql += "\n"

                description = json.dumps(description, ensure_ascii=False).replace(
                    "'", "\\'"
                )

                products_sql += f"""({id}, '{name}', E'{description}', {product_type_id}, {category_id}, {seo_description}, {seo_title}, {weight}, '{metadata}', '{private_metadata}', '{slug}', {default_variant_id}, '{description_plaintext}', {rating}, {search_document}, {search_vector}, {search_index_dirty}, {tax_class_id}, {external_reference}, '{created_at}', '{updated_at}'),"""

            products_sql = products_sql[:-1] + ";"
            age_from = None
            age_to = None
            sex = None
            biomarkers = None
            medical_exams = None

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
                age_from=age_from,
                age_to=age_to,
                sex=sex,
                biomarkers=biomarkers,
                medical_exams=medical_exams,
            )

    def insert_products_with_attributes(self, cursor):
        products = self.migrate_products()

        self.execute_sql_from_str(cursor, products.products, "products")

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
            self.execute_sql_from_file(cursor, "0_product_category.sql")
            self.execute_sql_from_file(cursor, "1_attribute_attribute.sql")
            self.execute_sql_from_file(cursor, "2_attribute_attributeproduct.sql")
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
            self.execute_sql_from_file(cursor, "3_attribute_attributevalue_sex.sql")

            self.insert_products_with_attributes(cursor)

            self.execute_sql_from_file(cursor, "4_permission_permission.sql")
            self.execute_sql_from_file(cursor, "5_app_app.sql")
            self.execute_sql_from_file(cursor, "6_checkupcenter.sql")
