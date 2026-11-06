import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Enterprise Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
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
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = None

if "lang" not in st.session_state:
    st.session_state.lang = "ar"

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
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
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

        if st.button(
            T["login"],
            use_container_width=True,
            type="primary"
        ):
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


if not st.session_state.authenticated:
    login_page()

else:
    top_bar()
    sidebar_menu()

    query_params = st.query_params
    module = query_params.get("module", None)

    if module:
        user = USERS[st.session_state.username]

        if module in user["modules"]:
            module_dashboard(module)
        else:
            st.warning(T["no_access"])

    else:
        welcome_page()
