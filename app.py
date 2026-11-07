import hmac
import logging

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from sqlalchemy.exc import IntegrityError

import database as db
import hr_operations

st.set_page_config(
    page_title="Enterprise Workspace",
    layout="wide",
    initial_sidebar_state="expanded",
)


for key, default in {
    "authenticated": False,
    "module": "home",
    "hr_page": "Dashboard",
    "lang": "ar",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def tr(ar, en):
    return ar if st.session_state.lang == "ar" else en


def change_language():
    st.session_state.lang = st.session_state.language


def navigate(module):
    st.session_state.module = module
    st.session_state.hr_page = "Dashboard"


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def attempt(function, *args):
    try:
        function(*args)

    except db.ConflictError:
        st.error(tr(
            "البيانات تغيرت. حدّث الصفحة وحاول مجددًا.",
            "Data changed. Reload and retry.",
        ))

    except IntegrityError:
        st.error(tr(
            "تعذر الحفظ: كود مكرر، علاقة غير صحيحة، "
            "أو عقد نشط موجود بالفعل.",
            "Save failed: duplicate code, invalid relationship "
            "or an active contract already exists.",
        ))

    except ValueError as error:
        messages = {
            "Company name is required": (
                "اسم الشركة مطلوب.",
                "Company name is required.",
            ),
            "Department name is required": (
                "اسم الإدارة مطلوب.",
                "Department name is required.",
            ),
            "Missing employee fields": (
                "أكمل بيانات الموظف المطلوبة.",
                "Complete required employee fields.",
            ),
            "Contract number required": (
                "رقم العقد مطلوب.",
                "Contract number is required.",
            ),
            "Invalid contract dates": (
                "تواريخ العقد غير صحيحة.",
                "Invalid contract dates.",
            ),
            "Employee is inactive": (
                "الموظف غير نشط.",
                "Employee is inactive.",
            ),
            "Contract starts before hire date": (
                "بداية العقد تسبق تاريخ التعيين.",
                "Contract starts before hire date.",
            ),
            "Invalid attendance times": (
                "وقت الانصراف يجب أن يكون بعد الحضور.",
                "Check-out must follow check-in.",
            ),
            "Attendance precedes hire date": (
                "الحضور يسبق تاريخ تعيين الموظف.",
                "Attendance precedes hire date.",
            ),
            "Invalid leave request": (
                "راجع تواريخ الإجازة والسبب.",
                "Check leave dates and reason.",
            ),
            "Leave precedes hire date": (
                "الإجازة تسبق تاريخ التعيين.",
                "Leave precedes hire date.",
            ),
            "Overlapping leave request": (
                "يوجد طلب إجازة متداخل لهذا الموظف.",
                "An overlapping leave request exists.",
            ),
            "Review note required": (
                "تعليق المراجعة مطلوب.",
                "Review note is required.",
            ),
        }

        pair = messages.get(
            str(error),
            (
                "راجع البيانات وحالة الموظف أو الطلب.",
                "Check the data and employee/request status.",
            ),
        )

        st.error(tr(pair[0], pair[1]))        st.error(tr(
            "راجع الحقول والتواريخ وحالة الموظف والعقد.",
            "Check fields, dates and employee/contract status.",
        ))

    except Exception as error:
        logging.getLogger(__name__).error(
            "Operation failed: %s",
            type(error).__name__,
        )
        st.error(tr(
            "تعذر تنفيذ العملية. راجع إعدادات قاعدة البيانات.",
            "Operation failed. Check database configuration.",
        ))

    else:
        st.session_state.notice = True
        st.rerun()


def load(function, *args):
    try:
        return function(*args)

    except Exception as error:
        logging.getLogger(__name__).error(
            "Read failed: %s",
            type(error).__name__,
        )
        st.error(tr(
            "تعذر قراءة البيانات. تأكد من تنفيذ SQL "
            "وصحة Secrets.",
            "Could not load data. Check SQL setup and Secrets.",
        ))
        st.stop()


direction = "rtl" if st.session_state.lang == "ar" else "ltr"

st.markdown(
    f"""
    <style>
        .stApp {{
            direction: {direction};
        }}

        [data-testid="stSidebar"] {{
            width: 185px !important;
            min-width: 185px !important;
            max-width: 185px !important;
        }}

        [data-testid="stSidebar"] p {{
            font-size: 12px !important;
        }}

        [data-testid="stMainBlockContainer"] {{
            padding-top: 1.5rem;
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
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# الدخول: حساب مدير تجريبي من Secrets
# =========================================================

if not st.session_state.authenticated:
    _, center, _ = st.columns([1, 1.3, 1])

    with center:
        st.title("Enterprise Workspace")

        st.selectbox(
            "Language / اللغة",
            ["ar", "en"],
            index=0 if st.session_state.lang == "ar" else 1,
            key="language",
            on_change=change_language,
        )

        with st.form("login"):
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
            )

        if submitted:
            try:
                auth = st.secrets["auth"]

                valid_user = hmac.compare_digest(
                    username.strip().encode(),
                    str(auth["username"]).encode(),
                )

                valid_password = hmac.compare_digest(
                    password.encode(),
                    str(auth["password"]).encode(),
                )

                configured = bool(
                    str(auth["username"]).strip()
                    and str(auth["password"])
                )

            except Exception:
                st.error(
                    tr(
                        "أضف إعدادات [auth] في Secrets.",
                        "Add [auth] settings to Secrets.",
                    )
                )
                st.stop()

            if configured and valid_user and valid_password:
                st.session_state.authenticated = True
                st.session_state.actor = username.strip()
                st.rerun()
            else:
                st.error(
                    tr("بيانات غير صحيحة.", "Invalid credentials.")
                )

        st.caption(tr(
            "للاختبار الداخلي فقط. لا يوجد نظام مستخدمين "
            "متعدد أو حماية إنتاجية لتسجيل الدخول بعد.",
            "Internal testing only. Multi-user authentication "
            "and production login protections are not implemented.",
        ))

    st.stop()


actor = st.session_state.actor
companies = load(db.companies)


# =========================================================
# أول شركة
# =========================================================

if not companies:
    st.subheader(tr("إنشاء أول شركة", "Create first company"))

    with st.form("first_company"):
        company_name = st.text_input(
            tr("اسم الشركة", "Company name")
        )

        submit = st.form_submit_button(
            tr("إنشاء", "Create")
        )

    if submit:
        attempt(db.add_company, company_name, actor)

    st.button(tr("خروج", "Logout"), on_click=logout)
    st.stop()


# =========================================================
# الشريط العلوي
# =========================================================

company_names = {
    company["id"]: company["name"]
    for company in companies
}

if st.session_state.get("company_id") not in company_names:
    st.session_state.company_id = companies[0]["id"]


def changed_company():
    st.session_state.module = "home"
    st.session_state.hr_page = "Dashboard"


c1, c2, c3, c4, c5 = st.columns([1.2, 2, 1.5, 1, 0.8])

with c1:
    st.caption(tr("المستخدم", "User"))
    st.write(actor)

with c2:
    st.selectbox(
        tr("الشركة", "Company"),
        list(company_names),
        format_func=lambda key: company_names[key],
        key="company_id",
        on_change=changed_company,
    )

with c3:
    st.caption(tr("توقيت القاهرة", "Cairo time"))
    st.write(
        datetime.now(
            ZoneInfo("Africa/Cairo")
        ).strftime("%Y-%m-%d %H:%M")
    )

with c4:
    st.selectbox(
        "Language / اللغة",
        ["ar", "en"],
        index=0 if st.session_state.lang == "ar" else 1,
        key="language",
        on_change=change_language,
    )

with c5:
    st.button(
        tr("خروج", "Logout"),
        on_click=logout,
    )

st.divider()

if st.session_state.pop("notice", False):
    st.success(tr("تم تنفيذ العملية.", "Operation completed."))

company_id = st.session_state.company_id


# =========================================================
# القائمة الجانبية
# =========================================================

with st.sidebar:
    st.caption("Enterprise Workspace")

    st.button(
        tr("الرئيسية", "Home"),
        on_click=navigate,
        args=("home",),
        use_container_width=True,
    )

    st.button(
        tr("إدارة الشركة", "Company"),
        on_click=navigate,
        args=("company",),
        use_container_width=True,
    )

    st.button(
        tr("الموارد البشرية", "Human Resources"),
        on_click=navigate,
        args=("hr",),
        use_container_width=True,
    )

    if st.session_state.module == "hr":
               titles = {
            "Dashboard": tr("لوحة القسم", "Dashboard"),
            "Employees": tr("الموظفون", "Employees"),
            "Profile": tr("ملف الموظف", "Employee profile"),
            "Attendance": tr("الحضور والانصراف", "Attendance"),
            "Leaves": tr("الإجازات والمراجعة", "Leave & Review"),
        }

        st.radio(
            tr("صفحات القسم", "Module pages"),
            list(titles),
            format_func=lambda key: titles[key],
            key="hr_page",
        )

    st.button(
        tr("سجل العمليات", "Activity log"),
        on_click=navigate,
        args=("audit",),
        use_container_width=True,
    )


# =========================================================
# نموذج موظف متخصص
# =========================================================

def employee_form(departments, existing=None):
    department_map = {
        row["id"]: row["name"]
        for row in departments
    }

    if not departments:
        st.info(tr(
            "أضف إدارة من إدارة الشركة أولًا.",
            "Add a department from Company Management first.",
        ))
        return

    values = existing or {}

    form_key = (
        f"employee_{company_id}_"
        f"{values.get('id', 'new')}"
    )

    with st.form(form_key):
        c1, c2 = st.columns(2)

        with c1:
            code = st.text_input(
                tr("كود الموظف", "Employee code"),
                value=values.get("code", ""),
            )

            full_name = st.text_input(
                tr("الاسم الكامل", "Full name"),
                value=values.get("full_name", ""),
            )

            job_title = st.text_input(
                tr("المسمى الوظيفي", "Job title"),
                value=values.get("job_title", ""),
            )

            ids = list(department_map)

            selected_department = values.get(
                "department_id",
                ids[0],
            )

            department_id = st.selectbox(
                tr("الإدارة", "Department"),
                ids,
                index=(
                    ids.index(selected_department)
                    if selected_department in ids else 0
                ),
                format_func=lambda key: department_map[key],
            )

        with c2:
            phone = st.text_input(
                tr("الهاتف", "Phone"),
                value=values.get("phone", ""),
            )

            email = st.text_input(
                tr("البريد", "Email"),
                value=values.get("email", ""),
            )

            hire_date = st.date_input(
                tr("التعيين", "Hire date"),
                value=values.get("hire_date", date.today()),
            )

            status = st.selectbox(
                tr("الحالة", "Status"),
                ["active", "inactive"],
                index=(
                    1 if values.get("status") == "inactive" else 0
                ),
                format_func=lambda key: (
                    tr("نشط", "Active")
                    if key == "active"
                    else tr("غير نشط", "Inactive")
                ),
            )

        submitted = st.form_submit_button(
            tr("حفظ الموظف", "Save employee"),
            type="primary",
            use_container_width=True,
        )

    if submitted:
        attempt(
            db.save_employee,
            company_id,
            {
                "code": code,
                "full_name": full_name,
                "job_title": job_title,
                "department_id": department_id,
                "phone": phone,
                "email": email,
                "hire_date": hire_date,
                "status": status,
            },
            actor,
            existing,
        )


# =========================================================
# نموذج العقود
# =========================================================

def contract_panel(employee):
    st.caption(tr(
        "العقود هنا سجلات إدارية وليست مستندات قانونية "
        "معتمدة، ولا تنتج رواتب أو قيودًا تلقائيًا.",
        "Administrative contract records, not legally approved "
        "documents; no automatic payroll or accounting posting.",
    ))

    with st.expander(
        tr("إضافة عقد مسودة", "Add draft contract")
    ):
        with st.form(f"contract_{employee['id']}"):
            number = st.text_input(
                tr("رقم العقد", "Contract number")
            )

            start = st.date_input(
                tr("بداية العقد", "Start date"),
                value=date.today(),
            )

            fixed_term = st.checkbox(
                tr("له تاريخ انتهاء", "Has an end date")
            )

            end = st.date_input(
                tr("تاريخ الانتهاء إن وجد", "End date if applicable"),
                value=date.today(),
            )

            salary = st.number_input(
                tr("الراتب الأساسي", "Basic salary"),
                min_value=0.0,
                step=100.0,
            )

            currency = st.selectbox(
                tr("العملة", "Currency"),
                ["EGP", "USD", "EUR", "SAR", "AED"],
            )

            submitted = st.form_submit_button(
                tr("حفظ المسودة", "Save draft")
            )

        if submitted:
            attempt(
                db.add_contract,
                company_id,
                employee["id"],
                {
                    "contract_number": number,
                    "start_date": start,
                    "end_date": end if fixed_term else None,
                    "basic_salary": salary,
                    "currency": currency,
                },
                actor,
            )

    contracts = load(
        db.contracts,
        company_id,
        employee["id"],
    )

    if not contracts:
        st.info(tr("لا توجد عقود.", "No contracts."))
        return

    for contract in contracts:
        with st.container(border=True):
            st.write(
                f"{contract['contract_number']} "
                f"— {contract['status']}"
            )

            st.caption(
                f"{contract['start_date']} → "
                f"{contract['end_date'] or '—'}"
            )

            st.write(
                f"{contract['basic_salary']:,.2f} "
                f"{contract['currency']}"
            )

            if contract["status"] == "draft":
                if st.button(
                    tr("تفعيل العقد", "Activate contract"),
                    key=f"activate_{contract['id']}",
                ):
                    attempt(
                        db.transition_contract,
                        company_id,
                        employee["id"],
                        contract["id"],
                        "active",
                        actor,
                    )

            elif contract["status"] == "active":
                confirmed = st.checkbox(
                    tr("تأكيد إنهاء العقد", "Confirm ending contract"),
                    key=f"confirm_{contract['id']}",
                )

                if st.button(
                    tr("إنهاء العقد", "End contract"),
                    key=f"end_{contract['id']}",
                    disabled=not confirmed,
                ):
                    attempt(
                        db.transition_contract,
                        company_id,
                        employee["id"],
                        contract["id"],
                        "ended",
                        actor,
                    )


# =========================================================
# صفحات المنصة
# =========================================================

module = st.session_state.module

if module == "home":
    st.subheader(tr("مساحة العمل", "Workspace"))

    st.info(tr(
        "المتاح فعليًا الآن: إدارة الشركات والإدارات "
        "والموظفين وملفاتهم وعقودهم وسجل العمليات.",
        "Available: companies, departments, employees, "
        "employee profiles, contracts and activity log.",
    ))

    c1, c2 = st.columns(2)

    with c1:
        st.button(
            tr("إدارة الشركة", "Company Management"),
            key="home_company",
            use_container_width=True,
            on_click=navigate,
            args=("company",),
        )

    with c2:
        st.button(
            tr("الموارد البشرية", "Human Resources"),
            key="home_hr",
            use_container_width=True,
            on_click=navigate,
            args=("hr",),
        )


elif module == "company":
    st.subheader(tr("إدارة الشركة", "Company Management"))

    department_tab, company_tab = st.tabs([
        tr("الإدارات", "Departments"),
        tr("إضافة شركة", "Add company"),
    ])

    with department_tab:
        with st.form("department"):
            name = st.text_input(
                tr("اسم الإدارة", "Department name")
            )

            submitted = st.form_submit_button(
                tr("إضافة الإدارة", "Add department")
            )

        if submitted:
            attempt(
                db.add_department,
                company_id,
                name,
                actor,
            )

        rows = load(db.departments, company_id)

        if rows:
            st.dataframe(
                pd.DataFrame(rows)[["name"]],
                hide_index=True,
                use_container_width=True,
            )

    with company_tab:
        with st.form("additional_company"):
            name = st.text_input(
                tr("اسم الشركة", "Company name")
            )

            submitted = st.form_submit_button(
                tr("إضافة الشركة", "Add company")
            )

        if submitted:
            attempt(db.add_company, name, actor)


elif module == "hr":
    employees = load(db.employees, company_id)
    departments = load(db.departments, company_id)

    page = st.session_state.hr_page

    if page == "Dashboard":
        st.subheader(
            tr("لوحة الموارد البشرية", "HR Dashboard")
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            tr("إجمالي الموظفين", "Total employees"),
            len(employees),
        )

        c2.metric(
            tr("النشطون", "Active"),
            sum(
                employee["status"] == "active"
                for employee in employees
            ),
        )

        c3.metric(
            tr("الإدارات", "Departments"),
            len(departments),
        )

        if employees:
            counts = (
                pd.DataFrame(employees)["department"]
                .value_counts()
            )
            st.bar_chart(counts)

    elif page == "Employees":
        st.subheader(tr("الموظفون", "Employees"))

        add_tab, directory_tab = st.tabs([
            tr("إضافة موظف", "Add employee"),
            tr("دليل الموظفين", "Employee directory"),
        ])

        with add_tab:
            employee_form(departments)

        with directory_tab:
            search = st.text_input(
                tr("بحث بالاسم أو الكود", "Search name or code")
            ).strip().casefold()

            status_filter = st.selectbox(
                tr("الحالة", "Status"),
                ["all", "active", "inactive"],
            )

            department_options = {
                "all": tr("كل الإدارات", "All departments"),
                **{
                    department["id"]: department["name"]
                    for department in departments
                },
            }

            department_filter = st.selectbox(
                tr("الإدارة", "Department"),
                list(department_options),
                format_func=lambda key: department_options[key],
            )

            filtered = [
                employee
                for employee in employees
                if (
                    not search
                    or search in employee["full_name"].casefold()
                    or search in employee["code"].casefold()
                )
                and (
                    status_filter == "all"
                    or employee["status"] == status_filter
                )
                and (
                    department_filter == "all"
                    or employee["department_id"] == department_filter
                )
            ]

            if filtered:
                st.dataframe(
                    pd.DataFrame(filtered)[[
                        "code",
                        "full_name",
                        "job_title",
                        "department",
                        "status",
                        "hire_date",
                    ]],
                    hide_index=True,
                    use_container_width=True,
                )

                st.caption(
                    tr(
                        "للتعديل أو العقود افتح ملف الموظف "
                        "من القائمة الجانبية.",
                        "For editing or contracts, open Employee "
                        "profile from the sidebar.",
                    )
                )
            else:
                st.info(
                    tr("لا توجد نتائج.", "No results.")
                )

    elif page == "Profile":
        st.subheader(tr("ملف الموظف", "Employee Profile"))

        if not employees:
            st.info(
                tr("أضف موظفًا أولًا.", "Add an employee first.")
            )

        else:
            employee_map = {
                employee["id"]: employee
                for employee in employees
            }

            employee_id = st.selectbox(
                tr("اختيار الموظف", "Select employee"),
                list(employee_map),
                format_func=lambda key: (
                    f"{employee_map[key]['code']} — "
                    f"{employee_map[key]['full_name']}"
                ),
                key=f"profile_{company_id}",
            )

            employee = employee_map[employee_id]

            st.write(
                f"{employee['full_name']} | "
                f"{employee['job_title']}"
            )

            details_tab, contracts_tab = st.tabs([
                tr("البيانات والتعديل", "Details & edit"),
                tr("العقود", "Contracts"),
            ])

            with details_tab:
                employee_form(departments, employee)

            with contracts_tab:
                contract_panel(employee)
    elif page == "Attendance":
        hr_operations.attendance_page(
            company_id,
            actor,
            employees,
            load,
            attempt,
        )

    elif page == "Leaves":
        hr_operations.leaves_page(
            company_id,
            actor,
            employees,
            load,
            attempt,
        )

elif module == "audit":
    st.subheader(tr("سجل العمليات", "Activity Log"))

    events = load(db.audit_events, company_id)

    if events:
        st.dataframe(
            pd.DataFrame(events),
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(tr("لا توجد عمليات.", "No events."))


st.caption(tr(
    "نسخة تطوير داخلية. حساب المدير يرى كل الشركات. "
    "لا توجد صلاحيات تفصيلية أو رواتب أو حسابات مكتملة بعد.",
    "Internal development version. Administrator sees all companies. "
    "Granular permissions, payroll and accounting are not implemented.",
))
