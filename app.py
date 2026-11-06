import streamlit as st
import pandas as pd

from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from uuid import uuid4


# =========================================================
# إعداد التطبيق
# =========================================================

st.set_page_config(
    page_title="Enterprise Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# الأقسام
# =========================================================

MODULES = {
    "company": ("إدارة الشركات والمنصة", "Companies & Platform"),
    "finance": ("المالية والحسابات", "Finance & Accounting"),
    "sales": ("المبيعات وCRM", "Sales & CRM"),
    "purchases": ("المشتريات والموردون", "Purchasing & Suppliers"),
    "inventory": ("المخازن والمخزون", "Warehouses & Inventory"),
    "production": ("الإنتاج والتصنيع", "Production & Manufacturing"),
    "quality": ("الجودة", "Quality"),
    "hr": ("الموارد البشرية والموظفون", "Human Resources"),
    "operations": ("التشغيل والأسطول", "Operations & Fleet"),
    "secretariat": ("السكرتارية والأمن", "Secretariat & Security"),
    "communication": ("التواصل والاجتماعات", "Chat & Meetings"),
    "digital": ("المواقع والمتاجر", "Websites & Stores"),
    "projects": ("المشروعات والمهام", "Projects & Tasks"),
    "documents": ("المستندات والأرشفة", "Documents & Archive"),
    "builder": ("منشئ الأنظمة", "System Builder"),
    "ai": ("المساعد الذكي", "AI Assistant"),
    "executive": ("الإدارة العليا", "Executive Management"),
    "governance": ("الحوكمة والتكاملات", "Governance & Integrations"),
}

HR_PAGES = {
    "dashboard": ("لوحة الموارد البشرية", "HR Dashboard"),
    "employees": ("الموظفون", "Employees"),
    "contracts": ("العقود", "Contracts"),
    "attendance": ("الحضور والانصراف", "Attendance"),
    "leaves": ("الإجازات", "Leave Requests"),
    "payroll": ("الرواتب", "Payroll"),
    "evaluations": ("التقييمات", "Evaluations"),
    "training": ("التدريب", "Training"),
    "exit": ("نهاية الخدمة", "End of Employment"),
}


# =========================================================
# حسابات تجريبية فقط
# لا تستخدم كلمات مرور حقيقية داخل المستودع
# =========================================================

USERS = {
    "admin": {
        "password": "admin123",
        "name": ("مدير النظام", "System Administrator"),
        "company": ("مجموعة المؤسسة", "Enterprise Group"),
        "modules": list(MODULES.keys()),
    },
    "hr": {
        "password": "hr123",
        "name": ("مدير الموارد البشرية", "HR Manager"),
        "company": ("مجموعة المؤسسة", "Enterprise Group"),
        "modules": ["hr", "communication"],
    },
    "sales": {
        "password": "sales123",
        "name": ("مدير المبيعات", "Sales Manager"),
        "company": ("شركة المبيعات", "Sales Company"),
        "modules": ["sales", "inventory", "communication"],
    },
    "warehouse": {
        "password": "warehouse123",
        "name": ("مدير المخازن", "Warehouse Manager"),
        "company": ("شركة التشغيل", "Operations Company"),
        "modules": ["inventory", "purchases", "operations"],
    },
    "finance": {
        "password": "finance123",
        "name": ("المدير المالي", "Finance Manager"),
        "company": ("الشركة المالية", "Finance Company"),
        "modules": ["finance", "executive"],
    },
}


# =========================================================
# تهيئة الجلسة
# =========================================================

DEFAULTS = {
    "authenticated": False,
    "username": None,
    "lang": "ar",
    "module": None,
    "hr_page": "dashboard",
    "employees": [],
    "attendance": [],
    "leaves": [],
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        if isinstance(value, list):
            st.session_state[key] = value.copy()
        else:
            st.session_state[key] = value


def tr(arabic, english):
    return arabic if st.session_state.lang == "ar" else english


def translated(value):
    return tr(value[0], value[1])


# =========================================================
# تصميم الواجهة
# ملاحظة: محددات CSS الداخلية قد تحتاج تحديثًا
# عند تغيير إصدار Streamlit
# =========================================================

direction = "rtl" if st.session_state.lang == "ar" else "ltr"

st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 180px !important;
            min-width: 180px !important;
            max-width: 180px !important;
        }}

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] button {{
            font-size: 12px !important;
        }}

        [data-testid="stSidebar"] button {{
            min-height: 32px;
            padding: 4px 8px !important;
        }}

        [data-testid="stMainBlockContainer"] {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
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

        p, label {{
            font-size: 14px;
        }}

        .brand {{
            text-align: center;
            padding: 16px 0;
        }}

        .brand-mark {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 58px;
            height: 58px;
            border-radius: 16px;
            background: #2563eb;
            color: white;
            font-size: 24px;
            font-weight: 700;
            direction: ltr;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# التنقل والحساب
# =========================================================

def open_module(module_key):
    st.session_state.module = module_key
    st.session_state.hr_page = "dashboard"


def logout():
    # مسح الجلسة يمنع انتقال بيانات HR المؤقتة
    # إلى مستخدم آخر عند الدخول من نفس الجلسة
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def change_language():
    st.session_state.lang = st.session_state.header_language


def current_user():
    return USERS.get(st.session_state.username)


def company_employees():
    user = current_user()
    if user is None:
        return []

    return [
        employee
        for employee in st.session_state.employees
        if employee["company"] == user["company"][1]
    ]


def company_records(key):
    user = current_user()
    if user is None:
        return []

    return [
        record
        for record in st.session_state[key]
        if record["company"] == user["company"][1]
    ]


# =========================================================
# تسجيل الدخول
# =========================================================

def login_page():
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">EP</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<h2 style='text-align:center'>"
        f"{tr('منصة المؤسسة الذكية', 'Enterprise Smart Platform')}"
        f"</h2>",
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.5, 1])

    with center:
        with st.form("login_form"):
            username = st.text_input(
                tr("اسم المستخدم", "Username"),
                key="login_username",
            )

            password = st.text_input(
                tr("كلمة المرور", "Password"),
                type="password",
                key="login_password",
            )

            language = st.selectbox(
                "اللغة / Language",
                ["ar", "en"],
                format_func=lambda value: (
                    "العربية" if value == "ar" else "English"
                ),
                index=0 if st.session_state.lang == "ar" else 1,
            )

            submitted = st.form_submit_button(
                tr("تسجيل الدخول", "Sign in"),
                type="primary",
                use_container_width=True,
            )

        if submitted:
            username = username.strip()
            user = USERS.get(username)

            if user is not None and user["password"] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.lang = language
                st.session_state.module = None
                st.session_state.hr_page = "dashboard"
                st.rerun()
            else:
                st.error(
                    tr(
                        "اسم المستخدم أو كلمة المرور غير صحيحة.",
                        "Incorrect username or password.",
                    )
                )

        st.caption(
            tr(
                "نسخة تجريبية — لا تدخل بيانات شخصية أو مالية حقيقية.",
                "Demo version — do not enter real personal or financial data.",
            )
        )


# =========================================================
# الشريط العلوي
# =========================================================

def top_bar():
    user = current_user()
    now = datetime.now(ZoneInfo("Africa/Cairo"))

    c1, c2, c3, c4, c5 = st.columns(
        [2, 2, 1.6, 1.2, 1],
        vertical_alignment="center",
    )

    with c1:
        st.caption(tr("المستخدم", "User"))
        st.write(translated(user["name"]))

    with c2:
        st.caption(tr("الشركة الحالية", "Current company"))
        st.write(translated(user["company"]))

    with c3:
        st.caption(tr("توقيت القاهرة", "Cairo time"))
        st.write(now.strftime("%Y-%m-%d | %H:%M"))

    with c4:
        st.selectbox(
            "اللغة / Language",
            ["ar", "en"],
            index=0 if st.session_state.lang == "ar" else 1,
            format_func=lambda value: (
                "العربية" if value == "ar" else "English"
            ),
            key="header_language",
            on_change=change_language,
        )

    with c5:
        st.button(
            tr("خروج", "Sign out"),
            key="logout_button",
            on_click=logout,
            use_container_width=True,
        )

    st.divider()


# =========================================================
# القائمة الجانبية
# =========================================================

def sidebar_menu():
    user = current_user()
    module = st.session_state.module

    with st.sidebar:
        st.caption("Enterprise Platform")

        st.button(
            tr("كل الأقسام", "All modules"),
            key="sidebar_home",
            use_container_width=True,
            on_click=open_module,
            args=(None,),
        )

        if module == "hr":
            st.markdown(
                f"### {tr('الموارد البشرية', 'Human Resources')}"
            )

            st.radio(
                tr("صفحات القسم", "Module pages"),
                options=list(HR_PAGES.keys()),
                format_func=lambda key: translated(HR_PAGES[key]),
                key="hr_page",
                label_visibility="collapsed",
            )

        elif module in MODULES:
            st.markdown(
                f"### {translated(MODULES[module])}"
            )
            st.caption(
                tr(
                    "صفحات هذا القسم لم تُبنَ بعد.",
                    "Pages for this module are not implemented yet.",
                )
            )

        st.divider()

        with st.expander(tr("تبديل القسم", "Switch module")):
            for module_key in user["modules"]:
                st.button(
                    translated(MODULES[module_key]),
                    key=f"sidebar_module_{module_key}",
                    use_container_width=True,
                    on_click=open_module,
                    args=(module_key,),
                )


# =========================================================
# الصفحة الترحيبية
# =========================================================

def welcome_page():
    user = current_user()

    st.subheader(
        f"{tr('مرحبًا', 'Welcome')}، "
        f"{translated(user['name'])}"
    )

    st.caption(
        tr(
            "اختر القسم الذي تريد العمل عليه.",
            "Choose the module you want to work with.",
        )
    )

    columns = st.columns(3)

    for index, module_key in enumerate(user["modules"]):
        with columns[index % 3]:
            st.button(
                translated(MODULES[module_key]),
                key=f"welcome_module_{module_key}",
                use_container_width=True,
                on_click=open_module,
                args=(module_key,),
            )


# =========================================================
# أدوات الموارد البشرية
# =========================================================

def employee_options(key):
    employees = company_employees()

    if not employees:
        st.info(
            tr(
                "أضف موظفًا أولًا من صفحة الموظفين.",
                "Add an employee from the Employees page first.",
            )
        )
        return None

    names = {
        employee["id"]: (
            f"{employee['code']} — {employee['name']}"
        )
        for employee in employees
    }

    return st.selectbox(
        tr("الموظف", "Employee"),
        options=list(names.keys()),
        format_func=lambda employee_id: names[employee_id],
        key=key,
    )


def employee_name(employee_id):
    for employee in company_employees():
        if employee["id"] == employee_id:
            return employee["name"]
    return employee_id


def show_table(rows):
    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(tr("لا توجد سجلات بعد.", "No records yet."))


# =========================================================
# لوحة HR
# =========================================================

def hr_dashboard():
    employees = company_employees()
    attendance = company_records("attendance")
    leaves = company_records("leaves")

    st.subheader(
        tr("لوحة الموارد البشرية", "HR Dashboard")
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(tr("الموظفون", "Employees"), len(employees))
    c2.metric(
        tr("سجلات الحضور", "Attendance records"),
        len(attendance),
    )
    c3.metric(
        tr("طلبات الإجازة", "Leave requests"),
        len(leaves),
    )
    c4.metric(
        tr("طلبات معلقة", "Pending requests"),
        sum(row["status"] == "pending" for row in leaves),
    )

    st.divider()

    if employees:
        counts = (
            pd.DataFrame(employees)["department"]
            .value_counts()
            .rename(tr("عدد الموظفين", "Employee count"))
        )

        st.write(
            tr(
                "توزيع الموظفين حسب القسم",
                "Employees by department",
            )
        )
        st.bar_chart(counts)
    else:
        st.info(
            tr(
                "اختر الموظفين من القائمة الجانبية لإضافة أول موظف.",
                "Select Employees in the sidebar to add your first employee.",
            )
        )


# =========================================================
# الموظفون
# =========================================================

def employees_page():
    st.subheader(tr("الموظفون", "Employees"))

    add_tab, list_tab = st.tabs([
        tr("إضافة موظف", "Add employee"),
        tr("قائمة الموظفين", "Employee list"),
    ])

    with add_tab:
        with st.form("employee_form", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                code = st.text_input(
                    tr("كود الموظف", "Employee code")
                )
                name = st.text_input(
                    tr("الاسم الكامل", "Full name")
                )
                job = st.text_input(
                    tr("المسمى الوظيفي", "Job title")
                )
                department = st.selectbox(
                    tr("القسم", "Department"),
                    options=list(MODULES.keys()),
                    format_func=lambda key: translated(MODULES[key]),
                )

            with c2:
                branch = st.text_input(
                    tr("الفرع", "Branch")
                )
                phone = st.text_input(
                    tr("الهاتف", "Phone")
                )
                email = st.text_input(
                    tr("البريد الإلكتروني", "Email")
                )
                hire_date = st.date_input(
                    tr("تاريخ التعيين", "Hire date"),
                    value=date.today(),
                )

            submitted = st.form_submit_button(
                tr("حفظ الموظف", "Save employee"),
                type="primary",
                use_container_width=True,
            )

        if submitted:
            code = code.strip()
            name = name.strip()
            job = job.strip()

            existing_codes = {
                employee["code"].casefold()
                for employee in company_employees()
            }

            if not code or not name or not job:
                st.error(
                    tr(
                        "الكود والاسم والمسمى الوظيفي مطلوبة.",
                        "Code, name and job title are required.",
                    )
                )

            elif code.casefold() in existing_codes:
                st.error(
                    tr(
                        "كود الموظف مستخدم بالفعل.",
                        "Employee code already exists.",
                    )
                )

            else:
                st.session_state.employees.append({
                    "id": uuid4().hex,
                    "company": current_user()["company"][1],
                    "code": code,
                    "name": name,
                    "job": job,
                    "department": department,
                    "branch": branch.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "hire_date": hire_date.isoformat(),
                })

                st.success(
                    tr(
                        "تم حفظ الموظف في الجلسة الحالية.",
                        "Employee saved in the current session.",
                    )
                )
                st.rerun()

    with list_tab:
        search = st.text_input(
            tr("بحث بالاسم أو الكود", "Search name or code"),
            key="employee_search",
        ).strip().casefold()

        rows = []

        for employee in company_employees():
            if (
                search
                and search not in employee["name"].casefold()
                and search not in employee["code"].casefold()
            ):
                continue

            rows.append({
                tr("الكود", "Code"): employee["code"],
                tr("الاسم", "Name"): employee["name"],
                tr("الوظيفة", "Job"): employee["job"],
                tr("القسم", "Department"): translated(
                    MODULES[employee["department"]]
                ),
                tr("الفرع", "Branch"): employee["branch"],
                tr("الهاتف", "Phone"): employee["phone"],
                tr("البريد", "Email"): employee["email"],
                tr("التعيين", "Hire date"): employee["hire_date"],
            })

        show_table(rows)


# =========================================================
# الحضور والانصراف
# =========================================================

def attendance_page():
    st.subheader(
        tr("الحضور والانصراف", "Attendance")
    )

    add_tab, list_tab = st.tabs([
        tr("إضافة سجل", "Add record"),
        tr("سجل الحضور", "Attendance records"),
    ])

    with add_tab:
        if company_employees():
            with st.form("attendance_form"):
                employee_id = employee_options(
                    "attendance_employee"
                )

                work_date = st.date_input(
                    tr("التاريخ", "Date"),
                    value=date.today(),
                )

                c1, c2 = st.columns(2)

                with c1:
                    check_in = st.time_input(
                        tr("الحضور", "Check-in"),
                        value=time(9, 0),
                    )

                with c2:
                    check_out = st.time_input(
                        tr("الانصراف", "Check-out"),
                        value=time(17, 0),
                    )

                submitted = st.form_submit_button(
                    tr("حفظ السجل", "Save record"),
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                duplicate = any(
                    row["employee_id"] == employee_id
                    and row["date"] == work_date.isoformat()
                    for row in company_records("attendance")
                )

                if check_out <= check_in:
                    st.error(
                        tr(
                            "وقت الانصراف يجب أن يكون بعد الحضور. "
                            "النموذج الحالي يدعم وردية داخل اليوم نفسه فقط.",
                            "Check-out must follow check-in. "
                            "This form supports same-day shifts only.",
                        )
                    )

                elif duplicate:
                    st.error(
                        tr(
                            "يوجد سجل لهذا الموظف في التاريخ نفسه.",
                            "A record already exists for this employee and date.",
                        )
                    )

                else:
                    duration = (
                        datetime.combine(work_date, check_out)
                        - datetime.combine(work_date, check_in)
                    ).total_seconds() / 3600

                    st.session_state.attendance.append({
                        "company": current_user()["company"][1],
                        "employee_id": employee_id,
                        "date": work_date.isoformat(),
                        "check_in": check_in.strftime("%H:%M"),
                        "check_out": check_out.strftime("%H:%M"),
                        "hours": round(duration, 2),
                    })

                    st.rerun()
        else:
            st.info(
                tr(
                    "أضف موظفًا أولًا.",
                    "Add an employee first.",
                )
            )

    with list_tab:
        rows = [
            {
                tr("الموظف", "Employee"): employee_name(
                    row["employee_id"]
                ),
                tr("التاريخ", "Date"): row["date"],
                tr("الحضور", "Check-in"): row["check_in"],
                tr("الانصراف", "Check-out"): row["check_out"],
                tr("الساعات", "Hours"): row["hours"],
            }
            for row in company_records("attendance")
        ]

        show_table(rows)


# =========================================================
# الإجازات
# =========================================================

def leaves_page():
    st.subheader(tr("الإجازات", "Leave Requests"))

    add_tab, list_tab = st.tabs([
        tr("طلب إجازة", "New request"),
        tr("قائمة الطلبات", "Request list"),
    ])

    leave_types = {
        "annual": ("سنوية", "Annual"),
        "sick": ("مرضية", "Sick"),
        "unpaid": ("بدون راتب", "Unpaid"),
        "emergency": ("طارئة", "Emergency"),
    }

    with add_tab:
        if company_employees():
            with st.form("leave_form"):
                employee_id = employee_options(
                    "leave_employee"
                )

                leave_type = st.selectbox(
                    tr("نوع الإجازة", "Leave type"),
                    options=list(leave_types.keys()),
                    format_func=lambda key: translated(leave_types[key]),
                )

                c1, c2 = st.columns(2)

                with c1:
                    start = st.date_input(
                        tr("من تاريخ", "Start date"),
                        value=date.today(),
                    )

                with c2:
                    end = st.date_input(
                        tr("إلى تاريخ", "End date"),
                        value=date.today(),
                    )

                reason = st.text_area(
                    tr("السبب", "Reason")
                )

                submitted = st.form_submit_button(
                    tr("إرسال الطلب", "Submit request"),
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if end < start:
                    st.error(
                        tr(
                            "تاريخ النهاية لا يمكن أن يسبق البداية.",
                            "End date cannot precede start date.",
                        )
                    )
                else:
                    st.session_state.leaves.append({
                        "id": uuid4().hex,
                        "company": current_user()["company"][1],
                        "employee_id": employee_id,
                        "type": leave_type,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "days": (end - start).days + 1,
                        "reason": reason.strip(),
                        "status": "pending",
                    })

                    st.rerun()
        else:
            st.info(
                tr(
                    "أضف موظفًا أولًا.",
                    "Add an employee first.",
                )
            )

    with list_tab:
        rows = [
            {
                tr("الموظف", "Employee"): employee_name(
                    row["employee_id"]
                ),
                tr("النوع", "Type"): translated(
                    leave_types[row["type"]]
                ),
                tr("من", "From"): row["start"],
                tr("إلى", "To"): row["end"],
                tr("أيام تقويمية", "Calendar days"): row["days"],
                tr("السبب", "Reason"): row["reason"],
                tr("الحالة", "Status"): tr(
                    "بانتظار المراجعة", "Pending review"
                ),
            }
            for row in company_records("leaves")
        ]

        show_table(rows)

        st.caption(
            tr(
                "حساب الأيام هنا تقويمي فقط؛ لا يخصم العطلات "
                "ولا يتحقق من رصيد الإجازات بعد.",
                "Days are calendar days; holidays and leave "
                "balances are not checked yet.",
            )
        )


# =========================================================
# صفحات لم تُنفذ بعد
# =========================================================

def hr_placeholder(page_key):
    st.subheader(translated(HR_PAGES[page_key]))

    st.info(
        tr(
            "هذه صفحة محجوزة ضمن الهيكل، ولم تُنفذ وظائفها بعد.",
            "This page is reserved in the structure; "
            "its functionality is not implemented yet.",
        )
    )


def render_hr():
    page = st.session_state.hr_page

    handlers = {
        "dashboard": hr_dashboard,
        "employees": employees_page,
        "attendance": attendance_page,
        "leaves": leaves_page,
    }

    if page in handlers:
        handlers[page]()
    else:
        hr_placeholder(page)


def module_placeholder(module_key):
    st.subheader(translated(MODULES[module_key]))

    st.info(
        tr(
            "هذا القسم موجود في الهيكل العام فقط. "
            "صفحاته وعملياته لم تُنفذ بعد.",
            "This module is currently a structural placeholder. "
            "Its pages and operations are not implemented yet.",
        )
    )


# =========================================================
# تشغيل التطبيق مع التحقق من الصلاحيات
# =========================================================

if not st.session_state.authenticated:
    login_page()

else:
    user = current_user()

    if user is None:
        logout()
        st.rerun()

    if (
        st.session_state.module is not None
        and st.session_state.module not in user["modules"]
    ):
        st.error(
            tr(
                "لا تملك صلاحية الوصول إلى هذا القسم.",
                "You do not have access to this module.",
            )
        )
        st.stop()

    top_bar()
    sidebar_menu()

    st.caption(
        tr(
            "نسخة تجريبية — البيانات مؤقتة وتُمسح عند تسجيل الخروج "
            "أو انتهاء الجلسة. الوقت يتحدث عند تفاعل الصفحة.",
            "Demo — data is temporary and clears on logout "
            "or session end. Time updates on page interaction.",
        )
    )

    module = st.session_state.module

    if module is None:
        welcome_page()

    elif module == "hr":
        render_hr()

    else:
        module_placeholder(module)
