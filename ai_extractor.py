import json
import os
from datetime import datetime

try:
    import streamlit as st
except ImportError:
    st = None


# Google Gemini free tier. Using the "latest" alias instead of a
# dated model name so this doesn't break again when Google retires
# a specific model version (they do this every few months).
MODEL = "gemini-flash-latest"


def _get_secret(key):

    if st is not None:

        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass

    return os.environ.get(key)


INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "supplier": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "tin": {"type": "string"},
                "address": {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": [
                "name",
                "tin",
                "address",
                "phone",
                "email"
            ]
        },

        "invoice": {
            "type": "object",
            "properties": {
                "number": {"type": "string"},
                "date": {"type": "string"},
                "payment_terms": {"type": "string"},
                "total_before_tax": {"type": "number"},
                "tax_amount": {"type": "number"},
                "total_amount": {"type": "number"}
            },
            "required": [
                "number",
                "date",
                "payment_terms",
                "total_before_tax",
                "tax_amount",
                "total_amount"
            ]
        },

        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string"},
                    "unit_price": {"type": "number"},
                    "subtotal": {"type": "number"}
                },
                "required": [
                    "code",
                    "description",
                    "quantity",
                    "unit",
                    "unit_price",
                    "subtotal"
                ]
            }
        }
    },

    "required": [
        "supplier",
        "invoice",
        "items"
    ]
}


def empty_invoice():

    return {
        "supplier": {
            "name": "",
            "tin": "",
            "address": "",
            "phone": "",
            "email": ""
        },

        "invoice": {
            "number": "",
            "date": "",
            "payment_terms": "",
            "total_before_tax": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0
        },

        "items": []
    }


def clean_number(value):

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value)

    value = (
        value
        .replace("RM", "")
        .replace(",", "")
        .strip()
    )

    try:
        return float(value)

    except ValueError:
        return 0.0


def clean_date(value):

    if not value:
        return ""

    value = str(value).strip()

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d.%m.%Y"
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                value,
                fmt
            )

            return parsed.strftime("%Y-%m-%d")

        except ValueError:
            pass

    return value


def validate_invoice(data):

    invoice = empty_invoice()

    if not isinstance(data, dict):
        return invoice

    # -----------------------------------------------------
    # Supplier
    # -----------------------------------------------------

    supplier = data.get("supplier", {})

    if isinstance(supplier, dict):

        invoice["supplier"]["name"] = str(
            supplier.get("name", "")
        )

        invoice["supplier"]["tin"] = str(
            supplier.get("tin", "")
        )

        invoice["supplier"]["address"] = str(
            supplier.get("address", "")
        )

        invoice["supplier"]["phone"] = str(
            supplier.get("phone", "")
        )

        invoice["supplier"]["email"] = str(
            supplier.get("email", "")
        )

    # -----------------------------------------------------
    # Invoice
    # -----------------------------------------------------

    invoice_data = data.get(
        "invoice",
        {}
    )

    if isinstance(invoice_data, dict):

        invoice["invoice"]["number"] = str(
            invoice_data.get("number", "")
        )

        invoice["invoice"]["date"] = clean_date(
            invoice_data.get("date", "")
        )

        invoice["invoice"]["payment_terms"] = str(
            invoice_data.get("payment_terms", "")
        )

        invoice["invoice"]["total_before_tax"] = clean_number(
            invoice_data.get("total_before_tax", 0)
        )

        invoice["invoice"]["tax_amount"] = clean_number(
            invoice_data.get("tax_amount", 0)
        )

        invoice["invoice"]["total_amount"] = clean_number(
            invoice_data.get("total_amount", 0)
        )

    # -----------------------------------------------------
    # Items
    # -----------------------------------------------------

    items = data.get("items", [])

    if isinstance(items, list):

        for item in items:

            if not isinstance(item, dict):
                continue

            cleaned_item = {
                "code": str(
                    item.get("code", "")
                ),

                "description": str(
                    item.get("description", "")
                ),

                "quantity": clean_number(
                    item.get("quantity", 0)
                ),

                "unit": str(
                    item.get("unit", "")
                ),

                "unit_price": clean_number(
                    item.get("unit_price", 0)
                ),

                "subtotal": clean_number(
                    item.get("subtotal", 0)
                )
            }

            invoice["items"].append(
                cleaned_item
            )

    return invoice


def extract_invoice(ocr_text):

    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=_get_secret("GEMINI_API_KEY")
    )

    prompt = f"""
You are an invoice data extraction system.

Your task is to extract structured information from OCR text taken from a supplier invoice.

IMPORTANT:
You are extracting information from a REAL invoice.

Follow these rules exactly.

SUPPLIER RULES:

1. Identify the company that ISSUED the invoice as the supplier.
2. Do NOT use the customer's information as supplier information.
3. Extract the supplier's:
   - company name
   - TIN
   - complete address
   - phone number
   - email address
4. If a supplier field is not present in the OCR text, leave it empty.
5. Never invent or guess supplier information.

INVOICE RULES:

6. Extract the invoice number exactly as shown.
7. Preserve leading zeros in invoice numbers.
8. Extract the invoice date.
9. Convert the date to YYYY-MM-DD format.
10. Extract payment terms if shown.
11. Extract the amount before tax.
12. Extract the tax amount.
13. Extract the final total invoice amount.
14. Do not use bank account numbers as invoice information.
15. Do not use payment instructions as invoice information.

LINE ITEM RULES:

16. THIS IS EXTREMELY IMPORTANT:
    Extract EVERY identifiable product line from the invoice.

17. Carefully scan the ENTIRE OCR text from beginning to end.

18. Do NOT stop after finding the first product.

19. If there are 3 product rows, the output MUST contain exactly 3 items.

20. For EVERY product line, extract:
    - product code
    - product description
    - quantity
    - unit
    - unit price
    - subtotal

21. Preserve product codes exactly as shown.

22. Preserve hyphens, numbers and letters in product codes.

23. Do not combine separate product rows.

24. Do not omit a product simply because the same product description appears more than once.

25. Quantity and unit must be separated.

26. Unit price and subtotal must be separated.

27. Do not mistake package size or weight information for quantity.

28. For example:
    "18.00 KG/CTN" is product/package information.
    If the invoice says "10.00 CTN", the quantity is 10 and the unit is CTN.

29. Do not treat customer information as a product.

30. Do not treat bank information as a product.

31. Do not treat tax lines, subtotal lines, shipping charges, payment instructions or notes as product items.

ACCURACY RULES:

32. Use ONLY information found in the OCR text.

33. NEVER invent information.

34. NEVER guess missing values.

35. If information is genuinely unavailable:
    - use an empty string for text fields
    - use 0 for numeric fields

36. Before returning the result, perform a second scan of the OCR text specifically looking for missed product rows.

37. Check that all identifiable product rows are represented in the items array.

38. Check that the final invoice total is the actual final total shown on the invoice.

39. Return ONLY structured JSON matching the provided schema.

OCR TEXT:
--------------------------------------------------
{ocr_text}
--------------------------------------------------
"""

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=INVOICE_SCHEMA
            )
        )

        data = json.loads(response.text)

        return validate_invoice(data)

    except Exception as error:

        # Covers API errors (auth, quota, network) as well as
        # malformed JSON coming back from the model - fail safe
        # to an empty invoice the user can fill in by hand, but
        # surface the real reason instead of failing silently.
        if st is not None:
            st.error(f"AI extraction failed: {error}")
        else:
            print(f"AI extraction failed: {error}")

        return empty_invoice()


if __name__ == "__main__":

    sample_ocr = """
    YANGON KL MARKETING SDN BHD
    (1091055-H)
    20140404969

    NO.7, JALAN INR 1,
    TAMAN INDUSTRI NAUTICAL,
    RAWANG 48000 SELANGOR

    TIN: C23515880010
    TEL: 603-6021 8833
    EMAIL: enquiry@ykl-marketing.com

    INVOICE

    Invoice No: 00016223
    Date: 28/07/2026
    Payment Terms: 45 Days

    CUSTOMER:
    SEA MARINEX TRADING
    ATTENTION: SYIFA

    CODE        DESCRIPTION                    QTY       UNIT PRICE       TOTAL

    TAS         TILAPIA FISH (1 CUT)          10 CTN       RM333          RM3330
                18.00 KG/CTN

    TAXL-15KG   TILAPIA FISH (1 CUT)          10 CTN       RM345          RM3450
                15.00 KG/CTN

    TAEXL        TILAPIA FISH (2 CUTS)         20 CTN       RM486          RM9720
                 18.00 KG/CTN

    TOTAL EXCLUDING TAX: RM16500
    TAX: RM0
    TOTAL DUE: RM16500

    RINGGIT MALAYSIA:
    SIXTEEN THOUSAND AND FIVE HUNDRED ONLY
    """

    print("Sending OCR text to AI...")

    result = extract_invoice(sample_ocr)

    print()
    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print()
    print(
        f"Items extracted: {len(result['items'])}"
    )