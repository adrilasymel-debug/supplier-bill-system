import streamlit as st
from pathlib import Path
import re

from auth import login_user
from database import get_connection
from ocr import extract_text
from ai_extractor import extract_invoice
from styles import load_css, render_status


st.set_page_config(
    page_title="Supplier Bill Management System",
    page_icon=":material/receipt_long:",
    layout="wide"
)

load_css()


BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FILE NAME SAFETY
# ============================================================

def safe_filename(value):

    value = str(value).strip()

    value = re.sub(
        r'[<>:"/\\|?*]',
        '_',
        value
    )

    value = re.sub(
        r'[\x00-\x1f]',
        '_',
        value
    )

    value = value.strip(" .")

    if not value:
        value = "unknown"

    return value


# ============================================================
# LOGIN
# ============================================================

def login_page():

    left, center, right = st.columns([1, 1.2, 1])

    with center:

        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.markdown("# Supplier Bill Management")
        st.markdown(
            '<p class="login-subtitle">Sign in to continue</p>',
            unsafe_allow_html=True
        )

        username = st.text_input("Username")

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True
        ):

            user = login_user(
                username,
                password
            )

            if user:

                st.session_state["logged_in"] = True
                st.session_state["user"] = user

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# AI EXTRACTION DISPLAY
# ============================================================

def display_ai_extraction(extracted):

    supplier = extracted["supplier"]
    invoice = extracted["invoice"]
    items = extracted["items"]

    st.divider()

    st.subheader("Extracted Information")

    st.info(
        "Please check the information carefully. "
        "You can edit any field before saving the invoice."
    )

    # --------------------------------------------------------
    # SUPPLIER
    # --------------------------------------------------------

    st.write("### Supplier Information")

    supplier_name = st.text_input(
        "Supplier Name",
        value=supplier["name"],
        key="ai_supplier_name"
    )

    supplier_tin = st.text_input(
        "Supplier TIN",
        value=supplier["tin"],
        key="ai_supplier_tin"
    )

    supplier_address = st.text_area(
        "Supplier Address",
        value=supplier["address"],
        key="ai_supplier_address"
    )

    col1, col2 = st.columns(2)

    with col1:

        supplier_phone = st.text_input(
            "Supplier Phone",
            value=supplier["phone"],
            key="ai_supplier_phone"
        )

    with col2:

        supplier_email = st.text_input(
            "Supplier Email",
            value=supplier["email"],
            key="ai_supplier_email"
        )

    # --------------------------------------------------------
    # INVOICE
    # --------------------------------------------------------

    st.write("### Invoice Information")

    col1, col2 = st.columns(2)

    with col1:

        invoice_number = st.text_input(
            "Invoice Number",
            value=invoice["number"],
            key="ai_invoice_number"
        )

    with col2:

        invoice_date = st.text_input(
            "Invoice Date",
            value=invoice["date"],
            key="ai_invoice_date"
        )

    payment_terms = st.text_input(
        "Payment Terms",
        value=invoice["payment_terms"],
        key="ai_payment_terms"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        total_before_tax = st.number_input(
            "Total Before Tax (RM)",
            min_value=0.0,
            value=float(invoice["total_before_tax"]),
            step=0.01,
            key="ai_total_before_tax"
        )

    with col2:

        tax_amount = st.number_input(
            "Tax Amount (RM)",
            min_value=0.0,
            value=float(invoice["tax_amount"]),
            step=0.01,
            key="ai_tax_amount"
        )

    with col3:

        total_amount = st.number_input(
            "Total Amount (RM)",
            min_value=0.0,
            value=float(invoice["total_amount"]),
            step=0.01,
            key="ai_total_amount"
        )

    # --------------------------------------------------------
    # ITEMS
    # --------------------------------------------------------

    st.write("### Invoice Items")

    if not items:

        st.warning(
            "AI could not identify any invoice items."
        )

    edited_items = []

    for index, item in enumerate(items):

        st.write(
            f"#### Item {index + 1}"
        )

        col1, col2 = st.columns([1, 3])

        with col1:

            code = st.text_input(
                "Product Code",
                value=item["code"],
                key=f"item_code_{index}"
            )

        with col2:

            description = st.text_input(
                "Description",
                value=item["description"],
                key=f"item_description_{index}"
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=float(item["quantity"]),
                step=0.01,
                key=f"item_quantity_{index}"
            )

        with col2:

            unit = st.text_input(
                "Unit",
                value=item["unit"],
                key=f"item_unit_{index}"
            )

        with col3:

            unit_price = st.number_input(
                "Unit Price (RM)",
                min_value=0.0,
                value=float(item["unit_price"]),
                step=0.01,
                key=f"item_price_{index}"
            )

        with col4:

            subtotal = st.number_input(
                "Subtotal (RM)",
                min_value=0.0,
                value=float(item["subtotal"]),
                step=0.01,
                key=f"item_subtotal_{index}"
            )

        edited_items.append(
            {
                "code": code,
                "description": description,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "subtotal": subtotal
            }
        )

    # --------------------------------------------------------
    # TOTAL CHECK
    # --------------------------------------------------------

    calculated_items_total = sum(
        item["subtotal"]
        for item in edited_items
    )

    st.divider()

    st.write(
        f"**Sum of item subtotals: "
        f"RM {calculated_items_total:,.2f}**"
    )

    difference = (
        calculated_items_total
        - total_before_tax
    )

    if abs(difference) > 0.01:

        st.warning(
            f"Item total differs from "
            f"invoice subtotal by "
            f"RM {abs(difference):,.2f}. "
            f"Please check the figures."
        )

    else:

        st.success(
            "Item totals match the invoice subtotal."
        )

    st.divider()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    if st.button(
        "Save Invoice",
        type="primary",
        key="save_ai_invoice"
    ):

        if supplier_name.strip() == "":
            st.error("Supplier name is required.")
            return

        if total_amount <= 0:
            st.error(
                "Total invoice amount must be greater than RM 0."
            )
            return

        if invoice_date.strip() == "":
            st.error("Invoice date is required.")
            return

        if "uploaded_invoice_file" not in st.session_state:
            st.error(
                "Uploaded invoice file could not be found."
            )
            return

        connection = get_connection()

        try:

            # ------------------------------------------------
            # FIND OR CREATE SUPPLIER
            # ------------------------------------------------

            existing_supplier = connection.execute(
                """
                SELECT supplier_id
                FROM suppliers
                WHERE name = ?
                """,
                (supplier_name.strip(),)
            ).fetchone()

            if existing_supplier:

                supplier_id = existing_supplier["supplier_id"]

                connection.execute(
                    """
                    UPDATE suppliers
                    SET phone = ?,
                        address = ?,
                        tin = ?
                    WHERE supplier_id = ?
                    """,
                    (
                        supplier_phone.strip(),
                        supplier_address.strip(),
                        supplier_tin.strip(),
                        supplier_id
                    )
                )

            else:

                cursor = connection.execute(
                    """
                    INSERT INTO suppliers (
                        name,
                        phone,
                        address,
                        tin
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        supplier_name.strip(),
                        supplier_phone.strip(),
                        supplier_address.strip(),
                        supplier_tin.strip()
                    )
                )

                supplier_id = cursor.lastrowid

            # ------------------------------------------------
            # SAVE IMAGE
            # ------------------------------------------------

            uploaded_file = st.session_state[
                "uploaded_invoice_file"
            ]

            file_extension = Path(
                uploaded_file.name
            ).suffix.lower()

            safe_invoice_number = safe_filename(
                invoice_number
            )

            safe_invoice_date = safe_filename(
                invoice_date
            )

            file_name = (
                f"invoice_"
                f"{safe_invoice_number}_"
                f"{safe_invoice_date}"
                f"{file_extension}"
            )

            file_path = UPLOAD_DIR / file_name

            with open(
                file_path,
                "wb"
            ) as file:

                file.write(
                    uploaded_file.getbuffer()
                )

            # ------------------------------------------------
            # SAVE INVOICE
            # ------------------------------------------------

            cursor = connection.execute(
                """
                INSERT INTO invoices (
                    supplier_id,
                    invoice_number,
                    invoice_date,
                    payment_terms,
                    total_before_tax,
                    tax_amount,
                    total_amount,
                    amount_paid,
                    status,
                    image_path,
                    uploaded_by,
                    verification_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    supplier_id,
                    invoice_number.strip(),
                    invoice_date.strip(),
                    payment_terms.strip(),
                    total_before_tax,
                    tax_amount,
                    total_amount,
                    0,
                    "Unpaid",
                    str(file_path),
                    st.session_state["user"]["user_id"],
                    "Pending"
                )
            )

            invoice_id = cursor.lastrowid

            # ------------------------------------------------
            # SAVE ITEMS
            # ------------------------------------------------

            for item in edited_items:

                connection.execute(
                    """
                    INSERT INTO invoice_items (
                        invoice_id,
                        item_code,
                        product_name,
                        quantity,
                        unit,
                        unit_price,
                        subtotal
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id,
                        item["code"].strip(),
                        item["description"].strip(),
                        item["quantity"],
                        item["unit"].strip(),
                        item["unit_price"],
                        item["subtotal"]
                    )
                )

            connection.commit()

            st.success(
                "Invoice saved successfully!"
            )

            st.info(
                "Invoice is now Pending verification."
            )

            for key in [
                "ocr_text",
                "ai_invoice",
                "uploaded_invoice_file"
            ]:

                if key in st.session_state:
                    del st.session_state[key]

        except Exception as error:

            connection.rollback()

            st.error(
                f"Could not save invoice: {error}"
            )

        finally:

            connection.close()


# ============================================================
# UPLOAD INVOICE
# ============================================================

def upload_invoice_page():

    st.title("Upload Supplier Invoice")

    st.write(
        "Upload a photo of the supplier bill. "
        "The system will read the invoice using OCR "
        "and then use AI to extract the invoice information."
    )

    uploaded_file = st.file_uploader(
        "Take or upload a photo of the invoice",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if uploaded_file is None:
        return

    current_file_signature = (
        uploaded_file.name,
        uploaded_file.size
    )

    previous_file_signature = st.session_state.get(
        "uploaded_file_signature"
    )

    if current_file_signature != previous_file_signature:

        st.session_state[
            "uploaded_file_signature"
        ] = current_file_signature

        for key in [
            "ocr_text",
            "ai_invoice"
        ]:

            if key in st.session_state:
                del st.session_state[key]

    st.session_state[
        "uploaded_invoice_file"
    ] = uploaded_file

    st.divider()

    st.subheader("Invoice Preview")

    st.image(
        uploaded_file,
        caption="Uploaded invoice",
        width="stretch"
    )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    if st.button(
        "Read Invoice",
        type="primary"
    ):

        temp_path = (
            UPLOAD_DIR
            / "ocr_temp_image.jpg"
        )

        with open(
            temp_path,
            "wb"
        ) as file:

            file.write(
                uploaded_file.getbuffer()
            )

        with st.spinner(
            "Reading invoice with OCR..."
        ):

            try:

                extracted_text = extract_text(
                    temp_path
                )

                st.session_state[
                    "ocr_text"
                ] = extracted_text

            except Exception as error:

                st.error(
                    f"OCR failed: {error}"
                )

    # --------------------------------------------------------
    # OCR RESULT
    # --------------------------------------------------------

    if "ocr_text" in st.session_state:

        st.divider()

        st.subheader(
            "OCR Result"
        )

        extracted_text = st.text_area(
            "Text detected from invoice",
            value=st.session_state["ocr_text"],
            height=300
        )

        if st.button(
            "Extract Invoice Information with AI",
            type="primary"
        ):

            with st.spinner(
                "AI is analysing the invoice..."
            ):

                try:

                    extracted_invoice = extract_invoice(
                        extracted_text
                    )

                    st.session_state[
                        "ai_invoice"
                    ] = extracted_invoice

                    st.success(
                        "AI extraction completed."
                    )

                except Exception as error:

                    st.error(
                        f"AI extraction failed: {error}"
                    )

    # --------------------------------------------------------
    # AI FORM
    # --------------------------------------------------------

    if "ai_invoice" in st.session_state:

        display_ai_extraction(
            st.session_state["ai_invoice"]
        )


# ============================================================
# VERIFY INVOICE
# ============================================================

def verify_invoice_page():

    st.title("Verify Invoice")

    connection = get_connection()

    try:

        pending_invoices = connection.execute(
            """
            SELECT
                invoices.invoice_id,
                invoices.invoice_number,
                invoices.invoice_date,
                invoices.total_amount,
                invoices.image_path,
                suppliers.name AS supplier_name
            FROM invoices
            JOIN suppliers
                ON invoices.supplier_id =
                   suppliers.supplier_id
            WHERE invoices.verification_status = 'Pending'
            ORDER BY invoices.created_at DESC
            """
        ).fetchall()

    finally:

        connection.close()

    if not pending_invoices:

        st.success(
            "There are no invoices waiting for verification."
        )

        return

    st.write(
        f"**{len(pending_invoices)} invoice(s) "
        "waiting for verification.**"
    )

    st.divider()

    for invoice in pending_invoices:

        with st.container(border=True):

            st.subheader(
                f"Invoice #{invoice['invoice_number'] or 'Unknown'}"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write("### Invoice Photo")

                image_path = Path(
                    invoice["image_path"]
                )

                if image_path.exists():

                    st.image(
                        str(image_path),
                        caption="Uploaded invoice",
                        width="stretch"
                    )

                else:

                    st.error(
                        "Invoice image could not be found."
                    )

            with col2:

                st.write("### Invoice Information")

                st.write(
                    f"**Supplier:** "
                    f"{invoice['supplier_name']}"
                )

                st.write(
                    f"**Invoice Number:** "
                    f"{invoice['invoice_number'] or 'Not provided'}"
                )

                st.write(
                    f"**Invoice Date:** "
                    f"{invoice['invoice_date']}"
                )

                st.write(
                    f"**Total Amount:** "
                    f"RM {invoice['total_amount']:,.2f}"
                )

                st.write("### Verification")

                confirm = st.checkbox(
                    "I have checked the invoice information.",
                    key=f"confirm_{invoice['invoice_id']}"
                )

                if st.button(
                    "Verify Invoice",
                    key=f"verify_{invoice['invoice_id']}",
                    type="primary"
                ):

                    if not confirm:

                        st.warning(
                            "Please confirm that you have "
                            "checked the invoice information."
                        )

                    else:

                        connection = get_connection()

                        try:

                            connection.execute(
                                """
                                UPDATE invoices
                                SET verification_status = 'Verified'
                                WHERE invoice_id = ?
                                """,
                                (
                                    invoice["invoice_id"],
                                )
                            )

                            connection.commit()

                            st.success(
                                "Invoice verified successfully!"
                            )

                        finally:

                            connection.close()

                        st.rerun()


# ============================================================
# BOSS: INVOICE DETAIL
# ============================================================

def show_boss_invoice_detail(invoice_id):

    st.divider()

    if st.button(
        "Back",
        key=f"back_invoice_{invoice_id}"
    ):

        st.session_state.pop(
            "selected_invoice_id",
            None
        )

        st.rerun()

    connection = get_connection()

    try:

        invoice = connection.execute(
            """
            SELECT
                invoices.*,
                suppliers.name AS supplier_name,
                suppliers.phone AS supplier_phone,
                suppliers.address AS supplier_address,
                suppliers.tin AS supplier_tin,
                users.name AS uploaded_by_name
            FROM invoices
            JOIN suppliers
                ON invoices.supplier_id =
                   suppliers.supplier_id
            LEFT JOIN users
                ON invoices.uploaded_by =
                   users.user_id
            WHERE invoices.invoice_id = ?
            """,
            (invoice_id,)
        ).fetchone()

        items = connection.execute(
            """
            SELECT
                item_code,
                product_name,
                quantity,
                unit,
                unit_price,
                subtotal
            FROM invoice_items
            WHERE invoice_id = ?
            ORDER BY item_id
            """,
            (invoice_id,)
        ).fetchall()

    finally:

        connection.close()

    if invoice is None:

        st.error(
            "Invoice could not be found."
        )

        return

    st.subheader(
        f"Invoice #{invoice['invoice_number'] or 'Unknown'}"
    )

    col1, col2, col3, col4 = st.columns(4)

    outstanding = max(
        invoice["total_amount"]
        - invoice["amount_paid"],
        0
    )

    with col1:

        st.metric(
            "Invoice Total",
            f"RM {invoice['total_amount']:,.2f}"
        )

    with col2:

        st.metric(
            "Amount Paid",
            f"RM {invoice['amount_paid']:,.2f}"
        )

    with col3:

        st.metric(
            "Outstanding",
            f"RM {outstanding:,.2f}"
        )

    with col4:

        st.metric(
            "Status",
            invoice["status"]
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.write("### Supplier")

        st.write(
            f"**Name:** {invoice['supplier_name']}"
        )

        st.write(
            f"**TIN:** "
            f"{invoice['supplier_tin'] or 'Not provided'}"
        )

        st.write(
            f"**Phone:** "
            f"{invoice['supplier_phone'] or 'Not provided'}"
        )

        st.write(
            f"**Address:** "
            f"{invoice['supplier_address'] or 'Not provided'}"
        )

    with col2:

        st.write("### Invoice")

        st.write(
            f"**Invoice Number:** "
            f"{invoice['invoice_number'] or 'Not provided'}"
        )

        st.write(
            f"**Invoice Date:** "
            f"{invoice['invoice_date']}"
        )

        st.write(
            f"**Payment Terms:** "
            f"{invoice['payment_terms'] or 'Not provided'}"
        )

        st.write(
            f"**Verification:** "
            f"{invoice['verification_status']}"
        )

        st.write(
            f"**Uploaded By:** "
            f"{invoice['uploaded_by_name'] or 'Unknown'}"
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.write("### Original Invoice")

        image_path = Path(
            invoice["image_path"]
        )

        if image_path.exists():

            st.image(
                str(image_path),
                caption="Original uploaded invoice",
                width="stretch"
            )

        else:

            st.error(
                "Original invoice image could not be found."
            )

    with col2:

        st.write("### Invoice Items")

        if not items:

            st.info(
                "No invoice items recorded."
            )

        else:

            for index, item in enumerate(items):

                st.write(
                    f"**{index + 1}. "
                    f"{item['product_name']}**"
                )

                if item["item_code"]:

                    st.caption(
                        f"Code: {item['item_code']}"
                    )

                st.write(
                    f"Quantity: {item['quantity']:,.2f} "
                    f"{item['unit'] or ''}"
                )

                st.write(
                    f"Unit Price: "
                    f"RM {item['unit_price']:,.2f}"
                )

                st.write(
                    f"Subtotal: "
                    f"RM {item['subtotal']:,.2f}"
                )

                st.divider()

    st.divider()

    st.write("### Invoice Totals")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Before Tax",
            f"RM {invoice['total_before_tax']:,.2f}"
        )

    with col2:

        st.metric(
            "Tax",
            f"RM {invoice['tax_amount']:,.2f}"
        )

    with col3:

        st.metric(
            "Total",
            f"RM {invoice['total_amount']:,.2f}"
        )


# ============================================================
# BOSS: INVOICE MANAGEMENT
# ============================================================

def boss_invoice_management():

    st.title("Invoice Management")

    connection = get_connection()

    try:

        suppliers = connection.execute(
            """
            SELECT
                supplier_id,
                name
            FROM suppliers
            WHERE active = 1
            ORDER BY name
            """
        ).fetchall()

    finally:

        connection.close()

    st.subheader("Search & Filters")

    col1, col2 = st.columns(2)

    with col1:

        search = st.text_input(
            "Search invoice or supplier",
            placeholder="e.g. IV-2608 or supplier name"
        )

    with col2:

        supplier_options = {
            "All Suppliers": None
        }

        for supplier in suppliers:

            supplier_options[
                supplier["name"]
            ] = supplier["supplier_id"]

        selected_supplier_name = st.selectbox(
            "Supplier",
            list(supplier_options.keys())
        )

    col1, col2, col3 = st.columns(3)

    with col1:

        status_filter = st.selectbox(
            "Payment Status",
            [
                "All",
                "Unpaid",
                "Partially Paid",
                "Paid"
            ]
        )

    with col2:

        verification_filter = st.selectbox(
            "Verification",
            [
                "All",
                "Pending",
                "Verified"
            ]
        )

    with col3:

        sort_order = st.selectbox(
            "Sort",
            [
                "Newest First",
                "Oldest First",
                "Highest Amount",
                "Lowest Amount"
            ]
        )

    query = """
        SELECT
            invoices.invoice_id,
            invoices.invoice_number,
            invoices.invoice_date,
            invoices.total_amount,
            invoices.amount_paid,
            invoices.status,
            invoices.verification_status,
            suppliers.name AS supplier_name
        FROM invoices
        JOIN suppliers
            ON invoices.supplier_id =
               suppliers.supplier_id
        WHERE 1 = 1
    """

    parameters = []

    if search.strip():

        query += """
            AND (
                invoices.invoice_number LIKE ?
                OR suppliers.name LIKE ?
            )
        """

        search_value = f"%{search.strip()}%"

        parameters.extend([
            search_value,
            search_value
        ])

    selected_supplier_id = supplier_options[
        selected_supplier_name
    ]

    if selected_supplier_id is not None:

        query += """
            AND invoices.supplier_id = ?
        """

        parameters.append(
            selected_supplier_id
        )

    if status_filter != "All":

        query += """
            AND invoices.status = ?
        """

        parameters.append(
            status_filter
        )

    if verification_filter != "All":

        query += """
            AND invoices.verification_status = ?
        """

        parameters.append(
            verification_filter
        )

    if sort_order == "Newest First":

        query += """
            ORDER BY invoices.invoice_date DESC,
                     invoices.invoice_id DESC
        """

    elif sort_order == "Oldest First":

        query += """
            ORDER BY invoices.invoice_date ASC,
                     invoices.invoice_id ASC
        """

    elif sort_order == "Highest Amount":

        query += """
            ORDER BY invoices.total_amount DESC
        """

    else:

        query += """
            ORDER BY invoices.total_amount ASC
        """

    connection = get_connection()

    try:

        invoices = connection.execute(
            query,
            parameters
        ).fetchall()

    finally:

        connection.close()

    st.divider()

    total_invoices = len(invoices)

    total_amount = sum(
        invoice["total_amount"]
        for invoice in invoices
    )

    total_outstanding = sum(
        max(
            invoice["total_amount"]
            - invoice["amount_paid"],
            0
        )
        for invoice in invoices
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Invoices Found",
            total_invoices
        )

    with col2:

        st.metric(
            "Invoice Value",
            f"RM {total_amount:,.2f}"
        )

    with col3:

        st.metric(
            "Outstanding",
            f"RM {total_outstanding:,.2f}"
        )

    st.divider()

    if not invoices:

        st.info(
            "No invoices match your search or filters."
        )

        return

    st.subheader(
        f"{len(invoices)} Invoice(s)"
    )

    for invoice in invoices:

        outstanding = max(
            invoice["total_amount"]
            - invoice["amount_paid"],
            0
        )

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [2.5, 2, 1.5, 1.5]
            )

            with col1:

                st.write(
                    f"**{invoice['invoice_number'] or 'No Invoice Number'}**"
                )

                st.write(
                    invoice["supplier_name"]
                )

            with col2:

                st.write(
                    f"Date: **{invoice['invoice_date']}**"
                )

                st.write(
                    f"Total: **RM "
                    f"{invoice['total_amount']:,.2f}**"
                )

            with col3:

                if invoice["status"] == "Paid":

                    st.success("Paid")

                elif invoice["status"] == "Partially Paid":

                    st.warning("Partially Paid")

                else:

                    st.error("Unpaid")

                if invoice["verification_status"] == "Verified":

                    render_status("Verified", "verified")

                else:

                    render_status("Pending verification", "pending")

            with col4:

                st.write("Outstanding")

                st.write(
                    f"**RM {outstanding:,.2f}**"
                )

                if st.button(
                    "View",
                    key=f"view_invoice_{invoice['invoice_id']}"
                ):

                    st.session_state[
                        "selected_invoice_id"
                    ] = invoice["invoice_id"]

                    st.rerun()

    if "selected_invoice_id" in st.session_state:

        show_boss_invoice_detail(
            st.session_state["selected_invoice_id"]
        )


# ============================================================
# BOSS: SUPPLIER MANAGEMENT
# ============================================================

def boss_supplier_management():

    st.title("Supplier Management")

    connection = get_connection()

    try:

        suppliers = connection.execute(
            """
            SELECT
                suppliers.supplier_id,
                suppliers.name,
                suppliers.phone,
                suppliers.address,
                suppliers.tin,

                COUNT(invoices.invoice_id)
                    AS invoice_count,

                COALESCE(
                    SUM(invoices.total_amount),
                    0
                ) AS total_purchases,

                COALESCE(
                    SUM(invoices.amount_paid),
                    0
                ) AS total_paid,

                COALESCE(
                    SUM(
                        invoices.total_amount
                        - invoices.amount_paid
                    ),
                    0
                ) AS outstanding

            FROM suppliers

            LEFT JOIN invoices
                ON suppliers.supplier_id =
                   invoices.supplier_id

            WHERE suppliers.active = 1

            GROUP BY
                suppliers.supplier_id

            ORDER BY
                suppliers.name
            """
        ).fetchall()

    finally:

        connection.close()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "Search supplier",
        placeholder="Search by supplier name, phone or TIN"
    )

    filtered_suppliers = []

    for supplier in suppliers:

        if search.strip():

            search_value = search.strip().lower()

            searchable_text = " ".join([
                supplier["name"] or "",
                supplier["phone"] or "",
                supplier["tin"] or ""
            ]).lower()

            if search_value not in searchable_text:

                continue

        filtered_suppliers.append(
            supplier
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.divider()

    supplier_count = len(
        filtered_suppliers
    )

    total_purchases = sum(
        supplier["total_purchases"]
        for supplier in filtered_suppliers
    )

    total_outstanding = sum(
        max(
            supplier["outstanding"],
            0
        )
        for supplier in filtered_suppliers
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Suppliers",
            supplier_count
        )

    with col2:

        st.metric(
            "Total Purchases",
            f"RM {total_purchases:,.2f}"
        )

    with col3:

        st.metric(
            "Total Outstanding",
            f"RM {total_outstanding:,.2f}"
        )

    st.divider()

    # --------------------------------------------------------
    # SUPPLIER LIST
    # --------------------------------------------------------

    if not filtered_suppliers:

        st.info(
            "No suppliers found."
        )

        return

    st.subheader(
        f"{len(filtered_suppliers)} Supplier(s)"
    )

    for supplier in filtered_suppliers:

        with st.container(
            border=True
        ):

            col1, col2, col3, col4 = st.columns(
                [2.5, 1.5, 2, 1]
            )

            with col1:

                st.write(
                    f"### {supplier['name']}"
                )

                if supplier["tin"]:

                    st.caption(
                        f"TIN: {supplier['tin']}"
                    )

                if supplier["phone"]:

                    st.caption(
                        f"Phone: {supplier['phone']}"
                    )

            with col2:

                st.write(
                    "Invoices"
                )

                st.write(
                    f"**{supplier['invoice_count']}**"
                )

            with col3:

                st.write(
                    "Purchases"
                )

                st.write(
                    f"**RM "
                    f"{supplier['total_purchases']:,.2f}**"
                )

                st.write(
                    f"Outstanding: "
                    f"**RM "
                    f"{max(supplier['outstanding'], 0):,.2f}**"
                )

            with col4:

                if st.button(
                    "View",
                    key=f"view_supplier_{supplier['supplier_id']}"
                ):

                    st.session_state[
                        "selected_supplier_id"
                    ] = supplier["supplier_id"]

                    st.rerun()

    # --------------------------------------------------------
    # DETAIL
    # --------------------------------------------------------

    if "selected_supplier_id" in st.session_state:

        show_supplier_detail(
            st.session_state[
                "selected_supplier_id"
            ]
        )


# ============================================================
# BOSS: SUPPLIER DETAIL
# ============================================================

def show_supplier_detail(supplier_id):

    st.divider()

    if st.button(
        "Back to Supplier List",
        key="back_supplier_list"
    ):

        st.session_state.pop(
            "selected_supplier_id",
            None
        )

        st.rerun()

    connection = get_connection()

    try:

        supplier = connection.execute(
            """
            SELECT
                supplier_id,
                name,
                phone,
                address,
                tin
            FROM suppliers
            WHERE supplier_id = ?
            """,
            (supplier_id,)
        ).fetchone()

        invoices = connection.execute(
            """
            SELECT
                invoice_id,
                invoice_number,
                invoice_date,
                total_amount,
                amount_paid,
                status,
                verification_status
            FROM invoices
            WHERE supplier_id = ?
            ORDER BY invoice_date DESC,
                     invoice_id DESC
            """,
            (supplier_id,)
        ).fetchall()

    finally:

        connection.close()

    if supplier is None:

        st.error(
            "Supplier could not be found."
        )

        return

    total_purchases = sum(
        invoice["total_amount"]
        for invoice in invoices
    )

    total_paid = sum(
        invoice["amount_paid"]
        for invoice in invoices
    )

    outstanding = max(
        total_purchases - total_paid,
        0
    )

    # --------------------------------------------------------
    # SUPPLIER HEADER
    # --------------------------------------------------------

    st.subheader(
        supplier["name"]
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Invoices",
            len(invoices)
        )

    with col2:

        st.metric(
            "Total Purchases",
            f"RM {total_purchases:,.2f}"
        )

    with col3:

        st.metric(
            "Amount Paid",
            f"RM {total_paid:,.2f}"
        )

    with col4:

        st.metric(
            "Outstanding",
            f"RM {outstanding:,.2f}"
        )

    # --------------------------------------------------------
    # CONTACT INFORMATION
    # --------------------------------------------------------

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.write("### Supplier Information")

        st.write(
            f"**Supplier Name:** "
            f"{supplier['name']}"
        )

        st.write(
            f"**TIN:** "
            f"{supplier['tin'] or 'Not provided'}"
        )

        st.write(
            f"**Phone:** "
            f"{supplier['phone'] or 'Not provided'}"
        )

    with col2:

        st.write("### Address")

        st.write(
            supplier["address"]
            or "Not provided"
        )

    # --------------------------------------------------------
    # INVOICE HISTORY
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "Invoice History"
    )

    if not invoices:

        st.info(
            "This supplier has no invoices yet."
        )

        return

    for invoice in invoices:

        invoice_outstanding = max(
            invoice["total_amount"]
            - invoice["amount_paid"],
            0
        )

        with st.container(
            border=True
        ):

            col1, col2, col3, col4 = st.columns(
                [2, 2, 2, 1]
            )

            with col1:

                st.write(
                    f"**{invoice['invoice_number'] or 'Unknown'}**"
                )

                st.caption(
                    invoice["invoice_date"]
                )

            with col2:

                st.write(
                    "Invoice Total"
                )

                st.write(
                    f"**RM "
                    f"{invoice['total_amount']:,.2f}**"
                )

            with col3:

                st.write(
                    "Outstanding"
                )

                st.write(
                    f"**RM "
                    f"{invoice_outstanding:,.2f}**"
                )

                if invoice["verification_status"] == "Verified":

                    render_status("Verified", "verified")

                else:

                    render_status("Pending verification", "pending")

            with col4:

                if st.button(
                    "View",
                    key=f"supplier_invoice_{invoice['invoice_id']}"
                ):

                    st.session_state[
                        "selected_invoice_id"
                    ] = invoice["invoice_id"]

                    st.session_state[
                        "return_to_supplier"
                    ] = supplier_id

                    st.rerun()


# ============================================================
# BOSS: PAYMENT MANAGEMENT
# ============================================================

def boss_payment_management():

    st.title("Payment Management")

    connection = get_connection()

    try:

        invoices = connection.execute(
            """
            SELECT
                invoices.invoice_id,
                invoices.invoice_number,
                invoices.invoice_date,
                invoices.total_amount,
                invoices.amount_paid,
                invoices.status,
                invoices.verification_status,
                suppliers.name AS supplier_name
            FROM invoices
            JOIN suppliers
                ON invoices.supplier_id =
                   suppliers.supplier_id
            ORDER BY invoices.invoice_date DESC,
                     invoices.invoice_id DESC
            """
        ).fetchall()

    finally:

        connection.close()

    # --------------------------------------------------------
    # SEARCH & FILTER
    # --------------------------------------------------------

    st.subheader("Search & Filters")

    col1, col2 = st.columns(2)

    with col1:

        search = st.text_input(
            "Search invoice or supplier",
            placeholder="e.g. invoice number or supplier name"
        )

    with col2:

        status_filter = st.selectbox(
            "Payment Status",
            [
                "All",
                "Unpaid",
                "Partially Paid",
                "Paid"
            ]
        )

    filtered_invoices = []

    for invoice in invoices:

        if search.strip():

            search_value = search.strip().lower()

            searchable_text = " ".join([
                invoice["invoice_number"] or "",
                invoice["supplier_name"] or ""
            ]).lower()

            if search_value not in searchable_text:

                continue

        if (
            status_filter != "All"
            and invoice["status"] != status_filter
        ):

            continue

        filtered_invoices.append(invoice)

    st.divider()

    if not filtered_invoices:

        st.info(
            "No invoices match your search or filter."
        )

        return

    st.write(
        f"**{len(filtered_invoices)} invoice(s) found.**"
    )

    # --------------------------------------------------------
    # INVOICE SELECTION
    # --------------------------------------------------------

    invoice_options = {}

    for invoice in filtered_invoices:

        invoice_label = (
            f"{invoice['invoice_number'] or 'No Invoice Number'} "
            f"• {invoice['supplier_name']} "
            f"• RM {invoice['total_amount']:,.2f}"
        )

        invoice_options[invoice_label] = invoice["invoice_id"]

    selected_label = st.selectbox(
        "Select Invoice",
        list(invoice_options.keys())
    )

    selected_invoice_id = invoice_options[
        selected_label
    ]

    # --------------------------------------------------------
    # GET SELECTED INVOICE
    # --------------------------------------------------------

    connection = get_connection()

    try:

        invoice = connection.execute(
            """
            SELECT
                invoices.*,
                suppliers.name AS supplier_name
            FROM invoices
            JOIN suppliers
                ON invoices.supplier_id =
                   suppliers.supplier_id
            WHERE invoices.invoice_id = ?
            """,
            (selected_invoice_id,)
        ).fetchone()

        payments = connection.execute(
            """
            SELECT
                payments.payment_id,
                payments.payment_date,
                payments.amount,
                payments.payment_method,
                users.name AS recorded_by_name
            FROM payments
            LEFT JOIN users
                ON payments.recorded_by =
                   users.user_id
            WHERE payments.invoice_id = ?
            ORDER BY payments.payment_date DESC,
                     payments.payment_id DESC
            """,
            (selected_invoice_id,)
        ).fetchall()

    finally:

        connection.close()

    if invoice is None:

        st.error(
            "Invoice could not be found."
        )

        return

    outstanding = max(
        invoice["total_amount"]
        - invoice["amount_paid"],
        0
    )

    # --------------------------------------------------------
    # INVOICE SUMMARY
    # --------------------------------------------------------

    st.subheader(
        f"Invoice #{invoice['invoice_number'] or 'Unknown'}"
    )

    st.write(
        f"**Supplier:** {invoice['supplier_name']}"
    )

    st.write(
        f"**Invoice Date:** {invoice['invoice_date']}"
    )

    if invoice["verification_status"] == "Verified":

        st.success(
            "Invoice verified"
        )

    else:

        st.warning(
            "This invoice is still pending verification."
        )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Invoice Total",
            f"RM {invoice['total_amount']:,.2f}"
        )

    with col2:

        st.metric(
            "Amount Paid",
            f"RM {invoice['amount_paid']:,.2f}"
        )

    with col3:

        st.metric(
            "Outstanding",
            f"RM {outstanding:,.2f}"
        )

    with col4:

        st.metric(
            "Status",
            invoice["status"]
        )

    # --------------------------------------------------------
    # RECORD PAYMENT
    # --------------------------------------------------------

    st.divider()

    st.subheader("Record Payment")

    if outstanding <= 0:

        st.success(
            "This invoice has been fully paid."
        )

    else:

        payment_date = st.date_input(
            "Payment Date",
            value=None,
            key=f"payment_date_{selected_invoice_id}"
        )

        payment_amount = st.number_input(
            "Payment Amount (RM)",
            min_value=0.0,
            max_value=float(outstanding),
            value=0.0,
            step=0.01,
            key=f"payment_amount_{selected_invoice_id}"
        )

        payment_method = st.selectbox(
            "Payment Method",
            [
                "Bank Transfer",
                "Cash",
                "Cheque",
                "Other"
            ],
            key=f"payment_method_{selected_invoice_id}"
        )

        if st.button(
            "Record Payment",
            type="primary",
            key=f"record_payment_{selected_invoice_id}"
        ):

            if payment_date is None:

                st.error(
                    "Please select the payment date."
                )

            elif payment_amount <= 0:

                st.error(
                    "Payment amount must be greater than RM 0."
                )

            elif payment_amount > outstanding:

                st.error(
                    f"Payment cannot exceed the outstanding "
                    f"balance of RM {outstanding:,.2f}."
                )

            else:

                connection = get_connection()

                try:

                    # ----------------------------------------
                    # SAVE PAYMENT
                    # ----------------------------------------

                    connection.execute(
                        """
                        INSERT INTO payments (
                            invoice_id,
                            payment_date,
                            amount,
                            payment_method,
                            recorded_by
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            selected_invoice_id,
                            payment_date.isoformat(),
                            payment_amount,
                            payment_method,
                            st.session_state["user"]["user_id"]
                        )
                    )

                    # ----------------------------------------
                    # RECALCULATE TOTAL PAID
                    # ----------------------------------------

                    total_paid = connection.execute(
                        """
                        SELECT COALESCE(
                            SUM(amount),
                            0
                        ) AS total
                        FROM payments
                        WHERE invoice_id = ?
                        """,
                        (selected_invoice_id,)
                    ).fetchone()["total"]

                    # ----------------------------------------
                    # DETERMINE STATUS
                    # ----------------------------------------

                    total_amount = invoice["total_amount"]

                    if total_paid <= 0:

                        new_status = "Unpaid"

                    elif total_paid < total_amount:

                        new_status = "Partially Paid"

                    else:

                        new_status = "Paid"

                    # ----------------------------------------
                    # UPDATE INVOICE
                    # ----------------------------------------

                    connection.execute(
                        """
                        UPDATE invoices
                        SET amount_paid = ?,
                            status = ?
                        WHERE invoice_id = ?
                        """,
                        (
                            total_paid,
                            new_status,
                            selected_invoice_id
                        )
                    )

                    connection.commit()

                    st.success(
                        f"Payment of RM "
                        f"{payment_amount:,.2f} recorded successfully."
                    )

                    st.rerun()

                except Exception as error:

                    connection.rollback()

                    st.error(
                        f"Could not record payment: {error}"
                    )

                finally:

                    connection.close()

    # --------------------------------------------------------
    # PAYMENT HISTORY
    # --------------------------------------------------------

    st.divider()

    st.subheader("Payment History")

    if not payments:

        st.info(
            "No payments have been recorded for this invoice."
        )

    else:

        st.write(
            f"**{len(payments)} payment(s) recorded.**"
        )

        for payment in payments:

            with st.container(
                border=True
            ):

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.write("Payment Date")

                    st.write(
                        f"**{payment['payment_date']}**"
                    )

                with col2:

                    st.write("Amount")

                    st.write(
                        f"**RM "
                        f"{payment['amount']:,.2f}**"
                    )

                with col3:

                    st.write("Method")

                    st.write(
                        f"**{payment['payment_method'] or 'Not specified'}**"
                    )

                with col4:

                    st.write("Recorded By")

                    st.write(
                        f"**{payment['recorded_by_name'] or 'Unknown'}**"
                    )


# ============================================================
# BOSS: REPORTS & EXPORT
# ============================================================

def boss_reports():

    st.title("Reports & Export")

    connection = get_connection()

    try:

        # ----------------------------------------------------
        # SUMMARY DATA
        # ----------------------------------------------------

        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS invoice_count,
                COALESCE(SUM(total_amount), 0) AS total_purchases,
                COALESCE(SUM(amount_paid), 0) AS total_paid,
                COALESCE(
                    SUM(total_amount - amount_paid),
                    0
                ) AS total_outstanding
            FROM invoices
            """
        ).fetchone()

        # ----------------------------------------------------
        # INVOICE DATA
        # ----------------------------------------------------

        invoices = connection.execute(
            """
            SELECT
                invoices.invoice_id,
                invoices.invoice_number,
                invoices.invoice_date,
                suppliers.name AS supplier_name,
                invoices.total_before_tax,
                invoices.tax_amount,
                invoices.total_amount,
                invoices.amount_paid,
                (
                    invoices.total_amount
                    - invoices.amount_paid
                ) AS outstanding,
                invoices.status,
                invoices.verification_status,
                invoices.payment_terms
            FROM invoices
            JOIN suppliers
                ON invoices.supplier_id =
                   suppliers.supplier_id
            ORDER BY invoices.invoice_date DESC,
                     invoices.invoice_id DESC
            """
        ).fetchall()

        # ----------------------------------------------------
        # PAYMENT DATA
        # ----------------------------------------------------

        payments = connection.execute(
            """
            SELECT
                payments.payment_id,
                payments.payment_date,
                payments.amount,
                payments.payment_method,
                invoices.invoice_number,
                suppliers.name AS supplier_name,
                users.name AS recorded_by
            FROM payments
            JOIN invoices
                ON payments.invoice_id =
                   invoices.invoice_id
            JOIN suppliers
                ON invoices.supplier_id =
                   suppliers.supplier_id
            LEFT JOIN users
                ON payments.recorded_by =
                   users.user_id
            ORDER BY payments.payment_date DESC,
                     payments.payment_id DESC
            """
        ).fetchall()

        # ----------------------------------------------------
        # SUPPLIER DATA
        # ----------------------------------------------------

        supplier_report = connection.execute(
            """
            SELECT
                suppliers.name AS supplier_name,

                COUNT(invoices.invoice_id)
                    AS invoice_count,

                COALESCE(
                    SUM(invoices.total_amount),
                    0
                ) AS total_purchases,

                COALESCE(
                    SUM(invoices.amount_paid),
                    0
                ) AS total_paid,

                COALESCE(
                    SUM(
                        invoices.total_amount
                        - invoices.amount_paid
                    ),
                    0
                ) AS outstanding

            FROM suppliers

            LEFT JOIN invoices
                ON suppliers.supplier_id =
                   invoices.supplier_id

            WHERE suppliers.active = 1

            GROUP BY suppliers.supplier_id

            ORDER BY total_purchases DESC
            """
        ).fetchall()

    finally:

        connection.close()

    # ========================================================
    # DATE FILTER
    # ========================================================

    st.subheader("Report Period")

    col1, col2 = st.columns(2)

    with col1:

        start_date = st.date_input(
            "Start Date",
            value=None
        )

    with col2:

        end_date = st.date_input(
            "End Date",
            value=None
        )

    if start_date and end_date:

        if start_date > end_date:

            st.error(
                "Start date cannot be later than end date."
            )

            return

    # ========================================================
    # SUMMARY
    # ========================================================

    st.divider()

    st.subheader("Overall Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Invoices",
            summary["invoice_count"]
        )

    with col2:

        st.metric(
            "Total Purchases",
            f"RM {summary['total_purchases']:,.2f}"
        )

    with col3:

        st.metric(
            "Total Paid",
            f"RM {summary['total_paid']:,.2f}"
        )

    with col4:

        st.metric(
            "Outstanding",
            f"RM {summary['total_outstanding']:,.2f}"
        )

    # ========================================================
    # INVOICE REPORT
    # ========================================================

    st.divider()

    st.subheader("Invoice Report")

    filtered_invoices = []

    for invoice in invoices:

        if start_date:

            if invoice["invoice_date"] < start_date.isoformat():

                continue

        if end_date:

            if invoice["invoice_date"] > end_date.isoformat():

                continue

        filtered_invoices.append(invoice)

    if filtered_invoices:

        invoice_data = []

        for invoice in filtered_invoices:

            invoice_data.append(
                {
                    "Invoice Number":
                        invoice["invoice_number"] or "",

                    "Invoice Date":
                        invoice["invoice_date"],

                    "Supplier":
                        invoice["supplier_name"],

                    "Before Tax":
                        invoice["total_before_tax"],

                    "Tax":
                        invoice["tax_amount"],

                    "Total":
                        invoice["total_amount"],

                    "Paid":
                        invoice["amount_paid"],

                    "Outstanding":
                        max(
                            invoice["outstanding"],
                            0
                        ),

                    "Payment Status":
                        invoice["status"],

                    "Verification":
                        invoice["verification_status"],

                    "Payment Terms":
                        invoice["payment_terms"] or ""
                }
            )

        st.dataframe(
            invoice_data,
            width="stretch",
            hide_index=True
        )

    else:

        st.info(
            "No invoices found for the selected period."
        )

    # ========================================================
    # PAYMENT REPORT
    # ========================================================

    st.divider()

    st.subheader("Payment Report")

    filtered_payments = []

    for payment in payments:

        if start_date:

            if payment["payment_date"] < start_date.isoformat():

                continue

        if end_date:

            if payment["payment_date"] > end_date.isoformat():

                continue

        filtered_payments.append(payment)

    payment_total = sum(
        payment["amount"]
        for payment in filtered_payments
    )

    st.metric(
        "Payments During Selected Period",
        f"RM {payment_total:,.2f}"
    )

    if filtered_payments:

        payment_data = []

        for payment in filtered_payments:

            payment_data.append(
                {
                    "Payment Date":
                        payment["payment_date"],

                    "Invoice Number":
                        payment["invoice_number"] or "",

                    "Supplier":
                        payment["supplier_name"],

                    "Amount":
                        payment["amount"],

                    "Payment Method":
                        payment["payment_method"] or "",

                    "Recorded By":
                        payment["recorded_by"] or ""
                }
            )

        st.dataframe(
            payment_data,
            width="stretch",
            hide_index=True
        )

    else:

        st.info(
            "No payments found for the selected period."
        )

    # ========================================================
    # SUPPLIER REPORT
    # ========================================================

    st.divider()

    st.subheader("Supplier Report")

    if supplier_report:

        supplier_data = []

        for supplier in supplier_report:

            supplier_data.append(
                {
                    "Supplier":
                        supplier["supplier_name"],

                    "Invoices":
                        supplier["invoice_count"],

                    "Total Purchases":
                        supplier["total_purchases"],

                    "Total Paid":
                        supplier["total_paid"],

                    "Outstanding":
                        max(
                            supplier["outstanding"],
                            0
                        )
                }
            )

        st.dataframe(
            supplier_data,
            width="stretch",
            hide_index=True
        )

    else:

        st.info(
            "No supplier data available."
        )

    # ========================================================
    # EXPORT
    # ========================================================

    st.divider()

    st.subheader("Export")

    st.write(
        "Download the current reports as CSV files."
    )

    import csv
    import io

    # --------------------------------------------------------
    # INVOICE CSV
    # --------------------------------------------------------

    invoice_csv = io.StringIO()

    if filtered_invoices:

        writer = csv.writer(invoice_csv)

        writer.writerow(
            [
                "Invoice Number",
                "Invoice Date",
                "Supplier",
                "Before Tax",
                "Tax",
                "Total",
                "Paid",
                "Outstanding",
                "Payment Status",
                "Verification",
                "Payment Terms"
            ]
        )

        for invoice in filtered_invoices:

            writer.writerow(
                [
                    invoice["invoice_number"] or "",
                    invoice["invoice_date"],
                    invoice["supplier_name"],
                    invoice["total_before_tax"],
                    invoice["tax_amount"],
                    invoice["total_amount"],
                    invoice["amount_paid"],
                    max(
                        invoice["outstanding"],
                        0
                    ),
                    invoice["status"],
                    invoice["verification_status"],
                    invoice["payment_terms"] or ""
                ]
            )

    # --------------------------------------------------------
    # PAYMENT CSV
    # --------------------------------------------------------

    payment_csv = io.StringIO()

    if filtered_payments:

        writer = csv.writer(payment_csv)

        writer.writerow(
            [
                "Payment Date",
                "Invoice Number",
                "Supplier",
                "Amount",
                "Payment Method",
                "Recorded By"
            ]
        )

        for payment in filtered_payments:

            writer.writerow(
                [
                    payment["payment_date"],
                    payment["invoice_number"] or "",
                    payment["supplier_name"],
                    payment["amount"],
                    payment["payment_method"] or "",
                    payment["recorded_by"] or ""
                ]
            )

    # --------------------------------------------------------
    # SUPPLIER CSV
    # --------------------------------------------------------

    supplier_csv = io.StringIO()

    if supplier_report:

        writer = csv.writer(supplier_csv)

        writer.writerow(
            [
                "Supplier",
                "Invoices",
                "Total Purchases",
                "Total Paid",
                "Outstanding"
            ]
        )

        for supplier in supplier_report:

            writer.writerow(
                [
                    supplier["supplier_name"],
                    supplier["invoice_count"],
                    supplier["total_purchases"],
                    supplier["total_paid"],
                    max(
                        supplier["outstanding"],
                        0
                    )
                ]
            )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.download_button(
            "Download Invoice Report",
            data=invoice_csv.getvalue(),
            file_name="invoice_report.csv",
            mime="text/csv",
            disabled=not filtered_invoices
        )

    with col2:

        st.download_button(
            "Download Payment Report",
            data=payment_csv.getvalue(),
            file_name="payment_report.csv",
            mime="text/csv",
            disabled=not filtered_payments
        )

    with col3:

        st.download_button(
            "Download Supplier Report",
            data=supplier_csv.getvalue(),
            file_name="supplier_report.csv",
            mime="text/csv",
            disabled=not supplier_report
        )


# ============================================================
# STAFF DASHBOARD
# ============================================================

def staff_dashboard():

    user = st.session_state["user"]

    st.sidebar.title("Staff")

    st.sidebar.write(
        f"Logged in as: {user['name']}"
    )

    if st.sidebar.button("Logout"):

        st.session_state.clear()

        st.rerun()

    page = st.sidebar.radio(
        "Menu",
        [
            "Upload Invoice",
            "Verify Invoice"
        ]
    )

    if page == "Upload Invoice":

        upload_invoice_page()

    elif page == "Verify Invoice":

        verify_invoice_page()


# ============================================================
# BOSS DASHBOARD
# ============================================================

def boss_dashboard():

    user = st.session_state["user"]

    st.sidebar.title("Boss")

    st.sidebar.write(
        f"Logged in as: {user['name']}"
    )

    if st.sidebar.button("Logout"):

        st.session_state.clear()

        st.rerun()

    page = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Invoice Management",
            "Supplier Management",
            "Payment Management",
            "Reports & Export"
        ]
    )

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

    if page == "Dashboard":

        st.title("Boss Dashboard")

        st.write(
            f"Welcome, {user['name']}!"
        )

        connection = get_connection()

        try:

            supplier_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM suppliers
                WHERE active = 1
                """
            ).fetchone()["count"]

            invoice_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM invoices
                """
            ).fetchone()["count"]

            unpaid_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM invoices
                WHERE status = 'Unpaid'
                """
            ).fetchone()["count"]

            outstanding = connection.execute(
                """
                SELECT COALESCE(
                    SUM(total_amount - amount_paid),
                    0
                ) AS total
                FROM invoices
                WHERE status != 'Paid'
                """
            ).fetchone()["total"]

        finally:

            connection.close()

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Suppliers",
                supplier_count
            )

        with col2:

            st.metric(
                "Total Invoices",
                invoice_count
            )

        with col3:

            st.metric(
                "Unpaid Bills",
                unpaid_count
            )

        with col4:

            st.metric(
                "Total Outstanding",
                f"RM {outstanding:,.2f}"
            )

        st.divider()

        st.subheader(
            "System Functions"
        )

        st.markdown(
            "- Invoice Management\n"
            "- Supplier Management\n"
            "- Payment Management\n"
            "- Reports & Export"
        )

    # --------------------------------------------------------
    # INVOICE MANAGEMENT
    # --------------------------------------------------------

    elif page == "Invoice Management":

        boss_invoice_management()

    # --------------------------------------------------------
    # SUPPLIER MANAGEMENT
    # --------------------------------------------------------

    elif page == "Supplier Management":

        boss_supplier_management()

    # --------------------------------------------------------
    # PAYMENT MANAGEMENT
    # --------------------------------------------------------

    elif page == "Payment Management":

        boss_payment_management()

    # --------------------------------------------------------
    # REPORTS & EXPORT
    # --------------------------------------------------------

    elif page == "Reports & Export":

        boss_reports()


# ============================================================
# MAIN
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state[
        "logged_in"
    ] = False


if not st.session_state["logged_in"]:

    login_page()

else:

    user_role = st.session_state[
        "user"
    ]["role"]

    if user_role == "boss":

        boss_dashboard()

    elif user_role == "staff":

        staff_dashboard()