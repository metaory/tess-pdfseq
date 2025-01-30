import os
import sys
import time
from pathlib import Path
from typing import Iterator, List

import cv2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

class Config:
    """Runtime configuration"""
    langs: str = os.getenv('OCR_LANGS', 'eng')
    dpi: int = int(os.getenv('DPI', '500'))
    target_width: int = int(os.getenv('TARGET_WIDTH', '1800'))
    max_pages: int = int(os.getenv('MAX_PAGES', '3'))
    dirname: Path = Path(__file__).parent.parent

def log(msg: str) -> None:
    """Simple logging with timestamp"""
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

def get_pages(pdf_path: Path) -> Iterator[Image.Image]:
    """Extract pages from PDF"""
    return (p for p in convert_from_path(str(pdf_path), Config.dpi)[:Config.max_pages])

def resize_page(page: Image.Image) -> Image.Image:
    """Resize page to target width while maintaining aspect ratio"""
    w, h = page.size
    scale = max(1, int(Config.target_width / w))
    return page.resize((scale * w, scale * h), Image.LANCZOS)

def process_img(img: Image.Image) -> cv2.Mat:
    """Process image for better OCR results"""
    cv_img = cv2.cvtColor(cv2.UMat(img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    kernel = cv2.UMat(cv2.Mat(1, 1, cv2.CV_8U))
    morph = cv2.morphologyEx(cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)
    return cv2.bitwise_or(gray, morph)

def extract_text(img: cv2.Mat) -> str:
    """Extract text from processed image"""
    return os.linesep.join(
        line for line in pytesseract.image_to_string(img, lang=Config.langs).splitlines()
        if line.strip()
    )

def process_pdf(pdf_path: Path) -> None:
    """Process a single PDF file"""
    log(f'Processing {pdf_path.name}')

    for i, page in enumerate(get_pages(pdf_path), 1):
        text = extract_text(process_img(resize_page(page)))
        out_path = Config.dirname / "output" / f"out_{pdf_path.stem}_p{i}.txt"
        out_path.write_text(text, encoding='utf-8')
        log(f'✓ Page {i} done')

def main() -> None:
    start = time.time()
    log(f'Using languages: {Config.langs}')

    pdfs = list((Config.dirname / "data").glob('*.pdf'))
    for pdf in pdfs:
        try:
            process_pdf(pdf)
            log(f'Done with {pdf.name}\n')
        except Exception as e:
            print(f'Error processing {pdf.name}: {e}', file=sys.stderr, flush=True)

    log(f'All done in {time.time() - start:.1f}s')

if __name__ == "__main__":
    main()
