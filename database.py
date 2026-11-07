from decimal import Decimal
from uuid import uuid4

import streamlit as st

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool


class ConflictError(Exception):
    pass


@st.cache_resource
def engine():
    config = st.secrets["database"]

    url = URL.create(
        "postgresql+psycopg",
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


def read(query, params=None):
    with engine().connect() as connection:
        result = connection.execute(
            text(query),
            params or {},
        ).mappings().all()

    return [dict(row) for row in result]


def audit(connection, company_id, actor, action, kind, entity_id):
    connection.execute(
        text("""
            INSERT INTO erp_core.audit_events (
                company_id,
                actor,
                action,
                entity_type,
                entity_id
            )
            VALUES (
                :company_id,
                :actor,
                :action,
                :kind,
                :entity_id
            )
        """),
        {
            "company_id": company_id,
            "actor": actor,
            "action": action,
            "kind": kind,
            "entity_id": entity_id,
        },
    )


def companies():
    return read("""
        SELECT id::text AS id, name
        FROM erp_core.companies
        ORDER BY name
    """)


def add_company(name, actor):
    name = name.strip()

    if not name:
        raise ValueError("Company name is required")

    company_id = str(uuid4())

    with engine().begin() as connection:
        connection.execute(
            text("""
                INSERT INTO erp_core.companies(id, name)
                VALUES (:id, :name)
            """),
            {"id": company_id, "name": name},
        )

        audit(
            connection,
            company_id,
            actor,
            "created",
            "company",
            company_id,
        )


def departments(company_id):
    return read("""
        SELECT id::text AS id, name
        FROM erp_core.departments
        WHERE company_id = :company_id
        ORDER BY name
    """, {"company_id": company_id})


def add_department(company_id, name, actor):
    name = name.strip()

    if not name:
        raise ValueError("Department name is required")

    department_id = str(uuid4())

    with engine().begin() as connection:
        connection.execute(
            text("""
                INSERT INTO erp_core.departments(
                    id, company_id, name
                )
                VALUES (:id, :company_id, :name)
            """),
            {
                "id": department_id,
                "company_id": company_id,
                "name": name,
            },
        )

        audit(
            connection,
            company_id,
            actor,
            "created",
            "department",
            department_id,
        )


def employees(company_id):
    return read("""
        SELECT
            e.id::text AS id,
            e.department_id::text AS department_id,
            e.code,
            e.full_name,
            e.job_title,
            e.phone,
            e.email,
            e.hire_date,
            e.status,
            e.version,
            d.name AS department
        FROM erp_core.employees e
        JOIN erp_core.departments d
          ON d.id = e.department_id
         AND d.company_id = e.company_id
        WHERE e.company_id = :company_id
        ORDER BY e.full_name
    """, {"company_id": company_id})


def save_employee(company_id, data, actor, existing=None):
    required = ["code", "full_name", "job_title", "department_id"]

    if any(not str(data.get(key, "")).strip() for key in required):
        raise ValueError("Missing employee fields")

    values = {
        **data,
        "company_id": company_id,
        "code": data["code"].strip().upper(),
        "full_name": data["full_name"].strip(),
        "job_title": data["job_title"].strip(),
        "phone": data["phone"].strip(),
        "email": data["email"].strip(),
    }

    with engine().begin() as connection:
        if existing is None:
            employee_id = str(uuid4())
            values["id"] = employee_id

            connection.execute(
                text("""
                    INSERT INTO erp_core.employees (
                        id, company_id, department_id,
                        code, full_name, job_title,
                        phone, email, hire_date, status
                    )
                    VALUES (
                        :id, :company_id, :department_id,
                        :code, :full_name, :job_title,
                        :phone, :email, :hire_date, :status
                    )
                """),
                values,
            )

            action = "created"

        else:
            employee_id = existing["id"]

            values.update({
                "id": employee_id,
                "version": existing["version"],
            })

            result = connection.execute(
                text("""
                    UPDATE erp_core.employees
                    SET
                        department_id = :department_id,
                        code = :code,
                        full_name = :full_name,
                        job_title = :job_title,
                        phone = :phone,
                        email = :email,
                        hire_date = :hire_date,
                        status = :status,
                        version = version + 1,
                        updated_at = NOW()
                    WHERE id = :id
                      AND company_id = :company_id
                      AND version = :version
                """),
                values,
            )

            if result.rowcount != 1:
                raise ConflictError(
                    "Employee changed. Reload the page."
                )

            action = "updated"

        audit(
            connection,
            company_id,
            actor,
            action,
            "employee",
            employee_id,
        )


def contracts(company_id, employee_id):
    return read("""
        SELECT
            id::text AS id,
            contract_number,
            start_date,
            end_date,
            basic_salary,
            currency,
            status
        FROM erp_core.contracts
        WHERE company_id = :company_id
          AND employee_id = :employee_id
        ORDER BY created_at DESC
    """, {
        "company_id": company_id,
        "employee_id": employee_id,
    })


def add_contract(company_id, employee_id, data, actor):
    if not data["contract_number"].strip():
        raise ValueError("Contract number required")

    if data["end_date"] and data["end_date"] < data["start_date"]:
        raise ValueError("Invalid contract dates")

    contract_id = str(uuid4())

    values = {
        **data,
        "id": contract_id,
        "company_id": company_id,
        "employee_id": employee_id,
        "contract_number": data["contract_number"].strip().upper(),
        "basic_salary": Decimal(str(data["basic_salary"])),
        "currency": data["currency"].strip().upper(),
    }

    with engine().begin() as connection:
        connection.execute(
            text("""
                INSERT INTO erp_core.contracts (
                    id, company_id, employee_id,
                    contract_number, start_date,
                    end_date, basic_salary, currency
                )
                VALUES (
                    :id, :company_id, :employee_id,
                    :contract_number, :start_date,
                    :end_date, :basic_salary, :currency
                )
            """),
            values,
        )

        audit(
            connection,
            company_id,
            actor,
            "created_draft",
            "contract",
            contract_id,
        )


def transition_contract(
    company_id,
    employee_id,
    contract_id,
    target,
    actor,
):
    expected = {
        "active": "draft",
        "ended": "active",
    }.get(target)

    if expected is None:
        raise ValueError("Invalid transition")

    with engine().begin() as connection:
        employee = connection.execute(
            text("""
                SELECT status, hire_date
                FROM erp_core.employees
                WHERE company_id = :company_id
                  AND id = :employee_id
                FOR UPDATE
            """),
            {
                "company_id": company_id,
                "employee_id": employee_id,
            },
        ).mappings().first()

        if employee is None:
            raise ConflictError("Employee not found")

        contract = connection.execute(
            text("""
                SELECT status, start_date
                FROM erp_core.contracts
                WHERE company_id = :company_id
                  AND employee_id = :employee_id
                  AND id = :contract_id
                FOR UPDATE
            """),
            {
                "company_id": company_id,
                "employee_id": employee_id,
                "contract_id": contract_id,
            },
        ).mappings().first()

        if contract is None or contract["status"] != expected:
            raise ConflictError("Contract status changed")

        if target == "active":
            if employee["status"] != "active":
                raise ValueError("Employee is inactive")

            if contract["start_date"] < employee["hire_date"]:
                raise ValueError("Contract starts before hire date")

        connection.execute(
            text("""
                UPDATE erp_core.contracts
                SET status = :target
                WHERE id = :contract_id
                  AND company_id = :company_id
                  AND employee_id = :employee_id
                  AND status = :expected
            """),
            {
                "target": target,
                "contract_id": contract_id,
                "company_id": company_id,
                "employee_id": employee_id,
                "expected": expected,
            },
        )

        audit(
            connection,
            company_id,
            actor,
            f"status_{target}",
            "contract",
            contract_id,
        )


def audit_events(company_id):
    return read("""
        SELECT
            actor,
            action,
            entity_type,
            entity_id::text AS entity_id,
            created_at
        FROM erp_core.audit_events
        WHERE company_id = :company_id
        ORDER BY created_at DESC
        LIMIT 200
    """, {"company_id": company_id})
