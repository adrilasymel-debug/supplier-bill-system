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


if __name__ == "__main__":
    print("OCR module is ready.")