import hmac
import logging
import time

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from sqlalchemy.exc import IntegrityError

import database as db


# =========================================================
# إعداد التطبيق
# =========================================================

st.set_page_config(
    page_title="Enterprise Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# تعريف الأقسام والصفحات
# =========================================================

MODULES = {
    "company": ("إدارة الشركة", "Company Management"),
    "finance": ("المالية والحسابات", "Finance"),
    "sales": ("المبيعات والعملاء", "Sales & CRM"),
    "purchases": ("المشتريات والموردون", "Purchasing"),
    "inventory": ("المخازن والمخزون", "Inventory"),
    "production": ("الإنتاج والتصنيع", "Production"),
    "quality": ("الجودة", "Quality"),
    "hr": ("الموارد البشرية", "Human Resources"),
    "operations": ("التشغيل والأسطول", "Operations & Fleet"),
    "secretariat": ("السكرتارية والأمن", "Secretariat & Security"),
    "communication": ("التواصل والاجتماعات", "Communication"),
    "digital": ("المواقع والمتاجر", "Digital Channels"),
    "projects": ("المشروعات والمهام", "Projects"),
    "documents": ("المستندات", "Documents"),
    "builder": ("طلبات بناء الأنظمة", "System Build Requests"),
    "ai": ("طلبات المساعد الذكي", "AI Requests"),
    "executive": ("الإدارة العليا", "Executive Management"),
    "governance": ("الحوكمة والتكاملات", "Governance"),
}


def field(key, arabic, english, kind="text", required=False):
    return {
        "key": key,
        "label": (arabic, english),
        "kind": kind,
        "required": required,
    }


def category(arabic, english, fields=None):
    if fields is None:
        fields = [
            field("title", "العنوان", "Title", required=True),
            field("date", "التاريخ", "Date", "date"),
            field("owner", "المسؤول", "Owner"),
            field("notes", "التفاصيل", "Details", "textarea"),
        ]

    return {
        "label": (arabic, english),
        "fields": fields,
    }


PAGES = {
    "company": {
        "branches": category("الفروع والمواقع", "Branches & Sites"),
        "departments": category("الإدارات والأقسام", "Departments"),
        "policies": category("السياسات", "Policies"),
    },

    "finance": {
        "accounts": category("دليل الحسابات", "Account Directory"),
        "banks": category("الحسابات البنكية", "Bank Account Directory"),
        "cashboxes": category("الخزائن", "Cashbox Directory"),
        "expenses": category("طلبات المصروفات", "Expense Requests"),
        "taxes": category("ملفات المتابعة الضريبية", "Tax Follow-up"),
        "budgets": category("مسودات الموازنات", "Budget Drafts"),
    },

    "sales": {
        "customers": category(
            "العملاء",
            "Customers",
            [
                field("name", "اسم العميل", "Customer name",
                      required=True),
                field("phone", "الهاتف", "Phone"),
                field("email", "البريد", "Email"),
                field("address", "العنوان", "Address"),
                field("notes", "ملاحظات", "Notes", "textarea"),
            ],
        ),
        "leads": category("العملاء المحتملون", "Leads"),
        "opportunities": category("الفرص البيعية", "Opportunities"),
        "quotes": category("مسودات عروض الأسعار", "Quote Drafts"),
        "orders": category("سجل طلبات البيع", "Sales Request Register"),
        "visits": category("زيارات المندوبين", "Sales Visits"),
    },

    "purchases": {
        "suppliers": category(
            "الموردون",
            "Suppliers",
            [
                field("name", "اسم المورد", "Supplier name",
                      required=True),
                field("phone", "الهاتف", "Phone"),
                field("email", "البريد", "Email"),
                field("address", "العنوان", "Address"),
                field("notes", "ملاحظات", "Notes", "textarea"),
            ],
        ),
        "requests": category("طلبات الشراء", "Purchase Requests"),
        "quotes": category("سجل عروض الموردين", "Supplier Quotes"),
        "orders": category("مسودات أوامر الشراء", "Purchase Order Drafts"),
        "evaluations": category("تقييم الموردين", "Supplier Evaluations"),
    },

    "inventory": {
        "warehouses": category(
            "تعريف المخازن",
            "Warehouse Directory",
            [
                field("name", "اسم المخزن", "Warehouse name",
                      required=True),
                field("location", "الموقع", "Location"),
                field("manager", "المسؤول", "Manager"),
                field("notes", "ملاحظات", "Notes", "textarea"),
            ],
        ),
        "items": category(
            "تعريف الأصناف",
            "Item Directory",
            [
                field("name", "اسم الصنف", "Item name",
                      required=True),
                field("unit", "وحدة القياس", "Unit",
                      required=True),
                field("group", "المجموعة", "Group"),
                field("notes", "المواصفات", "Specifications", "textarea"),
            ],
        ),
        "stock_requests": category(
            "طلبات حركة مخزون",
            "Stock Movement Requests",
        ),
        "counts": category("محاضر الجرد", "Stock Count Notes"),
    },

    "production": {
        "products": category("تعريف المنتجات", "Product Directory"),
        "plans": category("خطط الإنتاج", "Production Plans"),
        "orders": category("مسودات أوامر التصنيع", "Manufacturing Drafts"),
        "stoppages": category("تقارير التوقف", "Stoppage Reports"),
    },

    "quality": {
        "plans": category("خطط الجودة", "Quality Plans"),
        "inspections": category("سجلات الفحص", "Inspection Records"),
        "ncr": category("بلاغات عدم المطابقة", "Nonconformity Reports"),
        "actions": category("الإجراءات التصحيحية", "Corrective Actions"),
        "audits": category("سجلات التدقيق", "Audit Records"),
    },

    "hr": {
        "employees": category(
            "الموظفون",
            "Employees",
            [
                field("name", "اسم الموظف", "Employee name",
                      required=True),
                field("job", "المسمى الوظيفي", "Job title",
                      required=True),
                field("department", "القسم", "Department"),
                field("branch", "الفرع", "Branch"),
                field("phone", "الهاتف", "Phone"),
                field("email", "البريد", "Email"),
                field("hire_date", "تاريخ التعيين", "Hire date", "date"),
                field("notes", "ملاحظات", "Notes", "textarea"),
            ],
        ),
        "contracts": category("سجل العقود", "Contract Register"),
        "attendance": category(
            "سجل الحضور",
            "Attendance Register",
            [
                field("employee_code", "كود الموظف", "Employee code",
                      required=True),
                field("date", "التاريخ", "Date", "date"),
                field("check_in", "وقت الحضور", "Check-in", "time"),
                field("check_out", "وقت الانصراف", "Check-out", "time"),
                field("notes", "ملاحظات", "Notes", "textarea"),
            ],
        ),
        "leaves": category(
            "طلبات الإجازات",
            "Leave Requests",
            [
                field("employee_code", "كود الموظف", "Employee code",
                      required=True),
                field("type", "نوع الإجازة", "Leave type",
                      required=True),
                field("start", "من تاريخ", "Start date", "date"),
                field("end", "إلى تاريخ", "End date", "date"),
                field("notes", "السبب", "Reason", "textarea"),
            ],
        ),
        "payroll": category(
            "مسودات الرواتب",
            "Payroll Drafts",
            [
                field("employee_code", "كود الموظف", "Employee code",
                      required=True),
                field("period", "الفترة مثل 2026-11", "Period: 2026-11",
                      required=True),
                field("currency", "العملة", "Currency",
                      required=True),
                field("basic", "الأساسي", "Basic", "number"),
                field("additions", "الإضافات", "Additions", "number"),
                field("deductions", "الخصومات", "Deductions", "number"),
                field("notes", "ملاحظات", "Notes", "textarea"),
            ],
        ),
        "evaluations": category("سجل التقييمات", "Evaluation Register"),
        "training": category("سجل التدريب", "Training Register"),
        "exits": category("سجل نهاية الخدمة", "Exit Register"),
    },

    "operations": {
        "vehicles": category("المركبات", "Vehicles"),
        "drivers": category("السائقون", "Drivers"),
        "deliveries": category("مهام التوصيل", "Delivery Tasks"),
        "maintenance": category("طلبات الصيانة", "Maintenance Requests"),
        "fuel": category("سجلات الوقود", "Fuel Records"),
    },

    "secretariat": {
        "appointments": category("المواعيد", "Appointments"),
        "visitors": category("الزوار", "Visitors"),
        "permits": category("طلبات التصاريح", "Permit Requests"),
        "incidents": category("البلاغات الأمنية", "Security Incidents"),
    },

    "communication": {
        "meetings": category("جدولة الاجتماعات", "Meeting Schedule"),
        "rooms": category("تعريف غرف الاجتماعات", "Meeting Room Directory"),
        "minutes": category("محاضر الاجتماعات", "Meeting Minutes"),
        "followups": category("متابعات التواصل", "Communication Follow-ups"),
    },

    "digital": {
        "websites": category("طلبات المواقع", "Website Requests"),
        "stores": category("طلبات المتاجر", "Store Requests"),
        "content": category("مسودات المحتوى", "Content Drafts"),
    },

    "projects": {
        "projects": category("سجل المشروعات", "Project Register"),
        "tasks": category("المهام", "Tasks"),
        "risks": category("مخاطر المشروعات", "Project Risks"),
    },

    "documents": {
        "register": category(
            "فهرس المستندات",
            "Document Index",
            [
                field("title", "اسم المستند", "Document title",
                      required=True),
                field("reference", "مرجع المستند", "Document reference"),
                field("owner", "المسؤول", "Owner"),
                field("notes", "ملاحظات", "Notes", "textarea"),
            ],
        ),
    },

    "builder": {
        "requests": category("طلبات بناء صفحات", "Page Build Requests"),
        "templates": category("أوصاف القوالب", "Template Descriptions"),
    },

    "ai": {
        "requests": category("طلبات التحليل والمساعدة", "Analysis Requests"),
    },

    "executive": {
        "goals": category("الأهداف", "Goals"),
        "decisions": category("القرارات", "Decisions"),
        "initiatives": category("المبادرات", "Initiatives"),
    },

    "governance": {
        "risks": category("سجل المخاطر", "Risk Register"),
        "obligations": category("الالتزامات", "Obligations"),
        "integrations": category("طلبات التكامل", "Integration Requests"),
        "changes": category("طلبات التغيير", "Change Requests"),
    },
}


# =========================================================
# تهيئة الجلسة واللغة
# =========================================================

DEFAULTS = {
    "authenticated": False,
    "lang": "ar",
    "module": None,
    "page": "dashboard",
    "login_attempts": 0,
    "login_block_until": 0.0,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def tr(arabic, english):
    return arabic if st.session_state.lang == "ar" else english


def label(pair):
    return tr(pair[0], pair[1])


direction = "rtl" if st.session_state.lang == "ar" else "ltr"

st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 180px !important;
            min-width: 180px !important;
            max-width: 180px !important;
        }}

        [data-testid="stSidebar"] button,
        [data-testid="stSidebar"] p {{
            font-size: 12px !important;
        }}

        [data-testid="stMainBlockContainer"] {{
            padding-top: 1.2rem;
        }}

        .stApp {{
            direction: {direction};
        }}

        h1 {{
            font-size: 25px !important;
        }}

        h2 {{
            font-size: 21px !important;
        }}

        h3 {{
            font-size: 17px !important;
        }}

        .brand {{
            text-align: center;
            padding: 20px;
            color: #2563eb;
            font-size: 30px;
            font-weight: 700;
            direction: ltr;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# أخطاء آمنة
# =========================================================

def database_error(error):
    logging.getLogger(__name__).error(
        "Database operation failed: %s",
        type(error).__name__,
    )

    st.error(
        tr(
            "تعذر تنفيذ العملية. راجع اتصال قاعدة البيانات "
            "وإنشاء الجداول وإعدادات Secrets.",
            "Operation failed. Check database connection, "
            "table setup and Secrets.",
        )
    )


def read_database(function, *args):
    try:
        return function(*args)
    except Exception as error:
        database_error(error)
        st.stop()


# =========================================================
# التنقل
# =========================================================

def open_module(module_key):
    st.session_state.module = module_key
    st.session_state.page = "dashboard"


def open_page(page_key):
    st.session_state.page = page_key


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def change_language():
    st.session_state.lang = st.session_state.language_choice


def change_company():
    st.session_state.page = "dashboard"


# =========================================================
# تسجيل الدخول
# =========================================================

def login_page():
    st.markdown(
        '<div class="brand">Enterprise Platform</div>',
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.4, 1])

    with center:
        st.subheader(tr("تسجيل الدخول", "Sign in"))

        st.selectbox(
            "اللغة / Language",
            ["ar", "en"],
            index=0 if st.session_state.lang == "ar" else 1,
            format_func=lambda value: (
                "العربية" if value == "ar" else "English"
            ),
            key="language_choice",
            on_change=change_language,
        )

        try:
            auth = st.secrets["auth"]
            expected_username = str(auth["username"])
            expected_password = str(auth["password"])

            if not expected_username or not expected_password:
                raise ValueError("Missing credentials")

        except Exception:
            st.error(
                tr(
                    "أضف قسم [auth] في Streamlit Secrets أولًا.",
                    "Add the [auth] section to Streamlit Secrets first.",
                )
            )
            st.stop()

        blocked = time.time() < st.session_state.login_block_until

        if blocked:
            st.warning(
                tr(
                    "محاولات كثيرة. انتظر دقيقة ثم أعد المحاولة.",
                    "Too many attempts. Wait a minute and retry.",
                )
            )

        with st.form("login_form"):
            username = st.text_input(
                tr("اسم المستخدم", "Username")
            )

            password = st.text_input(
                tr("كلمة المرور", "Password"),
                type="password",
            )

            submitted = st.form_submit_button(
                tr("دخول", "Sign in"),
                type="primary",
                use_container_width=True,
                disabled=blocked,
            )

        if submitted:
            username_valid = hmac.compare_digest(
                username.strip().encode("utf-8"),
                expected_username.encode("utf-8"),
            )

            password_valid = hmac.compare_digest(
                password.encode("utf-8"),
                expected_password.encode("utf-8"),
            )

            if username_valid and password_valid:
                st.session_state.authenticated = True
                st.session_state.login_attempts = 0
                st.session_state.login_block_until = 0.0
                st.session_state.display_name = expected_username
                st.rerun()

            else:
                st.session_state.login_attempts += 1

                if st.session_state.login_attempts >= 5:
                    st.session_state.login_block_until = time.time() + 60
                    st.session_state.login_attempts = 0

                st.error(
                    tr(
                        "بيانات الدخول غير صحيحة.",
                        "Incorrect credentials.",
                    )
                )

        st.caption(
            tr(
                "نسخة تأسيسية بحساب مدير واحد. "
                "ليست جاهزة لبيانات حساسة أو وصول عام.",
                "Foundation version with one administrator account. "
                "Not ready for sensitive data or public access.",
            )
        )


# =========================================================
# إدارة الشركات
# =========================================================

def company_creation_form(form_key):
    with st.form(form_key, clear_on_submit=True):
        name = st.text_input(
            tr("اسم الشركة", "Company name")
        )

        submitted = st.form_submit_button(
            tr("إضافة شركة", "Add company"),
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not name.strip():
            st.error(
                tr(
                    "اسم الشركة مطلوب.",
                    "Company name is required.",
                )
            )
            return

        try:
            db.create_company(name)

        except IntegrityError:
            st.error(
                tr(
                    "اسم الشركة موجود بالفعل.",
                    "Company name already exists.",
                )
            )

        except Exception as error:
            database_error(error)

        else:
            st.rerun()


# =========================================================
# الشريط العلوي
# =========================================================

def top_bar(companies):
    company_map = {
        company["id"]: company["name"]
        for company in companies
    }

    if st.session_state.get("selected_company") not in company_map:
        st.session_state.selected_company = companies[0]["id"]

    c1, c2, c3, c4, c5 = st.columns(
        [1.4, 2.2, 1.7, 1.2, 0.8],
        vertical_alignment="center",
    )

    with c1:
        st.caption(tr("المستخدم", "User"))
        st.write(st.session_state.display_name)

    with c2:
        st.selectbox(
            tr("الشركة", "Company"),
            options=list(company_map.keys()),
            format_func=lambda key: company_map[key],
            key="selected_company",
            on_change=change_company,
        )

    with c3:
        now = datetime.now(ZoneInfo("Africa/Cairo"))
        st.caption(tr("توقيت القاهرة", "Cairo time"))
        st.write(now.strftime("%Y-%m-%d %H:%M"))

    with c4:
        st.selectbox(
            "اللغة / Language",
            ["ar", "en"],
            index=0 if st.session_state.lang == "ar" else 1,
            format_func=lambda value: (
                "العربية" if value == "ar" else "English"
            ),
            key="language_choice",
            on_change=change_language,
        )

    with c5:
        st.button(
            tr("خروج", "Logout"),
            on_click=logout,
            use_container_width=True,
        )

    st.divider()


# =========================================================
# القائمة الجانبية
# =========================================================

def sidebar_menu():
    module = st.session_state.module

    with st.sidebar:
        st.caption("Enterprise Platform")

        st.button(
            tr("كل الأقسام", "All modules"),
            use_container_width=True,
            on_click=open_module,
            args=(None,),
            key="all_modules",
        )

        if module in MODULES:
            st.markdown(f"### {label(MODULES[module])}")

            st.button(
                tr("لوحة القسم", "Dashboard"),
                use_container_width=True,
                on_click=open_page,
                args=("dashboard",),
                key="section_dashboard",
            )

            if module == "company":
                st.button(
                    tr("إضافة شركة", "Add company"),
                    use_container_width=True,
                    on_click=open_page,
                    args=("new_company",),
                    key="new_company_page",
                )

            for page_key, specification in PAGES[module].items():
                st.button(
                    label(specification["label"]),
                    use_container_width=True,
                    on_click=open_page,
                    args=(page_key,),
                    key=f"nav_{module}_{page_key}",
                )

        st.divider()

        with st.expander(tr("تبديل القسم", "Switch module")):
            for module_key, module_label in MODULES.items():
                st.button(
                    label(module_label),
                    use_container_width=True,
                    on_click=open_module,
                    args=(module_key,),
                    key=f"switch_{module_key}",
                )

        if st.button(
            tr("اختبار قاعدة البيانات", "Test database"),
            key="database_test",
        ):
            try:
                if db.test_connection():
                    st.success(tr("متصل", "Connected"))

            except Exception as error:
                database_error(error)


# =========================================================
# الصفحة الترحيبية ولوحة القسم
# =========================================================

def welcome_page(company_id):
    st.subheader(
        tr(
            "مرحبًا بك في منصة المؤسسة",
            "Welcome to Enterprise Platform",
        )
    )

    counts = read_database(
        db.module_counts,
        company_id,
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        tr("الأقسام المتاحة", "Available modules"),
        len(MODULES),
    )

    c2.metric(
        tr("السجلات المحفوظة", "Saved records"),
        sum(counts.values()),
    )

    c3.metric(
        tr("أقسام بها بيانات", "Modules with data"),
        len(counts),
    )

    st.caption(
        tr(
            "هذه أعداد سجلات فعلية، وليست مؤشرات مالية أو تشغيلية.",
            "These are actual record counts, not financial "
            "or operational performance indicators.",
        )
    )

    columns = st.columns(3)

    for index, (module_key, module_label) in enumerate(MODULES.items()):
        with columns[index % 3]:
            st.button(
                f"{label(module_label)} · {counts.get(module_key, 0)}",
                key=f"home_{module_key}",
                use_container_width=True,
                on_click=open_module,
                args=(module_key,),
            )


def module_dashboard(company_id, module_key):
    st.subheader(
        label(MODULES[module_key])
    )

    counts = read_database(
        db.category_counts,
        company_id,
        module_key,
    )

    c1, c2 = st.columns(2)

    c1.metric(
        tr("عدد الصفحات", "Pages"),
        len(PAGES[module_key]),
    )

    c2.metric(
        tr("عدد السجلات", "Records"),
        sum(counts.values()),
    )

    if counts:
        chart = pd.DataFrame([
            {
                tr("الصفحة", "Page"): label(
                    PAGES[module_key].get(
                        key,
                        {"label": (key, key)},
                    )["label"]
                ),
                tr("السجلات", "Records"): count,
            }
            for key, count in counts.items()
        ])

        st.bar_chart(
            chart.set_index(
                tr("الصفحة", "Page")
            )
        )

    else:
        st.info(
            tr(
                "لا توجد بيانات في هذا القسم بعد.",
                "No records in this module yet.",
            )
        )


# =========================================================
# إنشاء حقول النموذج
# =========================================================

def render_field(specification):
    title = label(specification["label"])

    if specification["required"]:
        title += " *"

    kind = specification["kind"]

    if kind == "textarea":
        return st.text_area(title).strip()

    if kind == "date":
        return st.date_input(
            title,
            value=date.today(),
        ).isoformat()

    if kind == "time":
        return st.time_input(
            title,
            value=datetime.strptime("09:00", "%H:%M").time(),
        ).strftime("%H:%M")

    if kind == "number":
        return st.number_input(
            title,
            min_value=0.0,
            step=100.0,
        )

    return st.text_input(title).strip()


# =========================================================
# صفحات الإضافة والعرض
# =========================================================

def record_page(company_id, module_key, category_key):
    specification = PAGES[module_key][category_key]

    st.subheader(
        label(specification["label"])
    )

    st.caption(
        tr(
            "هذه صفحة تسجيل بيانات. الحفظ لا ينشئ قيودًا "
            "محاسبية أو حركة مخزون أو موافقات تلقائية.",
            "This is a record-entry page. Saving does not "
            "post accounting entries, move inventory "
            "or trigger approvals.",
        )
    )

    if module_key in ["builder", "ai"]:
        st.info(
            tr(
                "يُحفظ وصف الطلب فقط. لم يُربط نموذج "
                "ذكاء اصطناعي ولم يُفعّل البناء التلقائي.",
                "Only the request description is saved. "
                "No AI model or automatic builder is connected.",
            )
        )

    if module_key == "communication":
        st.info(
            tr(
                "سجلات الاجتماعات هنا لا تنشئ مكالمات فيديو "
                "ولا تمنع تعارض حجوزات الغرف بعد.",
                "Meeting records do not create video calls "
                "or prevent room-booking conflicts yet.",
            )
        )

    tabs = st.tabs([
        tr("إضافة", "Add"),
        tr("السجلات", "Records"),
    ])

    notice_key = (
        f"saved_{company_id}_{module_key}_{category_key}"
    )

    with tabs[0]:
        if st.session_state.pop(notice_key, False):
            st.success(
                tr(
                    "تم الحفظ في قاعدة البيانات.",
                    "Saved to the database.",
                )
            )

        with st.form(
            f"form_{company_id}_{module_key}_{category_key}"
        ):
            record_code = st.text_input(
                tr(
                    "كود السجل — يجب ألا يتكرر في الصفحة",
                    "Record code — unique within this page",
                )
            )

            payload = {}

            for specification_field in specification["fields"]:
                payload[specification_field["key"]] = render_field(
                    specification_field
                )

            submitted = st.form_submit_button(
                tr("حفظ السجل", "Save record"),
                type="primary",
                use_container_width=True,
            )

        if submitted:
            missing = [
                label(item["label"])
                for item in specification["fields"]
                if item["required"]
                and not str(
                    payload.get(item["key"], "")
                ).strip()
            ]

            if not record_code.strip():
                st.error(
                    tr(
                        "كود السجل مطلوب.",
                        "Record code is required.",
                    )
                )

            elif missing:
                st.error(
                    tr(
                        "أكمل الحقول: ",
                        "Complete fields: ",
                    )
                    + ", ".join(missing)
                )

            elif (
                module_key == "hr"
                and category_key == "leaves"
                and payload["end"] < payload["start"]
            ):
                st.error(
                    tr(
                        "نهاية الإجازة لا يمكن أن تسبق بدايتها.",
                        "Leave end cannot precede its start.",
                    )
                )

            else:
                if module_key == "hr" and category_key == "payroll":
                    payload["demo_net"] = round(
                        payload["basic"]
                        + payload["additions"]
                        - payload["deductions"],
                        2,
                    )

                try:
                    db.create_record(
                        company_id,
                        module_key,
                        category_key,
                        record_code,
                        payload,
                    )

                except IntegrityError:
                    st.error(
                        tr(
                            "تعذر الحفظ. قد يكون الكود مكررًا.",
                            "Save failed. The code may already exist.",
                        )
                    )

                except Exception as error:
                    database_error(error)

                else:
                    st.session_state[notice_key] = True
                    st.rerun()

    with tabs[1]:
        search = st.text_input(
            tr("بحث في السجلات", "Search records"),
            key=f"search_{company_id}_{module_key}_{category_key}",
        ).strip().casefold()

        records = read_database(
            db.list_records,
            company_id,
            module_key,
            category_key,
        )

        rows = []

        for record in records:
            row = {
                tr("الكود", "Code"): record["record_code"],
            }

            for item in specification["fields"]:
                row[label(item["label"])] = (
                    record["payload"].get(item["key"], "")
                )

            if "demo_net" in record["payload"]:
                row[
                    tr("صافي تجريبي", "Demo net")
                ] = record["payload"]["demo_net"]

            row[
                tr("تاريخ الحفظ", "Created at")
            ] = record["created_at"].isoformat()

            if search and not any(
                search in str(value).casefold()
                for value in row.values()
            ):
                continue

            rows.append(row)

        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                f"{tr('عدد النتائج', 'Results')}: {len(rows)}"
            )

        else:
            st.info(
                tr(
                    "لا توجد سجلات مطابقة.",
                    "No matching records.",
                )
            )


# =========================================================
# تشغيل المنصة
# =========================================================

if not st.session_state.authenticated:
    login_page()
    st.stop()


companies = read_database(db.list_companies)

if not companies:
    st.subheader(
        tr(
            "إعداد أول شركة",
            "Set up your first company",
        )
    )

    st.info(
        tr(
            "أضف اسم الشركة للبدء.",
            "Add a company name to begin.",
        )
    )

    company_creation_form("first_company_form")

    st.button(
        tr("خروج", "Logout"),
        on_click=logout,
        key="setup_logout",
    )

    st.stop()


top_bar(companies)
sidebar_menu()

st.caption(
    tr(
        "نسخة تأسيسية لحفظ السجلات. حساب المدير يرى كل الشركات. "
        "الوقت يتحدث عند التفاعل مع الصفحة.",
        "Foundation record-management version. "
        "The administrator can access all companies. "
        "Time updates on page interaction.",
    )
)

company_id = st.session_state.selected_company
module_key = st.session_state.module
page_key = st.session_state.page

if module_key is None:
    welcome_page(company_id)

elif module_key not in MODULES:
    st.error(tr("قسم غير معروف.", "Unknown module."))

elif module_key == "company" and page_key == "new_company":
    st.subheader(
        tr("إضافة شركة جديدة", "Add company")
    )
    company_creation_form("additional_company_form")

elif page_key == "dashboard":
    module_dashboard(company_id, module_key)

elif page_key in PAGES[module_key]:
    record_page(
        company_id,
        module_key,
        page_key,
    )

else:
    st.error(tr("صفحة غير معروفة.", "Unknown page."))
