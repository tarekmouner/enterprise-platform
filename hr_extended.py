from datetime import date, time

import pandas as pd
import streamlit as st

import database as db


def tr(arabic, english):
    return (
        arabic
        if st.session_state.get("lang", "ar") == "ar"
        else english
    )


def employee_selector(employees, key):
    active = [
        employee
        for employee in employees
        if employee["status"] == "active"
    ]

    if not active:
        return None

    employee_map = {
        employee["id"]: employee
        for employee in active
    }

    return st.selectbox(
        tr("الموظف", "Employee"),
        options=list(employee_map),
        format_func=lambda employee_id: (
            f"{employee_map[employee_id]['code']} — "
            f"{employee_map[employee_id]['full_name']}"
        ),
        key=key,
    )


def attendance_page(company_id, actor, employees, load, attempt):
    st.subheader(
        tr("الحضور والانصراف", "Attendance")
    )

    st.caption(
        tr(
            "تسجيل يدوي لوردية داخل اليوم نفسه. "
            "مدة التواجد ليست ساعات أجر معتمدة؛ "
            "لا يتم خصم الاستراحات أو حساب التأخير.",
            "Manual same-day shift entry. Presence duration "
            "is not approved paid time; breaks and lateness "
            "are not calculated.",
        )
    )

    add_tab, list_tab = st.tabs([
        tr("تسجيل حضور", "Add attendance"),
        tr("سجل الحضور", "Attendance register"),
    ])

    with add_tab:
        active = [
            employee
            for employee in employees
            if employee["status"] == "active"
        ]

        if not active:
            st.info(
                tr(
                    "أضف موظفًا نشطًا أولًا.",
                    "Add an active employee first.",
                )
            )

        else:
            with st.form(f"attendance_form_{company_id}"):
                employee_id = employee_selector(
                    employees,
                    f"attendance_employee_{company_id}",
                )

                work_date = st.date_input(
                    tr("يوم العمل", "Work date"),
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

                notes = st.text_area(
                    tr("ملاحظات", "Notes")
                )

                submitted = st.form_submit_button(
                    tr("حفظ الحضور", "Save attendance"),
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if check_out <= check_in:
                    st.error(
                        tr(
                            "الانصراف يجب أن يكون بعد الحضور. "
                            "الورديات الليلية ستُضاف لاحقًا.",
                            "Check-out must follow check-in. "
                            "Overnight shifts are not supported yet.",
                        )
                    )

                else:
                    attempt(
                        db.add_attendance,
                        company_id,
                        employee_id,
                        work_date,
                        check_in,
                        check_out,
                        notes,
                        actor,
                    )

    with list_tab:
        records = load(
            db.attendance_records,
            company_id,
        )

        search = st.text_input(
            tr("بحث بالاسم أو الكود", "Search name or code"),
            key=f"attendance_search_{company_id}",
        ).strip().casefold()

        rows = []

        for record in records:
            if search and not (
                search in record["employee_name"].casefold()
                or search in record["employee_code"].casefold()
            ):
                continue

            rows.append({
                tr("الكود", "Code"): record["employee_code"],
                tr("الموظف", "Employee"): record["employee_name"],
                tr("اليوم", "Date"): record["work_date"],
                tr("الحضور", "Check-in"): str(record["check_in"]),
                tr("الانصراف", "Check-out"): str(record["check_out"]),
                tr("مدة التواجد بالساعات", "Presence hours"):
                    float(record["presence_hours"]),
                tr("ملاحظات", "Notes"): record["notes"],
            })

        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info(
                tr("لا توجد سجلات مطابقة.", "No matching records.")
            )


def leaves_page(company_id, actor, employees, load, attempt):
    st.subheader(
        tr("طلبات الإجازة", "Leave Requests")
    )

    st.warning(
        tr(
            "الأيام المعروضة تقويمية وتشمل العطلات. "
            "لا توجد أرصدة إجازات أو تحقق من الاستحقاق القانوني "
            "في هذه المرحلة.",
            "Displayed days are calendar days including holidays. "
            "Leave balances and legal entitlement checks "
            "are not implemented yet.",
        )
    )

    types = {
        "annual": tr("سنوية", "Annual"),
        "sick": tr("مرضية", "Sick"),
        "unpaid": tr("بدون راتب", "Unpaid"),
        "other": tr("أخرى", "Other"),
    }

    statuses = {
        "pending": tr("بانتظار المراجعة", "Pending review"),
        "approved": tr("معتمد", "Approved"),
        "rejected": tr("مرفوض", "Rejected"),
    }

    add_tab, review_tab, list_tab = st.tabs([
        tr("طلب جديد", "New request"),
        tr("المراجعة", "Review"),
        tr("كل الطلبات", "All requests"),
    ])

    with add_tab:
        active = [
            employee
            for employee in employees
            if employee["status"] == "active"
        ]

        if not active:
            st.info(
                tr(
                    "لا يوجد موظفون نشطون.",
                    "No active employees.",
                )
            )

        else:
            with st.form(f"leave_form_{company_id}"):
                employee_id = employee_selector(
                    employees,
                    f"leave_employee_{company_id}",
                )

                leave_type = st.selectbox(
                    tr("نوع الإجازة", "Leave type"),
                    options=list(types),
                    format_func=lambda key: types[key],
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
                    tr("إرسال للمراجعة", "Submit for review"),
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if end < start:
                    st.error(
                        tr(
                            "نهاية الإجازة تسبق بدايتها.",
                            "End date precedes start date.",
                        )
                    )

                elif not reason.strip():
                    st.error(
                        tr("أدخل السبب.", "Enter a reason.")
                    )

                else:
                    selected_employee = next(
                        employee
                        for employee in employees
                        if employee["id"] == employee_id
                    )

                    if start < selected_employee["hire_date"]:
                        st.error(
                            tr(
                                "الإجازة لا يمكن أن تبدأ قبل التعيين.",
                                "Leave cannot start before hire date.",
                            )
                        )

                    else:
                        existing = load(
                            db.leave_requests,
                            company_id,
                        )

                        overlap = any(
                            row["employee_id"] == employee_id
                            and row["status"] in {"pending", "approved"}
                            and row["start_date"] <= end
                            and row["end_date"] >= start
                            for row in existing
                        )

                        if overlap:
                            st.error(
                                tr(
                                    "يوجد طلب متداخل لهذا الموظف.",
                                    "An overlapping request exists.",
                                )
                            )

                        else:
                            attempt(
                                db.add_leave_request,
                                company_id,
                                employee_id,
                                leave_type,
                                start,
                                end,
                                reason,
                                actor,
                            )

    requests = load(
        db.leave_requests,
        company_id,
    )

    with review_tab:
        pending = [
            row
            for row in requests
            if row["status"] == "pending"
        ]

        if not pending:
            st.info(
                tr(
                    "لا توجد طلبات تنتظر المراجعة.",
                    "No requests awaiting review.",
                )
            )

        else:
            request_map = {
                row["id"]: row
                for row in pending
            }

            request_id = st.selectbox(
                tr("الطلب", "Request"),
                options=list(request_map),
                format_func=lambda key: (
                    f"{request_map[key]['employee_name']} | "
                    f"{request_map[key]['start_date']} → "
                    f"{request_map[key]['end_date']}"
                ),
                key=f"review_request_{company_id}",
            )

            selected = request_map[request_id]

            st.write(
                f"{types[selected['leave_type']]} — "
                f"{selected['calendar_days']} "
                f"{tr('يومًا تقويميًا', 'calendar days')}"
            )

            st.write(selected["reason"])

            with st.form(f"review_form_{request_id}"):
                decision = st.selectbox(
                    tr("القرار", "Decision"),
                    ["approved", "rejected"],
                    format_func=lambda key: statuses[key],
                )

                review_note = st.text_area(
                    tr("تعليق المراجعة — مطلوب", "Review note — required")
                )

                confirmed = st.checkbox(
                    tr(
                        "أؤكد مراجعة بيانات الطلب.",
                        "I confirm the request has been reviewed.",
                    )
                )

                submitted = st.form_submit_button(
                    tr("تنفيذ القرار", "Apply decision"),
                    type="primary",
                )

            if submitted:
                if not confirmed or not review_note.strip():
                    st.error(
                        tr(
                            "أدخل تعليقًا وفعّل تأكيد المراجعة.",
                            "Enter a note and confirm the review.",
                        )
                    )

                else:
                    attempt(
                        db.review_leave_request,
                        company_id,
                        selected["employee_id"],
                        request_id,
                        decision,
                        review_note,
                        actor,
                    )

    with list_tab:
        filter_options = {
            "all": tr("كل الحالات", "All statuses"),
            **statuses,
        }

        selected_status = st.selectbox(
            tr("الحالة", "Status"),
            options=list(filter_options),
            format_func=lambda key: filter_options[key],
            key=f"leave_status_filter_{company_id}",
        )

        rows = []

        for request in requests:
            if (
                selected_status != "all"
                and request["status"] != selected_status
            ):
                continue

            rows.append({
                tr("الموظف", "Employee"):
                    request["employee_name"],
                tr("الكود", "Code"):
                    request["employee_code"],
                tr("النوع", "Type"):
                    types[request["leave_type"]],
                tr("من", "From"):
                    request["start_date"],
                tr("إلى", "To"):
                    request["end_date"],
                tr("أيام تقويمية", "Calendar days"):
                    request["calendar_days"],
                tr("الحالة", "Status"):
                    statuses[request["status"]],
                tr("المراجع", "Reviewer"):
                    request["reviewed_by"] or "",
                tr("تعليق المراجعة", "Review note"):
                    request["review_note"],
            })

        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info(
                tr("لا توجد طلبات مطابقة.", "No matching requests.")
            )
