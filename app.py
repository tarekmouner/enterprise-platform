import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Enterprise Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تصغير القائمة الجانبية
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            width: 200px !important;
            min-width: 200px !important;
        }
        [data-testid="stSidebar"] * {
            font-size: 12px !important;
        }
        [data-testid="stSidebar"] .stMarkdown {
            font-size: 12px !important;
        }
        [data-testid="stSidebar"] button {
            font-size: 12px !important;
            padding: 4px 6px !important;
        }
        [data-testid="stSidebar"] h3 {
            font-size: 13px !important;
            margin-bottom: 6px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

LANGS = {
    "ar": {
        "app_title": "منصة المؤسسة الذكية",
        "login_title": "تسجيل الدخول",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "login": "دخول",
        "logout": "خروج",
        "welcome": "مرحبًا",
        "welcome_sub": "اختر القسم الذي تريد العمل عليه",
        "company": "الشركة",
        "language": "اللغة",
        "no_access": "لا تملك صلاحية الوصول لهذا القسم",
        "modules": {
            "finance": "المالية",
            "sales": "المبيعات وCRM",
            "purchases": "المشتريات",
            "inventory": "المخازن",
            "production": "الإنتاج والتصنيع",
            "quality": "الجودة",
            "hr": "الموارد البشرية",
            "operations": "التشغيل والأسطول",
            "secretariat": "السكرتارية والأمن",
            "communication": "التواصل والتعاون",
            "digital": "القنوات الرقمية",
            "builder": "منشئ الأنظمة",
            "ai": "المساعد الذكي",
            "executive": "الإدارة العليا",
        },
    },
    "en": {
        "app_title": "Enterprise Smart Platform",
        "login_title": "Sign In",
        "username": "Username",
        "password": "Password",
        "login": "Sign In",
        "logout": "Sign Out",
        "welcome": "Welcome",
        "welcome_sub": "Choose the module you want to work with",
        "company": "Company",
        "language": "Language",
        "no_access": "You do not have access to this module",
        "modules": {
            "finance": "Finance",
            "sales": "Sales & CRM",
            "purchases": "Purchasing",
            "inventory": "Inventory",
            "production": "Production",
            "quality": "Quality",
            "hr": "Human Resources",
            "operations": "Operations & Fleet",
            "secretariat": "Secretariat & Security",
            "communication": "Communication & Collaboration",
            "digital": "Digital Channels",
            "builder": "System Builder",
            "ai": "AI Assistant",
            "executive": "Executive Management",
        },
    },
}

USERS = {
    "admin": {
        "password": "admin123",
        "name": "System Administrator",
        "company": "Enterprise Group",
        "modules": [
            "finance", "sales", "purchases", "inventory",
            "production", "quality", "hr", "operations",
            "secretariat", "communication", "digital",
            "builder", "ai", "executive",
        ],
    },
    "sales": {
        "password": "sales123",
        "name": "Sales Manager",
        "company": "Sales Company",
        "modules": [
            "sales", "inventory", "communication"
        ],
    },
    "warehouse": {
        "password": "warehouse123",
        "name": "Warehouse Manager",
        "company": "Operations Company",
        "modules": [
            "inventory", "purchases", "operations"
        ],
    },
    "finance": {
        "password": "finance123",
        "name": "Finance Manager",
        "company": "Finance Company",
        "modules": [
            "finance", "executive"
        ],
    },
    "hr": {
        "password": "hr123",
        "name": "HR Manager",
        "company": "Enterprise Group",
        "modules": [
            "hr", "communication"
        ],
    },
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = None

if "lang" not in st.session_state:
    st.session_state.lang = "ar"

if "employees" not in st.session_state:
    st.session_state.employees = []

if "attendance" not in st.session_state:
    st.session_state.attendance = []

if "leaves" not in st.session_state:
    st.session_state.leaves = []

T = LANGS[st.session_state.lang]


def login_page():
    st.markdown(
        f"""
        <div style="text-align:center; padding:40px 0 10px 0;">
            <h1 style="font-size:28px; margin-bottom:4px;">
                🏢 {T['app_title']}
            </h1>
            <p style="color:#666; font-size:14px;">
                {T['login_title']}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            username = st.text_input(
                T["username"],
                key="login_username"
            )

            password = st.text_input(
                T["password"],
                type="password",
                key="login_password"
            )

            lang_choice = st.selectbox(
                T["language"],
                options=["العربية", "English"],
                index=0
            )

            submitted = st.form_submit_button(
                T["login"],
                use_container_width=True,
                type="primary"
            )

            if submitted:
                user = USERS.get(username)

                if user and user["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.lang = (
                        "ar" if lang_choice == "العربية" else "en"
                    )
                    st.rerun()
                else:
                    st.error(
                        "بيانات الدخول غير صحيحة / Invalid credentials"
                    )


def top_bar():
    user = USERS[st.session_state.username]
    now = datetime.now()

    c1, c2, c3, c4, c5, c6 = st.columns(
        [0.7, 1.4, 1.6, 1.2, 1.4, 0.8],
        vertical_alignment="center"
    )

    with c1:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:34px;height:34px;border-radius:50%;
                            background:#2563eb;color:white;display:flex;
                            align-items:center;justify-content:center;
                            font-weight:bold;">
                    {user['name'][0]}
                </div>
                <div style="font-size:13px;font-weight:600;">
                    {user['name']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div style="font-size:13px;">
                <b>{T['company']}:</b> {user['company']}
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            """
            <div style="font-size:12px;color:#555;">
                🏢 Enterprise Platform
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div style="font-size:12px;color:#555;">
                📅 {now.strftime('%Y-%m-%d')}  
                🕒 {now.strftime('%H:%M')}
            </div>
            """,
            unsafe_allow_html=True
        )

    with c5:
        lang = st.selectbox(
            T["language"],
            options=["العربية", "English"],
            index=0 if st.session_state.lang == "ar" else 1,
            key="top_language",
            label_visibility="collapsed"
        )

        new_lang = "ar" if lang == "العربية" else "en"

        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

    with c6:
        if st.button(
            "🚪 " + T["logout"],
            use_container_width=True
        ):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

    st.divider()


def welcome_page():
    user = USERS[st.session_state.username]

    st.markdown(
        f"""
        <div style="padding:10px 0 20px 0;">
            <h2 style="margin-bottom:4px;">
                👋 {T['welcome']}، {user['name']}
            </h2>
            <p style="color:#666; font-size:14px;">
                {T['welcome_sub']}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    allowed = user["modules"]
    cols = st.columns(3)

    for i, module_key in enumerate(allowed):
        with cols[i % 3]:
            st.page_link(
                None,
                label=T["modules"][module_key],
                icon="📁",
                use_container_width=True,
                on_click=lambda m=module_key: st.query_params.update(
                    {"module": m}
                )
            )


def hr_dashboard():
    st.subheader("الموارد البشرية")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("عدد الموظفين", len(st.session_state.employees))

    with kpi2:
        st.metric("سجلات الحضور", len(st.session_state.attendance))

    with kpi3:
        st.metric("طلبات الإجازات", len(st.session_state.leaves))

    with kpi4:
        st.metric("نسبة الحضور", "96%")

    st.divider()

    tabs = st.tabs([
        "إضافة موظف",
        "قائمة الموظفين",
        "الحضور",
        "الإجازات",
        "الرواتب",
        "التقييمات",
        "التدريب",
        "نهاية الخدمة",
    ])

    with tabs[0]:
        add_employee()

    with tabs[1]:
        employees_list()

    with tabs[2]:
        attendance_page()

    with tabs[3]:
        leaves_page()

    with tabs[4]:
        payroll_page()

    with tabs[5]:
        evaluations_page()

    with tabs[6]:
        training_page()

    with tabs[7]:
        exit_page()


def add_employee():
    st.markdown("### إضافة موظف جديد")

    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("الاسم الكامل")
            job_title = st.text_input("المسمى الوظيفي")
            department = st.selectbox(
                "القسم",
                ["المبيعات", "المالية", "المخازن", "الإنتاج", "الجودة", "HR"]
            )
            branch = st.selectbox(
                "الفرع",
                ["القاهرة", "الإسكندرية", "المصنع"]
            )

        with col2:
            phone = st.text_input("رقم الهاتف")
            email = st.text_input("البريد الإلكتروني")
            hire_date = st.date_input("تاريخ التعيين")
            salary = st.number_input("الراتب الأساسي", min_value=0.0)

        submitted = st.form_submit_button(
            "حفظ الموظف",
            use_container_width=True,
            type="primary"
        )

        if submitted:
            if name and job_title:
                st.session_state.employees.append({
                    "name": name,
                    "job_title": job_title,
                    "department": department,
                    "branch": branch,
                    "phone": phone,
                    "email": email,
                    "hire_date": str(hire_date),
                    "salary": salary,
                })
                st.success("تم إضافة الموظف بنجاح")
            else:
                st.error("الاسم والمسمى الوظيفي مطلوبان")


def employees_list():
    st.markdown("### قائمة الموظفين")

    if not st.session_state.employees:
        st.info("لا يوجد موظفون بعد")
    else:
        for emp in st.session_state.employees:
            with st.expander(emp["name"]):
                st.write(f"المسمى الوظيفي: {emp['job_title']}")
                st.write(f"القسم: {emp['department']}")
                st.write(f"الفرع: {emp['branch']}")
                st.write(f"الهاتف: {emp['phone']}")
                st.write(f"البريد: {emp['email']}")
                st.write(f"تاريخ التعيين: {emp['hire_date']}")
                st.write(f"الراتب: {emp['salary']}")


def attendance_page():
    st.markdown("### تسجيل الحضور")

    with st.form("attendance_form"):
        employee_name = st.text_input("اسم الموظف")
        date = st.date_input("التاريخ")
        check_in = st.time_input("وقت الحضور")
        check_out = st.time_input("وقت الانصراف")

        submitted = st.form_submit_button(
            "حفظ الحضور",
            use_container_width=True
        )

        if submitted:
            st.session_state.attendance.append({
                "employee": employee_name,
                "date": str(date),
                "check_in": str(check_in),
                "check_out": str(check_out),
            })
            st.success("تم تسجيل الحضور")


def leaves_page():
    st.markdown("### طلب إجازة")

    with st.form("leave_form"):
        employee_name = st.text_input("اسم الموظف")
        leave_type = st.selectbox(
            "نوع الإجازة",
            ["سنوية", "مرضية", "بدون راتب", "طارئة"]
        )
        from_date = st.date_input("من تاريخ")
        to_date = st.date_input("إلى تاريخ")
        reason = st.text_area("السبب")

        submitted = st.form_submit_button(
            "إرسال الطلب",
            use_container_width=True
        )

        if submitted:
            st.session_state.leaves.append({
                "employee": employee_name,
                "type": leave_type,
                "from": str(from_date),
                "to": str(to_date),
                "reason": reason,
            })
            st.success("تم إرسال طلب الإجازة")


def payroll_page():
    st.markdown("### الرواتب")

    if not st.session_state.employees:
        st.info("لا يوجد موظفون بعد")
    else:
        for emp in st.session_state.employees:
            st.write(f"{emp['name']} - {emp['salary']}")


def evaluations_page():
    st.markdown("### التقييمات")

    st.info("صفحة التقييمات قيد التطوير")


def training_page():
    st.markdown("### التدريب")

    st.info("صفحة التدريب قيد التطوير")


def exit_page():
    st.markdown("### نهاية الخدمة")

    st.info("صفحة نهاية الخدمة قيد التطوير")


def module_dashboard(module_key):
    st.subheader(T["modules"][module_key])

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("KPI 1", "128", "+12%")

    with kpi2:
        st.metric("KPI 2", "42", "-3%")

    with kpi3:
        st.metric("KPI 3", "18", "+5%")

    with kpi4:
        st.metric("KPI 4", "96%", "+1%")

    st.divider()

    tabs = st.tabs([
        "إضافة / Add",
        "قائمة / List",
        "تقرير / Report",
        "إعدادات / Settings"
    ])

    with tabs[0]:
        st.info("صفحة الإضافة لهذا القسم")

    with tabs[1]:
        st.info("صفحة القائمة لهذا القسم")

    with tabs[2]:
        st.info("صفحة التقارير لهذا القسم")

    with tabs[3]:
        st.info("صفحة الإعدادات لهذا القسم")


def sidebar_menu():
    user = USERS[st.session_state.username]
    allowed = user["modules"]

    with st.sidebar:
        st.markdown("### 📚 الأقسام")

        for module_key in allowed:
            st.page_link(
                None,
                label=T["modules"][module_key],
                icon="📁",
                on_click=lambda m=module_key: st.query_params.update(
                    {"module": m}
                )
            )

        st.divider()

        st.markdown("### 📄 الصفحات")

        st.page_link(
            None,
            label="الرئيسية",
            icon="🏠",
            on_click=lambda: st.query_params.update({})
        )

        st.page_link(
            None,
            label="الإعدادات",
            icon="⚙️",
            on_click=lambda: st.query_params.update({"module": "settings"})
        )

        st.page_link(
            None,
            label="المستخدمون",
            icon="👥",
            on_click=lambda: st.query_params.update({"module": "users"})
        )

        st.page_link(
            None,
            label="الشركات",
            icon="🏢",
            on_click=lambda: st.query_params.update({"module": "companies"})
        )

        st.page_link(
            None,
            label="الفروع",
            icon="🏬",
            on_click=lambda: st.query_params.update({"module": "branches"})
        )

        st.page_link(
            None,
            label="المخازن",
            icon="📦",
            on_click=lambda: st.query_params.update({"module": "warehouses"})
        )


if not st.session_state.authenticated:
    login_page()

else:
    top_bar()
    sidebar_menu()

    query_params = st.query_params
    module = query_params.get("module", None)

    if module == "hr":
        hr_dashboard()

    elif module:
        user = USERS[st.session_state.username]

        if module in user["modules"]:
            module_dashboard(module)
        else:
            st.warning(T["no_access"])

    else:
        welcome_page()
