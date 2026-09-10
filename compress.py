import io
import os
from PIL import Image
import fitz  # PyMuPDF

QUALITY = int(os.environ.get("COMPRESSION_QUALITY", 70))
MAX_IMAGE_DIM = 2000
PDF_DPI = 150


def compress_image(file_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(file_bytes))
    img = img.convert("RGB")
    if max(img.size) > MAX_IMAGE_DIM:
        ratio = MAX_IMAGE_DIM / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=QUALITY, optimize=True)
    return buf.getvalue()


def compress_pdf(file_bytes: bytes) -> bytes:
    src = fitz.open(stream=file_bytes, filetype="pdf")
    out = fitz.open()
    zoom = PDF_DPI / 72
    mat = fitz.Matrix(zoom, zoom)

    for page in src:
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=QUALITY, optimize=True)
        buf.seek(0)

        new_page = out.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=buf.read())

    compressed = out.tobytes(deflate=True, garbage=4)
    out.close()
    src.close()
    return compressed


def compress_file(file_bytes: bytes, file_type: str) -> bytes:
    """file_type is 'pdf' or 'jpg'/'png' etc."""
    if file_type == "pdf":
        return compress_pdf(file_bytes)
    return compress_image(file_bytes)
