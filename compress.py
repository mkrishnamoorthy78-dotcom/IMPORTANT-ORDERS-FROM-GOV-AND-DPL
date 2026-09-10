import io
import os
from PIL import Image
import fitz  # PyMuPDF

import gc

QUALITY = int(os.environ.get("COMPRESSION_QUALITY", 70))
MAX_IMAGE_DIM = 2000
PDF_DPI = int(os.environ.get("PDF_DPI", 120))


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


def _adaptive_dpi(page_count: int) -> int:
    """Lower DPI for PDFs with many pages to keep peak memory bounded
    on low-RAM hosts (e.g. Render free tier's 512MB)."""
    if page_count > 60:
        return 70
    if page_count > 30:
        return 90
    if page_count > 15:
        return 100
    return PDF_DPI


MAX_PAGE_PX = 1600  # cap the longer side of any rendered page to this many pixels


def _dpi_for_page_size(page, target_dpi: int) -> int:
    """Even at a 'safe' DPI, a physically large page (A3/legal/broadsheet
    scans) can still render to a huge pixmap. Cap the DPI further so the
    longer side never exceeds MAX_PAGE_PX pixels, regardless of page size."""
    longer_side_inches = max(page.rect.width, page.rect.height) / 72.0
    if longer_side_inches <= 0:
        return target_dpi
    max_dpi_for_size = int(MAX_PAGE_PX / longer_side_inches)
    return max(40, min(target_dpi, max_dpi_for_size))


def compress_pdf(file_bytes: bytes) -> bytes:
    src = fitz.open(stream=file_bytes, filetype="pdf")
    out = fitz.open()
    base_dpi = _adaptive_dpi(src.page_count)

    for page in src:
        dpi = _dpi_for_page_size(page, base_dpi)
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)

        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, alpha=False)
        # Encode directly to JPEG via PyMuPDF - avoids a Pillow round-trip
        # and the extra copy of raw pixel data that entails.
        img_bytes = pix.tobytes("jpeg", jpg_quality=QUALITY)

        new_page = out.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=img_bytes)

        pix = None
        img_bytes = None
        gc.collect()

    compressed = out.tobytes(deflate=True, garbage=4)
    out.close()
    src.close()
    gc.collect()
    return compressed


def compress_file(file_bytes: bytes, file_type: str) -> bytes:
    """file_type is 'pdf' or 'jpg'/'png' etc."""
    if file_type == "pdf":
        return compress_pdf(file_bytes)
    return compress_image(file_bytes)
