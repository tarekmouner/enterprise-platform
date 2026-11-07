import json
from uuid import uuid4

import streamlit as st

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool


@st.cache_resource
def get_engine():
    config = st.secrets["database"]

    url = URL.create(
        drivername="postgresql+psycopg",
        username=config["user"],
        password=config["password"],
        host=config["host"],
        port=int(config.get("port", 5432)),
        database=config.get("name", "postgres"),
    )

    return create_engine(
        url,
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
    )


def test_connection():
    with get_engine().connect() as connection:
        value = connection.execute(
            text("SELECT 1")
        ).scalar_one()

    return value == 1


def list_companies():
    query = text("""
        SELECT
            id::text AS id,
            name
        FROM enterprise.platform_companies
        ORDER BY name
    """)

    with get_engine().connect() as connection:
        rows = connection.execute(query).mappings().all()

    return [dict(row) for row in rows]


def create_company(name):
    query = text("""
        INSERT INTO enterprise.platform_companies (
            id,
            name
        )
        VALUES (
            CAST(:id AS UUID),
            :name
        )
    """)

    values = {
        "id": str(uuid4()),
        "name": name.strip(),
    }

    with get_engine().begin() as connection:
        connection.execute(query, values)


def list_records(company_id, module_key, category_key):
    query = text("""
        SELECT
            id::text AS id,
            record_code,
            payload,
            created_at
        FROM enterprise.platform_records
        WHERE company_id = CAST(:company_id AS UUID)
          AND module_key = :module_key
          AND category_key = :category_key
        ORDER BY created_at DESC
    """)

    values = {
        "company_id": company_id,
        "module_key": module_key,
        "category_key": category_key,
    }

    with get_engine().connect() as connection:
        rows = connection.execute(
            query,
            values,
        ).mappings().all()

    return [dict(row) for row in rows]


def create_record(
    company_id,
    module_key,
    category_key,
    record_code,
    payload,
):
    query = text("""
        INSERT INTO enterprise.platform_records (
            id,
            company_id,
            module_key,
            category_key,
            record_code,
            payload
        )
        VALUES (
            CAST(:id AS UUID),
            CAST(:company_id AS UUID),
            :module_key,
            :category_key,
            :record_code,
            CAST(:payload AS JSONB)
        )
    """)

    values = {
        "id": str(uuid4()),
        "company_id": company_id,
        "module_key": module_key,
        "category_key": category_key,
        "record_code": record_code.strip().upper(),
        "payload": json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
        ),
    }

    with get_engine().begin() as connection:
        connection.execute(query, values)


def module_counts(company_id):
    query = text("""
        SELECT
            module_key,
            COUNT(*) AS total
        FROM enterprise.platform_records
        WHERE company_id = CAST(:company_id AS UUID)
        GROUP BY module_key
    """)

    with get_engine().connect() as connection:
        rows = connection.execute(
            query,
            {"company_id": company_id},
        ).mappings().all()

    return {
        row["module_key"]: int(row["total"])
        for row in rows
    }


def category_counts(company_id, module_key):
    query = text("""
        SELECT
            category_key,
            COUNT(*) AS total
        FROM enterprise.platform_records
        WHERE company_id = CAST(:company_id AS UUID)
          AND module_key = :module_key
        GROUP BY category_key
    """)

    with get_engine().connect() as connection:
        rows = connection.execute(
            query,
            {
                "company_id": company_id,
                "module_key": module_key,
            },
        ).mappings().all()

    return {
        row["category_key"]: int(row["total"])
        for row in rows
    }
