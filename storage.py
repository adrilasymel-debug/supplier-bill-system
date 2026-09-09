import os

from supabase import create_client

try:
    import streamlit as st
except ImportError:
    st = None


BUCKET_NAME = "invoice-photos"


def _get_secret(key):

    if st is not None:

        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass

    return os.environ.get(key)


_client = None


def get_client():

    global _client

    if _client is None:

        _client = create_client(
            _get_secret("SUPABASE_URL"),
            _get_secret("SUPABASE_SERVICE_KEY"),
        )

    return _client


def upload_invoice_image(file_name, file_bytes, content_type="image/jpeg"):
    """
    Uploads invoice photo bytes to Supabase Storage and returns
    the public URL to store in invoices.image_path.
    """

    client = get_client()

    client.storage.from_(BUCKET_NAME).upload(
        file_name,
        file_bytes,
        {
            "content-type": content_type,
            "upsert": "true",
        },
    )

    return client.storage.from_(BUCKET_NAME).get_public_url(file_name)
