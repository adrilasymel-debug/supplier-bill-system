import platform
import pytesseract
from PIL import Image
from pathlib import Path


# On Streamlit Community Cloud (Linux), packages.txt installs
# tesseract-ocr via apt, and it's already on the system PATH - no
# manual path needed there. On Windows, tesseract isn't normally on
# PATH after installing, so point pytesseract straight at the exe.
if platform.system() == "Windows":

    WINDOWS_TESSERACT_PATH = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    if Path(WINDOWS_TESSERACT_PATH).exists():
        pytesseract.pytesseract.tesseract_cmd = WINDOWS_TESSERACT_PATH


def extract_text(image_path):
    image_path = Path(image_path)

    image = Image.open(image_path)

    text = pytesseract.image_to_string(image)

    return text


def extract_text_from_image(image):
    """
    Same as extract_text, but accepts an already-open PIL Image
    (or a file-like object PIL can open) instead of a filesystem
    path - avoids needing to write to local disk first.
    """

    if not isinstance(image, Image.Image):
        image = Image.open(image)

    return pytesseract.image_to_string(image)


def pdf_to_images(pdf_bytes, dpi=200):
    """
    Renders every page of a PDF into a PIL Image, so a multi-page
    invoice can be OCR'd page by page. Accepts raw PDF bytes
    (e.g. from st.file_uploader.getvalue()) - no temp file needed.
    Returns a list of PIL Images, one per page, in page order.
    """

    import fitz  # PyMuPDF

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    images = []

    for page in document:

        pixmap = page.get_pixmap(matrix=matrix)

        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples
        )

        images.append(image)

    document.close()

    return images


def extract_text_from_pages(images):
    """
    Runs OCR on a list of PIL Images (e.g. the pages of a PDF
    invoice) and joins the results into one text block, with a
    page marker between each page so a multi-page invoice stays
    readable and the AI extraction step can still tell where one
    page ends and the next begins.
    """

    page_texts = []

    for index, image in enumerate(images, start=1):

        text = pytesseract.image_to_string(image)

        page_texts.append(
            f"--- Page {index} of {len(images)} ---\n{text}"
        )

    return "\n\n".join(page_texts)


if __name__ == "__main__":
    print("OCR module is ready.")