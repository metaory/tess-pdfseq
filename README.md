<div align="center">
  <img src=".github/logo.svg" title="tess-pdfseq" width="128" />
  <h1>tess-pdfseq</h1>
</div>

Configurable OCR for documents in any language. Built with Tesseract and optimized for PDF processing.

## Features
- Process PDFs with high accuracy
- Support for any language Tesseract supports 
- Memory efficient processing
- Optional GPU acceleration via OpenCV
- Graceful fallback to CPU processing
- Docker-based deployment
- 7z archive support for batch processing

## Quick Start

```bash
# Build with default language (English)
docker build -t tess-pdfseq .

# Process a 7z archive (CPU mode)
./bin/pdfseq input.7z

# Process with GPU acceleration
GPU=1 ./bin/pdfseq input.7z

# Process with custom settings
LANGS="eng+ara" DPI=300 WIDTH=2400 GPU=1 ./bin/pdfseq docs.7z
```

## Configuration

### Shell Script Options
Environment variables for `bin/pdfseq`:
- `LANGS`: OCR languages (default: eng)
- `DPI`: PDF scan resolution (default: 500)
- `WIDTH`: Target width in pixels (default: 1800)
- `MAX_PAGES`: Max pages per PDF (default: 3)
- `WORKDIR`: Working directory (default: current directory)
- `GPU`: Enable GPU acceleration (default: 0)
- `TAG`: Docker image tag (default: latest)

### Languages

First, install languages during Docker build (plus-separated):
```bash
# Build with multiple languages available
docker build -t tess-pdfseq --build-arg TESS_LANGS="eng+fas+ara" .
```

Then use any of the installed languages at runtime:
```bash
# Use English (default)
./bin/pdfseq docs.7z

# Use Persian/Farsi
LANGS=fas ./bin/pdfseq docs.7z

# Use multiple languages together
LANGS="eng+fas" ./bin/pdfseq docs.7z
```

Note: You can only use languages at runtime that were installed during build.

List available languages:
```bash
# On Arch Linux
pacman -Ss tesseract-data | grep -Po 'tesseract-data-\K[^/\s]*(?=\s)'

# Using Docker
docker run --rm python:3.12-alpine sh -c \
  "apk add --no-cache tesseract-ocr && tesseract --list-langs"
```

Common languages:
- `eng` - English
- `heb` - Hebrew
- `jpn` - Japanese
- `kor` - Korean
- `rus` - Russian
- `fas` - Persian/Farsi
- `chi_sim` - Chinese Simplified

### Processing
- Optimizes images for OCR (1800px width)
- GPU acceleration with OpenCV UMat when enabled
- Automatic fallback to CPU if GPU fails
- Outputs plain text files

## Requirements
- Docker (GPU support optional)
- NVIDIA Container Toolkit for GPU support
- ~1GB disk space for Docker image
- p7zip for archive handling

## Development

```bash
git clone https://github.com/metaory/tess-pdfseq
cd tess-pdfseq

# Build with custom languages
docker build -t tess-pdfseq --build-arg TESS_LANGS="eng+ara" .
```

## License

[MIT](LICENSE)

