# PDF Title & Header Parser

A sophisticated PDF parsing solution designed for Adobe India Hackathon Challenge 1a. This tool intelligently extracts document titles and hierarchical header structures from PDF files using advanced font analysis and pattern recognition techniques.

## Features

- **Smart Title Detection**: Automatically identifies document titles using font size analysis and content filtering
- **Hierarchical Header Extraction**: Detects and classifies headers into H1 and H2 levels based on typography
- **Table of Contents Recognition**: Identifies and handles ToC sections appropriately
- **Noise Filtering**: Removes headers, footers, version numbers, dates, and tabular content
- **Font Analysis**: Determines paragraph font sizes for accurate content classification
- **Duplicate Prevention**: Avoids duplicate headers across pages and sections
- **Docker Support**: Containerized solution for consistent deployment

## Project Structure

```
AdobeIndiaHackathon25Sol1/
├── pdf_parser.py          # Main parsing logic
├── Dockerfile             # Docker configuration
├── README.md             # This file
└── sample_dataset/
    ├── pdfs/             # Input PDF files
    ├── outputs/          # Generated JSON outputs
    └── schema/           # Expected output schema
```

## Quick Start

### Method 1: Docker (Recommended)

1. **Build the Docker image:**
   ```bash
   docker build -t pdf-parser .
   ```

2. **Run with your PDF files:**
   ```bash
   docker run -v /path/to/your/pdfs:/app/input -v /path/to/output:/app/output pdf-parser
   ```

### Method 2: Local Python

1. **Install dependencies:**
   ```bash
   pip install pymupdf
   ```

2. **Modify input/output paths in the script and run:**
   ```bash
   python pdf_parser.py
   ```

## � Docker Instructions for Challenge 1a and 1b

This document explains how to build and run Docker containers for two projects:

- `pdf_parser.py` (Challenge 1a)
- `pdf_analyzer.py` (Challenge 1b)

---

### PROJECT 1: `pdf_parser.py` (Challenge 1a)

#### Dockerfile Summary:
- Mount `sample_dataset/pdfs` → `/app/input` (read-only)
- Mount `sample_dataset/outputs` → `/app/output` (writable)
- Output: JSON files in `/sample_dataset/outputs`

#### 🔧 1. Build Image (Same on all platforms)

```bash
docker build --platform linux/amd64 -t pdf-processor .
```

#### ▶️ 2. Run Container

| Environment         | Run Command                                                                                         |
|---------------------|-----------------------------------------------------------------------------------------------------|
| **Windows CMD**      | `docker run --rm -v "%cd%\sample_dataset\pdfs:/app/input:ro" -v "%cd%\sample_dataset\outputs:/app/output" --network none pdf-processor` |
| **Windows PowerShell** | `docker run --rm -v "${PWD}\sample_dataset\pdfs:/app/input:ro" -v "${PWD}\sample_dataset\outputs:/app/output" --network none pdf-processor` |
| **macOS / Linux**     | `docker run --rm -v "$(pwd)/sample_dataset/pdfs:/app/input:ro" -v "$(pwd)/sample_dataset/outputs:/app/output" --network none pdf-processor` |
| **WSL (Ubuntu)**      | Same as macOS/Linux                                                                                 |

---

### PROJECT 2: `pdf_analyzer.py` (Challenge 1b)

#### Dockerfile Summary:
- Mount entire project directory to `/app`
- Expects:
  - `Collection 1`, `Collection 2`, `Collection 3`
  - Each with `challenge1b_input.json` and `PDFs/`
- Output: `challenge1b_output.json` inside each collection

#### 1. Build Image (Same on all platforms)

```bash
docker build -t pdf-analyzer .
```

#### 2. Run Container (All Collections)

| Environment         | Run Command                                                   |
|---------------------|---------------------------------------------------------------|
| **Windows CMD**      | `docker run --rm -v "%cd%:/app" pdf-analyzer`                 |
| **Windows PowerShell** | `docker run --rm -v "${PWD}:/app" pdf-analyzer`                |
| **macOS / Linux**     | `docker run --rm -v "$(pwd):/app" pdf-analyzer`              |
| **WSL (Ubuntu)**      | Same as macOS/Linux                                          |

#### 3. Run Container (Specific Collections)

| Shell             | Example Command                                                                 |
|------------------|----------------------------------------------------------------------------------|
| **CMD**           | `docker run --rm -v "%cd%:/app" pdf-analyzer --collections "Collection 1"`       |
| **PowerShell**    | `docker run --rm -v "${PWD}:/app" pdf-analyzer --collections "Collection 1"`     |
| **macOS/Linux**   | `docker run --rm -v "$(pwd):/app" pdf-analyzer --collections "Collection 1"`     |
| **WSL**           | Same as macOS/Linux                                                              |

---

## How It Works

### Core Components

1. **PDFTitleHeaderParser Class**: Main parsing engine with multiple analysis modules

2. **Font Analysis Engine**: 
   - Analyzes font characteristics across the document
   - Identifies the most common paragraph font size
   - Uses font size hierarchy for header classification

3. **Content Filtering System**:
   - Detects and excludes headers/footers
   - Identifies table elements and version information
   - Recognizes ToC sections and navigation elements

4. **Header Classification**:
   - **H1**: Larger font sizes than paragraph text
   - **H2**: Same font size as paragraphs but bold, limited word count

### Intelligent Detection Features

- **Table Element Detection**: Identifies tabular structures using pattern matching and neighbor analysis
- **ToC Section Handling**: Recognizes table of contents and processes it separately
- **Duplicate Prevention**: Tracks seen headers to avoid repetition
- **Title Extraction**: Uses font size priority to identify main document title

## Output Format

The parser generates JSON files with the following structure:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Main Section Header",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "Subsection Header",
      "page": 2
    }
  ]
}
```

## 🎯 Algorithm Details

### Title Detection Process
1. Filter out headers, footers, and noise elements
2. Exclude paragraph text and table content
3. Rank candidates by font size
4. Select highest font size element as title

### Header Classification Logic
```python
if font_size > paragraph_font_size:
    return "H1"
elif font_size == paragraph_font_size and is_bold and word_count <= 10:
    return "H2"
else:
    return "paragraph"
```

### Noise Filtering Patterns
- Headers/Footers: Page numbers, dates, copyrights
- Version Info: Version numbers, document IDs, revisions
- Table Elements: Tabular data, structured content
- Navigation: Dots, dashes, ToC entries

## Technical Implementation

### Key Technologies
- **PyMuPDF (fitz)**: PDF text extraction and font analysis
- **Regular Expressions**: Pattern matching for content classification
- **Python Collections**: Efficient data structure management

### Performance Optimizations
- Font analysis caching
- Element classification batching
- Duplicate detection using sets
- Page-wise processing for memory efficiency

## Accuracy Features

1. **Multi-pass Analysis**: Separate passes for font analysis and content extraction
2. **Context-aware Classification**: Considers neighboring elements for table detection
3. **Robust Pattern Matching**: Handles various document formats and languages
4. **Edge Case Handling**: Manages documents without clear hierarchies

## Example Usage

```python
from pdf_parser import PDFTitleHeaderParser, extract_elements_from_pdf

# Extract elements from PDF
elements = extract_elements_from_pdf("document.pdf")

# Initialize parser
parser = PDFTitleHeaderParser()

# Parse and get results
result = parser.parse_pdf_data(elements)

print(f"Title: {result['title']}")
print(f"Headers found: {len(result['outline'])}")
```

## Troubleshooting

### Common Issues

1. **No headers detected**: Document may use non-standard formatting
2. **Incorrect title**: Multiple large font elements on first page
3. **Missing headers**: Headers may be in tables or have unusual formatting

### Debug Tips

- Check `font_analysis` output for font distribution
- Verify `paragraph_font_size` detection
- Review filtered elements in `table_elements` set

## 📋 Requirements

- Python 3.7+
- PyMuPDF (fitz) library
- Docker (optional, for containerized deployment)

## Challenge Alignment

This solution addresses Adobe India Hackathon Challenge 1a requirements:

- **Title Extraction**: Intelligent font-based title detection
- **Header Hierarchy**: Multi-level header classification (H1, H2)
- **JSON Output**: Structured output format as specified
- **Robustness**: Handles various PDF formats and edge cases
- **Accuracy**: Advanced filtering and classification algorithms


## License

This project is developed for the Adobe India Hackathon 2025.

---

*Built with ❤️ for Adobe India Hackathon 2025*
