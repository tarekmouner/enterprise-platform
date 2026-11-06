import streamlit as st
import pandas as pd

from datetime import date
from uuid import uuid4


# =========================================================
# اللغة والبيانات المؤقتة
# =========================================================

def tr(arabic, english):
    return arabic if st.session_state.get("lang", "ar") == "ar" else english


def initialize():
    for key in [
        "hr_contracts",
        "hr_payroll_drafts",
        "hr_evaluations",
        "hr_training",
        "hr_exits",
    ]:
        if key not in st.session_state:
            st.session_state[key] = []


def records(key, company):
    return [
        row
        for row in st.session_state[key]
        if row["company"] == company
    ]


def employee_picker(employees, key):
    mapping = {
        employee["id"]: (
            f"{employee['code']} — {employee['name']}"
        )
        for employee in employees
    }

    return st.selectbox(
        tr("الموظف", "Employee"),
        options=list(mapping.keys()),
        format_func=lambda employee_id: mapping[employee_id],
        key=key,
    )


def employee_name(employees, employee_id):
    for employee in employees:
        if employee["id"] == employee_id:
            return employee["name"]

    return employee_id


def show_records(key, company, employees, columns):
    rows = []

    for record in records(key, company):
        display = {
            tr("الموظف", "Employee"): employee_name(
                employees,
                record["employee_id"],
            )
        }

        for field, arabic, english in columns:
            display[tr(arabic, english)] = record.get(field, "")

        rows.append(display)

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info(tr("لا توجد سجلات بعد.", "No records yet."))


def save_record(key, company, values):
    st.session_state[key].append({
        "id": uuid4().hex,
        "company": company,
        **values,
    })

    st.rerun()


# =========================================================
# العقود
# =========================================================

def contracts_page(company, employees):
    st.subheader(tr("عقود الموظفين", "Employee Contracts"))

    add_tab, list_tab = st.tabs([
        tr("إضافة عقد", "Add contract"),
        tr("قائمة العقود", "Contract list"),
    ])

    with add_tab:
        st.caption(
            tr(
                "تسجيل بيانات العقد فقط، وليس إنشاء عقد قانوني معتمد.",
                "Contract record only, not a legally approved contract.",
            )
        )

        with st.form("extended_contract_form"):
            employee_id = employee_picker(
                employees,
                "contract_employee",
            )

            number = st.text_input(
                tr("رقم العقد", "Contract number")
            )

            contract_type = st.selectbox(
                tr("نوع العقد", "Contract type"),
                ["fixed", "indefinite", "other"],
                format_func=lambda value: {
                    "fixed": tr("محدد المدة", "Fixed-term"),
                    "indefinite": tr("غير محدد المدة", "Indefinite"),
                    "other": tr("آخر", "Other"),
                }[value],
            )

            c1, c2 = st.columns(2)

            with c1:
                start = st.date_input(
                    tr("تاريخ البداية", "Start date")
                )

            with c2:
                end = st.date_input(
                    tr(
                        "تاريخ النهاية إن كان محدد المدة",
                        "End date for fixed-term contracts",
                    )
                )

            basic_salary = st.number_input(
                tr("الراتب الأساسي", "Basic salary"),
                min_value=0.0,
                step=100.0,
            )

            currency = st.text_input(
                tr("رمز العملة", "Currency code"),
                value="EGP",
            )

            notes = st.text_area(tr("ملاحظات", "Notes"))

            submitted = st.form_submit_button(
                tr("حفظ العقد", "Save contract"),
                type="primary",
                use_container_width=True,
            )

        if submitted:
            number = number.strip()
            currency = currency.strip().upper()

            duplicate = any(
                row["number"].casefold() == number.casefold()
                for row in records("hr_contracts", company)
            )

            if not number or not currency:
                st.error(
                    tr(
                        "رقم العقد والعملة مطلوبان.",
                        "Contract number and currency are required.",
                    )
                )

            elif duplicate:
                st.error(
                    tr(
                        "رقم العقد مستخدم بالفعل.",
                        "Contract number already exists.",
                    )
                )

            elif contract_type == "fixed" and end < start:
                st.error(
                    tr(
                        "تاريخ النهاية يجب ألا يسبق البداية.",
                        "End date cannot precede start date.",
                    )
                )

            else:
                save_record(
                    "hr_contracts",
                    company,
                    {
                        "employee_id": employee_id,
                        "number": number,
                        "type": contract_type,
                        "start": start.isoformat(),
                        "end": (
                            end.isoformat()
                            if contract_type == "fixed"
                            else ""
                        ),
                        "basic_salary": basic_salary,
                        "currency": currency,
                        "notes": notes.strip(),
                    },
                )

    with list_tab:
        show_records(
            "hr_contracts",
            company,
            employees,
            [
                ("number", "رقم العقد", "Contract number"),
                ("type", "نوع العقد", "Contract type"),
                ("start", "البداية", "Start"),
                ("end", "النهاية", "End"),
                ("basic_salary", "الأساسي", "Basic salary"),
                ("currency", "العملة", "Currency"),
                ("notes", "الملاحظات", "Notes"),
            ],
        )


# =========================================================
# مسودات الرواتب
# =========================================================

def payroll_page(company, employees):
    st.subheader(tr("مسودات الرواتب", "Payroll Drafts"))

    st.warning(
        tr(
            "حساب تجريبي يدوي فقط. لا يحسب الضرائب أو التأمينات "
            "أو رصيد الإجازات أو الاستقطاعات القانونية، "
            "ولا ينشئ قيدًا محاسبيًا أو تحويلًا بنكيًا.",
            "Manual demo calculation only. It does not calculate taxes, "
            "insurance, leave balances or statutory deductions, "
            "and does not create accounting entries or bank transfers.",
        )
    )

    add_tab, list_tab = st.tabs([
        tr("إضافة مسودة", "Add draft"),
        tr("قائمة المسودات", "Draft list"),
    ])

    with add_tab:
        with st.form("extended_payroll_form"):
            employee_id = employee_picker(
                employees,
                "payroll_employee",
            )

            c1, c2 = st.columns(2)

            with c1:
                year = st.number_input(
                    tr("السنة", "Year"),
                    min_value=2000,
                    max_value=2100,
                    value=date.today().year,
                    step=1,
                )

            with c2:
                month = st.selectbox(
                    tr("الشهر", "Month"),
                    list(range(1, 13)),
                    index=date.today().month - 1,
                )

            currency = st.text_input(
                tr("رمز العملة", "Currency code"),
                value="EGP",
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                basic = st.number_input(
                    tr("الأساسي", "Basic salary"),
                    min_value=0.0,
                    step=100.0,
                )

            with c2:
                additions = st.number_input(
                    tr("إضافات يدوية", "Manual additions"),
                    min_value=0.0,
                    step=100.0,
                )

            with c3:
                deductions = st.number_input(
                    tr("خصومات يدوية", "Manual deductions"),
                    min_value=0.0,
                    step=100.0,
                )

            notes = st.text_area(tr("ملاحظات", "Notes"))

            submitted = st.form_submit_button(
                tr("حفظ المسودة", "Save draft"),
                type="primary",
                use_container_width=True,
            )

        if submitted:
            period = f"{int(year):04d}-{month:02d}"
            net = round(basic + additions - deductions, 2)

            duplicate = any(
                row["employee_id"] == employee_id
                and row["period"] == period
                for row in records("hr_payroll_drafts", company)
            )

            if not currency.strip():
                st.error(
                    tr("العملة مطلوبة.", "Currency is required.")
                )

            elif duplicate:
                st.error(
                    tr(
                        "توجد مسودة لهذا الموظف في الشهر نفسه.",
                        "A draft already exists for this employee and month.",
                    )
                )

            elif net < 0:
                st.error(
                    tr(
                        "الخصومات تتجاوز الأساسي والإضافات.",
                        "Deductions exceed salary and additions.",
                    )
                )

            else:
                save_record(
                    "hr_payroll_drafts",
                    company,
                    {
                        "employee_id": employee_id,
                        "period": period,
                        "basic": basic,
                        "additions": additions,
                        "deductions": deductions,
                        "net": net,
                        "currency": currency.strip().upper(),
                        "notes": notes.strip(),
                    },
                )

    with list_tab:
        show_records(
            "hr_payroll_drafts",
            company,
            employees,
            [
                ("period", "الفترة", "Period"),
                ("basic", "الأساسي", "Basic"),
                ("additions", "الإضافات", "Additions"),
                ("deductions", "الخصومات", "Deductions"),
                ("net", "الصافي التجريبي", "Demo net"),
                ("currency", "العملة", "Currency"),
                ("notes", "الملاحظات", "Notes"),
            ],
        )


# =========================================================
# التقييمات
# =========================================================

def evaluations_page(company, employees):
    st.subheader(tr("تقييمات الموظفين", "Employee Evaluations"))

    add_tab, list_tab = st.tabs([
        tr("إضافة تقييم", "Add evaluation"),
        tr("قائمة التقييمات", "Evaluation list"),
    ])

    with add_tab:
        with st.form("extended_evaluation_form"):
            employee_id = employee_picker(
                employees,
                "evaluation_employee",
            )

            evaluation_date = st.date_input(
                tr("تاريخ التقييم", "Evaluation date")
            )

            evaluator = st.text_input(
                tr("اسم المقيّم", "Evaluator name")
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                performance = st.slider(
                    tr("الأداء", "Performance"),
                    1,
                    5,
                    3,
                )

            with c2:
                discipline = st.slider(
                    tr("الالتزام", "Discipline"),
                    1,
                    5,
                    3,
                )

            with c3:
                teamwork = st.slider(
                    tr("التعاون", "Teamwork"),
                    1,
                    5,
                    3,
                )

            notes = st.text_area(
                tr("ملاحظات وخطة تحسين", "Notes and improvement plan")
            )

            submitted = st.form_submit_button(
                tr("حفظ التقييم", "Save evaluation"),
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not evaluator.strip():
                st.error(
                    tr(
                        "اسم المقيّم مطلوب.",
                        "Evaluator name is required.",
                    )
                )
            else:
                save_record(
                    "hr_evaluations",
                    company,
                    {
                        "employee_id": employee_id,
                        "date": evaluation_date.isoformat(),
                        "evaluator": evaluator.strip(),
                        "performance": performance,
                        "discipline": discipline,
                        "teamwork": teamwork,
                        "average": round(
                            (performance + discipline + teamwork) / 3,
                            2,
                        ),
                        "notes": notes.strip(),
                    },
                )

    with list_tab:
        show_records(
            "hr_evaluations",
            company,
            employees,
            [
                ("date", "التاريخ", "Date"),
                ("evaluator", "المقيّم", "Evaluator"),
                ("performance", "الأداء", "Performance"),
                ("discipline", "الالتزام", "Discipline"),
                ("teamwork", "التعاون", "Teamwork"),
                ("average", "المتوسط من 5", "Average out of 5"),
                ("notes", "الملاحظات", "Notes"),
            ],
        )


# =========================================================
# التدريب
# =========================================================

def training_page(company, employees):
    st.subheader(tr("تدريب الموظفين", "Employee Training"))

    add_tab, list_tab = st.tabs([
        tr("إضافة تدريب", "Add training"),
        tr("قائمة التدريب", "Training list"),
    ])

    with add_tab:
        with st.form("extended_training_form"):
            employee_id = employee_picker(
                employees,
                "training_employee",
            )

            title = st.text_input(
                tr("اسم البرنامج", "Program name")
            )

            provider = st.text_input(
                tr("الجهة المقدمة", "Provider")
            )

            c1, c2 = st.columns(2)

            with c1:
                start = st.date_input(
                    tr("بداية التدريب", "Start date")
                )

            with c2:
                end = st.date_input(
                    tr("نهاية التدريب", "End date")
                )

            hours = st.number_input(
                tr("عدد الساعات", "Training hours"),
                min_value=0.0,
                step=1.0,
            )

            status = st.selectbox(
                tr("الحالة", "Status"),
                ["planned", "in_progress", "completed"],
                format_func=lambda value: {
                    "planned": tr("مخطط", "Planned"),
                    "in_progress": tr("جارٍ", "In progress"),
                    "completed": tr("مكتمل", "Completed"),
                }[value],
            )

            submitted = st.form_submit_button(
                tr("حفظ التدريب", "Save training"),
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not title.strip():
                st.error(
                    tr(
                        "اسم البرنامج مطلوب.",
                        "Program name is required.",
                    )
                )

            elif end < start:
                st.error(
                    tr(
                        "تاريخ النهاية يجب ألا يسبق البداية.",
                        "End date cannot precede start date.",
                    )
                )

            else:
                save_record(
                    "hr_training",
                    company,
                    {
                        "employee_id": employee_id,
                        "title": title.strip(),
                        "provider": provider.strip(),
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "hours": hours,
                        "status": status,
                    },
                )

    with list_tab:
        show_records(
            "hr_training",
            company,
            employees,
            [
                ("title", "البرنامج", "Program"),
                ("provider", "الجهة", "Provider"),
                ("start", "البداية", "Start"),
                ("end", "النهاية", "End"),
                ("hours", "الساعات", "Hours"),
                ("status", "الحالة", "Status"),
            ],
        )


# =========================================================
# نهاية الخدمة
# =========================================================

def exit_page(company, employees):
    st.subheader(
        tr("تسجيل نهاية الخدمة", "End of Employment Record")
    )

    st.warning(
        tr(
            "هذه الصفحة تسجل الواقعة فقط. لا تحسب المستحقات القانونية، "
            "ولا توقف حساب المستخدم، ولا تغيّر حالة الموظف تلقائيًا.",
            "This page records the event only. It does not calculate "
            "legal entitlements, disable accounts or automatically "
            "change employee status.",
        )
    )

    add_tab, list_tab = st.tabs([
        tr("إضافة سجل", "Add record"),
        tr("السجلات", "Records"),
    ])

    with add_tab:
        with st.form("extended_exit_form"):
            employee_id = employee_picker(
                employees,
                "exit_employee",
            )

            last_day = st.date_input(
                tr("آخر يوم عمل", "Last working day")
            )

            reason = st.text_area(
                tr("السبب والملاحظات", "Reason and notes")
            )

            acknowledged = st.checkbox(
                tr(
                    "أفهم أن هذا سجل تجريبي وليس تسوية نهائية.",
                    "I understand this is a demo record, "
                    "not a final settlement.",
                )
            )

            submitted = st.form_submit_button(
                tr("حفظ السجل", "Save record"),
                type="primary",
                use_container_width=True,
            )

        if submitted:
            employee = next(
                item
                for item in employees
                if item["id"] == employee_id
            )

            duplicate = any(
                row["employee_id"] == employee_id
                for row in records("hr_exits", company)
            )

            if not acknowledged:
                st.error(
                    tr(
                        "فعّل مربع الإقرار أولًا.",
                        "Select the acknowledgement first.",
                    )
                )

            elif not reason.strip():
                st.error(
                    tr("السبب مطلوب.", "Reason is required.")
                )

            elif last_day < date.fromisoformat(employee["hire_date"]):
                st.error(
                    tr(
                        "آخر يوم عمل لا يمكن أن يسبق تاريخ التعيين.",
                        "Last working day cannot precede hire date.",
                    )
                )

            elif duplicate:
                st.error(
                    tr(
                        "يوجد سجل نهاية خدمة لهذا الموظف بالفعل.",
                        "An end-of-employment record already exists.",
                    )
                )

            else:
                save_record(
                    "hr_exits",
                    company,
                    {
                        "employee_id": employee_id,
                        "last_day": last_day.isoformat(),
                        "reason": reason.strip(),
                    },
                )

    with list_tab:
        show_records(
            "hr_exits",
            company,
            employees,
            [
                ("last_day", "آخر يوم عمل", "Last working day"),
                ("reason", "السبب والملاحظات", "Reason and notes"),
            ],
        )


# =========================================================
# نقطة الاستدعاء من app.py
# =========================================================

def render_extended_hr(page, company, employees):
    initialize()

    if not employees:
        st.info(
            tr(
                "أضف موظفًا أولًا من صفحة الموظفين.",
                "Add an employee from the Employees page first.",
            )
        )
        return

    handlers = {
        "contracts": contracts_page,
        "payroll": payroll_page,
        "evaluations": evaluations_page,
        "training": training_page,
        "exit": exit_page,
    }

    handler = handlers.get(page)

    if handler is None:
        st.warning(
            tr(
                "هذه الصفحة غير متاحة.",
                "This page is unavailable.",
            )
        )
        return

    handler(company, employees)
