import os
import sys
import time
from pathlib import Path
from typing import Iterator, List
import numpy as np
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
    use_gpu: bool = bool(int(os.getenv('GPU', '0')))

def log(msg: str, level: str = 'info') -> None:
    """Enhanced logging with timestamp and color"""
    colors = {
        'info': '\033[36m',  # cyan
        'debug': '\033[2m',  # dim
        'warn': '\033[33m',  # yellow
        'error': '\033[31m'  # red
    }
    color = colors.get(level, '')
    reset = '\033[0m'
    ts = time.strftime("%H:%M:%S")
    print(f'[{ts}] {color}{msg}{reset}', flush=True)

def debug(msg: str) -> None:
    """Debug level logging with indentation"""
    log(f'  {msg}', 'debug')

def get_pages(pdf_path: Path) -> Iterator[Image.Image]:
    """Extract pages from PDF"""
    log(f'Processing PDF: {pdf_path.name}')
    pages = list(convert_from_path(str(pdf_path), Config.dpi)[:Config.max_pages])
    debug(f'Extracted {len(pages)} pages at {Config.dpi} DPI')
    return (p for p in pages)

def resize_page(page: Image.Image) -> Image.Image:
    """Resize page to target width while maintaining aspect ratio"""
    w, h = page.size
    scale = max(1, int(Config.target_width / w))
    new_size = (scale * w, scale * h)
    debug(f'Resizing page from {w}x{h} to {new_size[0]}x{new_size[1]}')
    return page.resize(new_size, Image.LANCZOS)

def process_img(img: Image.Image) -> cv2.Mat:
    """Process image for better OCR results"""
    debug('Converting to OpenCV format')
    # Convert PIL Image to numpy array first
    np_img = np.array(img)

    # Use UMat for GPU acceleration if enabled
    if Config.use_gpu:
        debug('Using GPU acceleration')
        cv_img = cv2.UMat(cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR))
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((1,1), np.uint8)
        kernel_umat = cv2.UMat(kernel)
    else:
        debug('Using CPU processing')
        cv_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((1,1), np.uint8)

    debug('Converting to grayscale')
    debug('Applying morphological operations')
    try:
        if Config.use_gpu:
            morph = cv2.morphologyEx(cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_umat),
                                   cv2.MORPH_CLOSE, kernel_umat)
        else:
            morph = cv2.morphologyEx(cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel),
                                   cv2.MORPH_CLOSE, kernel)

        result = cv2.bitwise_or(gray, morph)
        if Config.use_gpu:
            result = result.get()  # Download from GPU if needed
        return result
    except cv2.error as e:
        log(f'OpenCV error: {e}', 'error')
        log('Falling back to grayscale only', 'warn')
        return gray.get() if Config.use_gpu else gray

def extract_text(img: cv2.Mat) -> str:
    """Extract text from processed image"""
    debug('Running Tesseract OCR')
    text = pytesseract.image_to_string(img, lang=Config.langs)
    lines = [line for line in text.splitlines() if line.strip()]
    debug(f'Extracted {len(lines)} lines of text')
    return os.linesep.join(lines)

def process_pdf(pdf_path: Path) -> None:
    """Process a single PDF file"""
    log(f'Processing PDF: {pdf_path.name}')
    start = time.time()
    total_chars = 0
    total_lines = 0

    for i, page in enumerate(get_pages(pdf_path), 1):
        page_start = time.time()
        log(f'Page {i}:', 'debug')

        debug('Resizing page...')
        resized = resize_page(page)

        debug('Processing image...')
        processed = process_img(resized)

        debug('Extracting text...')
        text = extract_text(processed)
        lines = text.splitlines()
        chars = sum(len(line) for line in lines)

        out_path = Config.dirname / "output" / f"out_{pdf_path.stem}_p{i}.txt"
        out_path.write_text(text, encoding='utf-8')

        page_time = time.time() - page_start
        total_chars += chars
        total_lines += len(lines)

        log(f'✓ Page {i} done in {page_time:.1f}s ({len(lines)} lines, {chars} chars)', 'info')

    duration = time.time() - start
    avg_time = duration / i if i > 0 else 0
    log(f'Completed {pdf_path.name} in {duration:.1f}s')
    debug(f'Average {avg_time:.1f}s per page')
    debug(f'Total: {total_lines} lines, {total_chars} chars')

def main() -> None:
    start = time.time()
    log('Starting OCR process')
    debug(f'Languages: {Config.langs}')
    debug(f'DPI: {Config.dpi}')
    debug(f'Target width: {Config.target_width}')
    debug(f'Max pages: {Config.max_pages}')
    debug(f'GPU acceleration: {"enabled" if Config.use_gpu else "disabled"}')

    pdfs = list((Config.dirname / "data").glob('*.pdf'))
    debug(f'Found {len(pdfs)} PDF files')

    for pdf in pdfs:
        try:
            process_pdf(pdf)
        except Exception as e:
            log(f'Error processing {pdf.name}: {e}', 'error')

    duration = time.time() - start
    log(f'All done in {duration:.1f}s')

if __name__ == "__main__":
    main()
