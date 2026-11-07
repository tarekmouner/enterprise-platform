import logging
import re

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from uuid import uuid4

import pandas as pd
import streamlit as st

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import database as db


# =========================================================
# القوائم الابتدائية
# =========================================================

DEFAULT_OPTIONS = {
    "payment_method": [
        "كاش",
        "آجل",
        "على المبيع",
        "فاتورة + فاتورة",
    ],
    "due_type": [
        "يوم من تاريخ الفاتورة",
        "يوم من نهاية شهر الفاتورة",
        "شهر",
    ],
    "payment_status": [
        "مدفوع بالكامل",
        "جزئي",
        "غير مدفوع",
        "متأخر",
    ],
    "receipt_status": [
        "تم الاستلام",
        "لم يتم الاستلام",
        "مرتجع",
        "مرتجع جزئي",
    ],
    "collector": [
        "محمد رمضان",
        "أيمن",
        "حماده",
        "طارق",
        "مندوب مبيعات",
    ],
    "month": [
        "يناير",
        "فبراير",
        "مارس",
        "أبريل",
        "مايو",
        "يونيو",
        "يوليو",
        "أغسطس",
        "سبتمبر",
        "أكتوبر",
        "نوفمبر",
        "ديسمبر",
    ],
    "year": [str(year) for year in range(2024, 2051)],
    "discount_type": [
        "نسبة مئوية",
        "مبلغ ثابت",
    ],
    "collection_type": [
        "كاش",
        "شيك",
        "تحويل بنكي",
        "خصم من المديونية",
    ],
    "contract_condition": [
        "على المبيعات",
        "على الشيك",
        "مرة واحدة",
        "شهري",
        "ربع سنوي",
        "نصف سنوي",
        "سنوي",
    ],
}

OPTION_LABELS = {
    "payment_method": "طرق الدفع",
    "due_type": "أنواع الاستحقاق",
    "payment_status": "حالات الدفع",
    "receipt_status": "حالات الاستلام",
    "collector": "المحصلون",
    "month": "الشهور",
    "year": "السنوات",
    "discount_type": "أنواع الخصم",
    "collection_type": "أنواع التحصيل",
    "contract_condition": "شروط خصم العقد",
}

COLUMNS = [
    "كود العميل",
    "اسم العميل",
    "طريقة الدفع",
    "مدة الاستحقاق",
    "نوع الاستحقاق",
    "رصيد أول المدة",
    "تاريخ رصيد أول المدة",
    "استحقاق رصيد أول المدة",
    "عدد الفروع",
    "الفروع",
    "الرقم الضريبي",
    "تنبيه فاتورة + فاتورة",
    "الحد الأقصى للعميل",
]


# =========================================================
# أدوات عامة
# =========================================================

def show_error(error):
    logging.getLogger(__name__).error(
        "Customer module error: %s",
        type(error).__name__,
    )

    if isinstance(error, db.ConflictError):
        st.error(
            "بيانات العميل تغيرت. حدّث الصفحة قبل إعادة التعديل."
        )

    elif isinstance(error, IntegrityError):
        st.error(
            "تعذر الحفظ. قد يكون كود العميل أو اسم الخيار مكررًا، "
            "أو توجد علاقة بيانات غير صحيحة."
        )

    elif isinstance(error, ValueError):
        st.error(str(error))

    else:
        st.error(
            "تعذر تنفيذ العملية. تأكد من إنشاء الجداول "
            "وصحة الاتصال بقاعدة البيانات."
        )


def excel_bytes(rows):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(
            rows,
            columns=COLUMNS,
        ).to_excel(
            writer,
            index=False,
            sheet_name="العملاء",
        )

    return output.getvalue()


def parse_money(value, field_name):
    try:
        cleaned = str(value).strip().replace(",", "")
        number = Decimal(cleaned or "0")

        if not number.is_finite():
            raise ValueError

        return number.quantize(Decimal("0.01"))

    except (InvalidOperation, ValueError):
        raise ValueError(
            f"قيمة غير صحيحة في: {field_name}"
        )


def parse_date(value, field_name, optional=False):
    if value is None or str(value).strip() == "":
        if optional:
            return None

        raise ValueError(
            f"الحقل مطلوب: {field_name}"
        )

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        # صيغة موحدة لتجنب عكس اليوم والشهر.
        return date.fromisoformat(
            str(value).strip()
        )

    except ValueError:
        raise ValueError(
            f"{field_name}: استخدم تاريخًا بصيغة YYYY-MM-DD"
        )


def split_branches(value):
    cleaned = str(value).strip()

    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1]

    if not cleaned.strip():
        return []

    names = [
        item.strip()
        for item in re.split(
            r"\s*[-–—]\s*",
            cleaned,
        )
        if item.strip()
    ]

    if len(names) != len(set(names)):
        raise ValueError(
            "يوجد اسم فرع مكرر داخل العميل نفسه."
        )

    return names


# =========================================================
# الإعدادات
# =========================================================

def ensure_options(company_id):
    with db.engine().begin() as connection:
        for category, values in DEFAULT_OPTIONS.items():
            for index, value in enumerate(values):
                connection.execute(
                    text("""
                        INSERT INTO erp_core.customer_options (
                            company_id,
                            category,
                            value,
                            sort_order
                        )
                        VALUES (
                            :company_id,
                            :category,
                            :value,
                            :sort_order
                        )
                        ON CONFLICT (
                            company_id,
                            category,
                            value
                        )
                        DO NOTHING
                    """),
                    {
                        "company_id": company_id,
                        "category": category,
                        "value": value,
                        "sort_order": index,
                    },
                )


def get_options(company_id):
    rows = db.read("""
        SELECT category, value
        FROM erp_core.customer_options
        WHERE company_id = :company_id
        ORDER BY category, sort_order, value
    """, {"company_id": company_id})

    result = {
        key: []
        for key in DEFAULT_OPTIONS
    }

    for row in rows:
        if row["category"] in result:
            result[row["category"]].append(
                row["value"]
            )

    return result


def settings_page(company_id, actor, options):
    st.subheader("المسودة والإعدادات")

    st.caption(
        "هذه القوائم تخص الشركة الحالية. "
        "إضافة طريقة دفع جديدة لا تنشئ قاعدة استحقاق تلقائيًا."
    )

    rows = []

    for category, values in options.items():
        for index, value in enumerate(values, start=1):
            rows.append({
                "القائمة": OPTION_LABELS[category],
                "الترتيب": index,
                "القيمة": value,
            })

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### إضافة اختيار")

    with st.form(
        f"customer_option_form_{company_id}"
    ):
        category = st.selectbox(
            "القائمة",
            options=list(OPTION_LABELS),
            format_func=lambda key: OPTION_LABELS[key],
        )

        value = st.text_input(
            "الاختيار الجديد"
        )

        submitted = st.form_submit_button(
            "حفظ الاختيار",
            type="primary",
        )

    if submitted:
        value = value.strip()

        if not value:
            st.error("اكتب قيمة الاختيار.")
            return

        try:
            with db.engine().begin() as connection:
                connection.execute(
                    text("""
                        INSERT INTO erp_core.customer_options (
                            company_id,
                            category,
                            value,
                            sort_order
                        )
                        VALUES (
                            :company_id,
                            :category,
                            :value,
                            1000
                        )
                    """),
                    {
                        "company_id": company_id,
                        "category": category,
                        "value": value,
                    },
                )

                db.audit(
                    connection,
                    company_id,
                    actor,
                    "option_added",
                    "customer_settings",
                    company_id,
                )

        except Exception as error:
            show_error(error)

        else:
            st.rerun()


# =========================================================
# قراءة العملاء
# =========================================================

def get_customers(company_id):
    return db.read("""
        SELECT
            c.id::text AS id,
            c.code,
            c.name,
            c.payment_method,
            c.due_duration,
            c.due_type,
            c.opening_balance,
            c.opening_date,
            c.opening_due_date,
            c.tax_number,
            c.invoice_plus_alert,
            c.credit_limit,
            c.version,

            COALESCE(
                (
                    SELECT jsonb_agg(
                        b.name
                        ORDER BY b.name
                    )
                    FROM erp_core.customer_branches b
                    WHERE b.customer_id = c.id
                      AND b.company_id = c.company_id
                      AND b.active = TRUE
                ),
                '[]'::jsonb
            ) AS branches

        FROM erp_core.customers c

        WHERE c.company_id = :company_id

        ORDER BY c.created_at, c.code
    """, {"company_id": company_id})


def customer_to_row(customer):
    branches = customer["branches"]

    return {
        "كود العميل": customer["code"],
        "اسم العميل": customer["name"],
        "طريقة الدفع": customer["payment_method"],
        "مدة الاستحقاق": customer["due_duration"],
        "نوع الاستحقاق": customer["due_type"],
        "رصيد أول المدة": str(customer["opening_balance"]),
        "تاريخ رصيد أول المدة":
            customer["opening_date"].isoformat(),
        "استحقاق رصيد أول المدة": (
            customer["opening_due_date"].isoformat()
            if customer["opening_due_date"]
            else ""
        ),
        "عدد الفروع": len(branches),
        "الفروع": (
            "( " + " - ".join(branches) + " )"
            if branches
            else ""
        ),
        "الرقم الضريبي": customer["tax_number"],
        "تنبيه فاتورة + فاتورة": (
            "نعم" if customer["invoice_plus_alert"] else "لا"
        ),
        "الحد الأقصى للعميل": str(customer["credit_limit"]),
    }


# =========================================================
# التحقق من بيانات العميل
# =========================================================

def validate_customer(row, options):
    code = str(
        row.get("كود العميل", "")
    ).strip().upper()

    name = str(
        row.get("اسم العميل", "")
    ).strip()

    method = str(
        row.get("طريقة الدفع", "")
    ).strip()

    due_type = str(
        row.get("نوع الاستحقاق", "")
    ).strip()

    if not code or not name:
        raise ValueError(
            "كود العميل واسم العميل مطلوبان."
        )

    if method not in options["payment_method"]:
        raise ValueError(
            f"طريقة دفع غير موجودة في المسودة: {method}"
        )

    if due_type not in options["due_type"]:
        raise ValueError(
            f"نوع استحقاق غير موجود في المسودة: {due_type}"
        )

    try:
        duration_value = Decimal(
            str(row.get("مدة الاستحقاق", "0")).strip() or "0"
        )

        branch_count_value = Decimal(
            str(row.get("عدد الفروع", "0")).strip() or "0"
        )

        if (
            not duration_value.is_finite()
            or not branch_count_value.is_finite()
        ):
            raise ValueError

        if (
            duration_value != duration_value.to_integral_value()
            or branch_count_value
            != branch_count_value.to_integral_value()
        ):
            raise ValueError

        duration = int(duration_value)
        branch_count = int(branch_count_value)

    except (InvalidOperation, ValueError, OverflowError):
        raise ValueError(
            "مدة الاستحقاق وعدد الفروع يجب أن يكونا عددين صحيحين."
        )

    if duration < 0 or branch_count < 0:
        raise ValueError(
            "مدة الاستحقاق وعدد الفروع لا يمكن أن يكونا سالبين."
        )

    branches = split_branches(
        row.get("الفروع", "")
    )

    if len(branches) != branch_count:
        raise ValueError(
            f"عدد الفروع المكتوب {branch_count}، "
            f"لكن الأسماء المدخلة {len(branches)}."
        )

    opening = parse_money(
        row.get("رصيد أول المدة", "0"),
        "رصيد أول المدة",
    )

    credit = parse_money(
        row.get("الحد الأقصى للعميل", "0"),
        "الحد الأقصى للعميل",
    )

    if credit < 0:
        raise ValueError(
            "الحد الائتماني لا يمكن أن يكون سالبًا."
        )

    alert = str(
        row.get("تنبيه فاتورة + فاتورة", "لا")
    ).strip()

    if alert not in {"نعم", "لا"}:
        raise ValueError(
            "تنبيه فاتورة + فاتورة يجب أن يكون نعم أو لا."
        )

    return {
        "code": code,
        "name": name,
        "payment_method": method,
        "due_duration": duration,
        "due_type": due_type,
        "opening_balance": opening,
        "opening_date": parse_date(
            row.get("تاريخ رصيد أول المدة"),
            "تاريخ رصيد أول المدة",
        ),
        "opening_due_date": parse_date(
            row.get("استحقاق رصيد أول المدة", ""),
            "استحقاق رصيد أول المدة",
            optional=True,
        ),
        "tax_number": str(
            row.get("الرقم الضريبي", "")
        ).strip(),
        "invoice_plus_alert": alert == "نعم",
        "credit_limit": credit,
        "branches": branches,
    }


# =========================================================
# الحفظ داخل معاملة واحدة
# =========================================================

def write_customer(
    connection,
    company_id,
    actor,
    data,
    existing=None,
):
    values = {
        key: value
        for key, value in data.items()
        if key != "branches"
    }

    values["company_id"] = company_id

    if existing is None:
        customer_id = str(uuid4())
        values["id"] = customer_id

        connection.execute(
            text("""
                INSERT INTO erp_core.customers (
                    id,
                    company_id,
                    code,
                    name,
                    payment_method,
                    due_duration,
                    due_type,
                    opening_balance,
                    opening_date,
                    opening_due_date,
                    tax_number,
                    invoice_plus_alert,
                    credit_limit
                )
                VALUES (
                    :id,
                    :company_id,
                    :code,
                    :name,
                    :payment_method,
                    :due_duration,
                    :due_type,
                    :opening_balance,
                    :opening_date,
                    :opening_due_date,
                    :tax_number,
                    :invoice_plus_alert,
                    :credit_limit
                )
            """),
            values,
        )

        action = "created"

    else:
        customer_id = existing["id"]

        values["id"] = customer_id
        values["version"] = existing["version"]

        result = connection.execute(
            text("""
                UPDATE erp_core.customers
                SET
                    code = :code,
                    name = :name,
                    payment_method = :payment_method,
                    due_duration = :due_duration,
                    due_type = :due_type,
                    opening_balance = :opening_balance,
                    opening_date = :opening_date,
                    opening_due_date = :opening_due_date,
                    tax_number = :tax_number,
                    invoice_plus_alert = :invoice_plus_alert,
                    credit_limit = :credit_limit,
                    version = version + 1,
                    updated_at = NOW()
                WHERE id = :id
                  AND company_id = :company_id
                  AND version = :version
            """),
            values,
        )

        if result.rowcount != 1:
            raise db.ConflictError(
                "Customer changed"
            )

        action = "updated"

        connection.execute(
            text("""
                UPDATE erp_core.customer_branches
                SET active = FALSE
                WHERE company_id = :company_id
                  AND customer_id = :customer_id
            """),
            {
                "company_id": company_id,
                "customer_id": customer_id,
            },
        )

    for branch in data["branches"]:
        connection.execute(
            text("""
                INSERT INTO erp_core.customer_branches (
                    company_id,
                    customer_id,
                    name,
                    active
                )
                VALUES (
                    :company_id,
                    :customer_id,
                    :name,
                    TRUE
                )
                ON CONFLICT (customer_id, name)
                DO UPDATE SET active = TRUE
            """),
            {
                "company_id": company_id,
                "customer_id": customer_id,
                "name": branch,
            },
        )

    db.audit(
        connection,
        company_id,
        actor,
        action,
        "customer",
        customer_id,
    )


# =========================================================
# إضافة العميل وتعديله
# =========================================================

def customer_form(
    company_id,
    actor,
    options,
    existing=None,
):
    row = (
        customer_to_row(existing)
        if existing
        else {
            "طريقة الدفع": "آجل",
            "نوع الاستحقاق": "يوم من تاريخ الفاتورة",
            "تاريخ رصيد أول المدة": date.today().isoformat(),
        }
    )

    suffix = (
        existing["id"]
        if existing
        else "new"
    )

    with st.form(
        f"customer_form_{company_id}_{suffix}"
    ):
        c1, c2 = st.columns(2)

        with c1:
            code = st.text_input(
                "كود العميل",
                value=row.get("كود العميل", ""),
            )

            name = st.text_input(
                "اسم العميل",
                value=row.get("اسم العميل", ""),
            )

            methods = options["payment_method"]

            method_value = row.get(
                "طريقة الدفع",
                methods[0],
            )

            method = st.selectbox(
                "طريقة الدفع",
                options=methods,
                index=(
                    methods.index(method_value)
                    if method_value in methods
                    else 0
                ),
            )

            duration = st.number_input(
                "مدة الاستحقاق",
                min_value=0,
                step=1,
                value=int(row.get("مدة الاستحقاق", 0)),
            )

            due_types = options["due_type"]

            due_value = row.get(
                "نوع الاستحقاق",
                due_types[0],
            )

            due_type = st.selectbox(
                "نوع الاستحقاق",
                options=due_types,
                index=(
                    due_types.index(due_value)
                    if due_value in due_types
                    else 0
                ),
            )

            opening = st.text_input(
                "رصيد أول المدة",
                value=str(row.get("رصيد أول المدة", "0")),
                help="القيمة السالبة تعني رصيدًا لصالح العميل.",
            )

            opening_date = st.date_input(
                "تاريخ رصيد أول المدة",
                value=date.fromisoformat(
                    row["تاريخ رصيد أول المدة"]
                ),
            )

        with c2:
            has_opening_due = st.checkbox(
                "يوجد موعد استحقاق لرصيد أول المدة",
                value=bool(
                    row.get("استحقاق رصيد أول المدة", "")
                ),
            )

            opening_due_date = st.date_input(
                "استحقاق رصيد أول المدة إن وجد",
                value=(
                    date.fromisoformat(
                        row["استحقاق رصيد أول المدة"]
                    )
                    if row.get("استحقاق رصيد أول المدة")
                    else date.today()
                ),
            )

            branch_count = st.number_input(
                "عدد الفروع",
                min_value=0,
                step=1,
                value=int(row.get("عدد الفروع", 0)),
            )

            branches = st.text_input(
                "الفروع",
                value=row.get("الفروع", ""),
                placeholder="(معادي - تجمع - أكتوبر)",
            )

            tax_number = st.text_input(
                "الرقم الضريبي",
                value=row.get("الرقم الضريبي", ""),
            )

            alert = st.selectbox(
                "تنبيه فاتورة + فاتورة",
                ["لا", "نعم"],
                index=(
                    1
                    if row.get("تنبيه فاتورة + فاتورة") == "نعم"
                    else 0
                ),
            )

            credit = st.text_input(
                "الحد الأقصى للعميل — صفر يعني بلا حد",
                value=str(
                    row.get("الحد الأقصى للعميل", "0")
                ),
            )

        submitted = st.form_submit_button(
            "حفظ التعديلات" if existing else "إضافة العميل",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        input_row = {
            "كود العميل": code,
            "اسم العميل": name,
            "طريقة الدفع": method,
            "مدة الاستحقاق": duration,
            "نوع الاستحقاق": due_type,
            "رصيد أول المدة": opening,
            "تاريخ رصيد أول المدة": opening_date,
            "استحقاق رصيد أول المدة": (
                opening_due_date
                if has_opening_due
                else ""
            ),
            "عدد الفروع": branch_count,
            "الفروع": branches,
            "الرقم الضريبي": tax_number,
            "تنبيه فاتورة + فاتورة": alert,
            "الحد الأقصى للعميل": credit,
        }

        try:
            data = validate_customer(
                input_row,
                options,
            )

            with db.engine().begin() as connection:
                write_customer(
                    connection,
                    company_id,
                    actor,
                    data,
                    existing,
                )

        except Exception as error:
            show_error(error)

        else:
            st.session_state.customer_saved = True
            st.rerun()


# =========================================================
# Excel: معاينة ثم اعتماد
# =========================================================

def import_page(company_id, actor, options, customers):
    st.caption(
        "الاستيراد الحالي يضيف عملاء جدد فقط. "
        "الأكواد الموجودة تُرفض ولا تُستبدل تلقائيًا."
    )

    template = [{
        "كود العميل": "CUST-001",
        "اسم العميل": "عميل تجريبي",
        "طريقة الدفع": "آجل",
        "مدة الاستحقاق": 30,
        "نوع الاستحقاق": "يوم من تاريخ الفاتورة",
        "رصيد أول المدة": "0",
        "تاريخ رصيد أول المدة": date.today().isoformat(),
        "استحقاق رصيد أول المدة": "",
        "عدد الفروع": 3,
        "الفروع": "(معادي - تجمع - أكتوبر)",
        "الرقم الضريبي": "",
        "تنبيه فاتورة + فاتورة": "لا",
        "الحد الأقصى للعميل": "0",
    }]

    st.download_button(
        "تحميل قالب Excel",
        data=excel_bytes(template),
        file_name="customers_template.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        key=f"customer_template_{company_id}",
    )

    uploaded = st.file_uploader(
        "ارفع ملف العملاء بصيغة xlsx",
        type=["xlsx"],
        key=f"customer_import_{company_id}",
    )

    if uploaded is None:
        return

    if uploaded.size > 5 * 1024 * 1024:
        st.error("الحد الحالي للملف 5 ميجابايت.")
        return

    try:
        book = pd.ExcelFile(
            BytesIO(uploaded.getvalue()),
            engine="openpyxl",
        )

        sheet = st.selectbox(
            "ورقة البيانات",
            book.sheet_names,
            key=f"customer_sheet_{company_id}",
        )

        frame = pd.read_excel(
            book,
            sheet_name=sheet,
            dtype=str,
            keep_default_na=False,
            nrows=2001,
        )

        frame.columns = [
            str(column).strip()
            for column in frame.columns
        ]

        if frame.columns.duplicated().any():
            raise ValueError(
                "الملف يحتوي على أسماء أعمدة مكررة."
            )

        missing = [
            column
            for column in COLUMNS
            if column not in frame.columns
        ]

        if missing:
            raise ValueError(
                "أعمدة ناقصة: " + "، ".join(missing)
            )

        frame = frame.loc[
            frame["كود العميل"].str.strip().ne("")
            | frame["اسم العميل"].str.strip().ne("")
        ]

        if len(frame) > 2000:
            raise ValueError(
                "الحد الحالي 2000 عميل في الاستيراد الواحد."
            )

        existing_codes = {
            customer["code"].casefold()
            for customer in customers
        }

        seen_codes = set()
        valid = []
        errors = []

        for index, row in frame.iterrows():
            try:
                data = validate_customer(
                    row.to_dict(),
                    options,
                )

                normalized = data["code"].casefold()

                if normalized in existing_codes:
                    raise ValueError(
                        "كود العميل موجود بالفعل في الشركة."
                    )

                if normalized in seen_codes:
                    raise ValueError(
                        "كود العميل مكرر داخل الملف."
                    )

                seen_codes.add(normalized)
                valid.append(data)

            except ValueError as error:
                errors.append({
                    "صف Excel": int(index) + 2,
                    "الخطأ": str(error),
                })

    except Exception as error:
        show_error(error)
        return

    st.markdown("### معاينة البيانات")

    st.dataframe(
        frame,
        hide_index=True,
        use_container_width=True,
    )

    st.write(
        f"السجلات الجاهزة: {len(valid)} | الأخطاء: {len(errors)}"
    )

    if errors:
        st.dataframe(
            pd.DataFrame(errors),
            hide_index=True,
            use_container_width=True,
        )

        st.warning(
            "لم يُحفظ أي سجل. صحح الأخطاء ثم ارفع الملف مرة أخرى."
        )
        return

    confirmed = st.checkbox(
        "راجعت البيانات وأوافق على إضافة العملاء",
        key=f"confirm_customer_import_{company_id}",
    )

    if st.button(
        "اعتماد الاستيراد",
        type="primary",
        disabled=not confirmed or not valid,
        key=f"save_customer_import_{company_id}",
    ):
        try:
            # حفظ الملف كله أو التراجع عنه كله.
            with db.engine().begin() as connection:
                for data in valid:
                    write_customer(
                        connection,
                        company_id,
                        actor,
                        data,
                    )

        except Exception as error:
            show_error(error)

        else:
            st.session_state.customer_saved = True
            st.rerun()


# =========================================================
# الصفحة الرئيسية لوحدة العملاء
# =========================================================

def render(company_id, actor):
    st.subheader("حسابات العملاء — تأسيس البيانات")

    st.caption(
        "المتاح الآن: المسودة، العملاء، الفروع، التعديل، "
        "استيراد وتصدير Excel. الفواتير والأرصدة المتحركة "
        "والتحصيلات لم تُربط بهذه الوحدة بعد."
    )

    try:
        ensure_options(company_id)
        options = get_options(company_id)
        customers = get_customers(company_id)

    except Exception as error:
        show_error(error)
        return

    if st.session_state.pop("customer_saved", False):
        st.success("تم حفظ البيانات في قاعدة البيانات.")

    section = st.radio(
        "الصفحة",
        ["المسودة والإعدادات", "العملاء"],
        horizontal=True,
        key=f"customer_section_{company_id}",
    )

    if section == "المسودة والإعدادات":
        settings_page(
            company_id,
            actor,
            options,
        )
        return

    add_tab, list_tab, edit_tab, import_tab = st.tabs([
        "إضافة عميل",
        "جدول العملاء",
        "تعديل عميل",
        "استيراد Excel",
    ])

    with add_tab:
        customer_form(
            company_id,
            actor,
            options,
        )

    with list_tab:
        search = st.text_input(
            "بحث بكود العميل أو اسمه",
            key=f"customer_search_{company_id}",
        ).strip().casefold()

        rows = []

        for customer in customers:
            if search and not (
                search in customer["code"].casefold()
                or search in customer["name"].casefold()
            ):
                continue

            rows.append(
                customer_to_row(customer)
            )

        if rows:
            display = pd.DataFrame(rows)

            display.insert(
                0,
                "م",
                range(1, len(display) + 1),
            )

            st.dataframe(
                display,
                hide_index=True,
                use_container_width=True,
            )

            st.download_button(
                "تصدير النتائج إلى Excel",
                data=excel_bytes(rows),
                file_name="customers.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key=f"export_customers_{company_id}",
            )

        else:
            st.info("لا يوجد عملاء مطابقون.")

    with edit_tab:
        if not customers:
            st.info("أضف عميلًا أولًا.")

        else:
            customer_map = {
                customer["id"]: customer
                for customer in customers
            }

            selected_id = st.selectbox(
                "اختيار العميل بالكود أو الاسم",
                options=list(customer_map),
                format_func=lambda key: (
                    f"{customer_map[key]['code']} — "
                    f"{customer_map[key]['name']}"
                ),
                key=f"edit_customer_{company_id}",
            )

            customer_form(
                company_id,
                actor,
                options,
                existing=customer_map[selected_id],
            )

    with import_tab:
        import_page(
            company_id,
            actor,
            options,
            customers,
        )
