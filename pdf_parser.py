import fitz  # PyMuPDF
import re
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional


class PDFTitleHeaderParser:
    def __init__(self):
        self.title = None
        self.title_page = None
        self.outline = []
        self.content = []
        self.font_analysis = {}
        self.paragraph_font_size = 12
        self.in_toc_section = False
        self.seen_headers = set()
        self.table_elements = set()
        self.toc_patterns = [
            r'table\s+of\s+contents',
            r'contents',
            r'index',
            r'table\s+des\s+matières',
            r'sommaire'
        ]

    def detect_table_elements(self, elements: List[Dict]) -> None:
        page_elements = defaultdict(list)
        for i, element in enumerate(elements):
            page_elements[element.get('page', 1)].append((i, element))
        for page_elems in page_elements.values():
            page_elems.sort(key=lambda x: x[0])
            for i in range(len(page_elems)):
                idx, element = page_elems[i]
                if self.is_table_element(element, elements, idx):
                    self.table_elements.add(idx)

    def is_table_element(self, element: Dict, all_elements: List[Dict], element_idx: int) -> bool:
        text = element.get('text', '').strip().lower()
        table_indicators = [
            r'^(version|date|remarks|identifier|reference|days|syllabus)$',
            r'^\d+\.\d+$',
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',
            r'^v?\d+\.\d+(\.\d+)?$',
            r'^rev\s+\d+$',
            r'^revision\s+\d+$'
        ]
        if any(re.match(pattern, text) for pattern in table_indicators):
            return True
        return self.is_in_tabular_structure(element, all_elements, element_idx) or self.has_tabular_neighbors(element, all_elements, element_idx)

    def is_in_tabular_structure(self, element: Dict, all_elements: List[Dict], element_idx: int) -> bool:
        page = element.get('page', 1)
        font_size = element.get('font_size', 12)
        same_page_elements = [
            (i, e) for i, e in enumerate(all_elements)
            if e.get('page') == page and abs(i - element_idx) <= 10
        ]
        table_header_count = 0
        short_entries_count = 0
        for _, elem in same_page_elements:
            txt = elem.get('text', '').strip().lower()
            elem_font = elem.get('font_size', 12)
            if any(header in txt for header in ['version', 'date', 'remarks']):
                table_header_count += 1
            if len(txt.split()) <= 3 and elem_font == font_size:
                short_entries_count += 1
        return table_header_count >= 2 and short_entries_count >= 3

    def has_tabular_neighbors(self, element: Dict, all_elements: List[Dict], element_idx: int) -> bool:
        page = element.get('page', 1)
        for i in range(max(0, element_idx - 5), min(len(all_elements), element_idx + 6)):
            if i == element_idx or all_elements[i].get('page') != page:
                continue
            neighbor_text = all_elements[i].get('text', '').strip().lower()
            if re.match(r'^(version|date|remarks|identifier|reference)$', neighbor_text):
                return True
        return False

    def is_header_footer(self, element: Dict) -> bool:
        text = element.get('text', '').strip().lower()
        patterns = [
            r'page\s+\d+', r'^\d+$', r'chapter\s+\d+',
            r'©\s*\d{4}', r'confidential', r'document\s+id',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        ]
        return any(re.search(p, text) for p in patterns) or (len(text) <= 10 and re.match(r'^[\d\s\-/\.]+$', text))

    def is_version_or_date(self, element: Dict) -> bool:
        text = element.get('text', '').strip().lower()
        patterns = [
            r'^v\d+\.\d+', r'^version\s+\d+', r'^rev\s+\d+',
            r'^\d+\.\d+\.\d+', r'^date:', r'^created:', r'^updated:'
        ]
        return any(re.match(p, text) for p in patterns)

    def is_dots_or_dashes(self, element: Dict) -> bool:
        text = re.sub(r'\s', '', element.get('text', '').strip())
        return len(text) >= 3 and re.match(r'^[.\-_=*~]{3,}$', text)

    def is_table_of_contents_header(self, element: Dict) -> bool:
        text = element.get('text', '').strip().lower()
        return any(re.search(p, text) for p in self.toc_patterns)

    def is_toc_content(self, element: Dict) -> bool:
        text = element.get('text', '').strip()
        patterns = [
            r'^\d+\.?\s*$', r'^\d+\.\d+', r'\.\.\.\.\.', r'^.+\s+\d+$'
        ]
        return any(re.search(p, text) for p in patterns)

    def analyze_font_characteristics(self, elements: List[Dict]) -> None:
        font_data = defaultdict(lambda: {'count': 0, 'total_chars': 0, 'pages': set()})
        for element in elements:
            if self.is_header_footer(element) or self.is_version_or_date(element) or self.is_dots_or_dashes(element):
                continue
            font_size = element.get('font_size', 12)
            text = element.get('text', '').strip()
            page = element.get('page', 1)
            font_data[font_size]['count'] += 1
            font_data[font_size]['total_chars'] += len(text)
            font_data[font_size]['pages'].add(page)
        candidates = [(v['total_chars'] * len(v['pages']), k) for k, v in font_data.items()]
        if candidates:
            candidates.sort(reverse=True)
            self.paragraph_font_size = candidates[0][1]
        self.font_analysis = {k: dict(v, pages=len(v['pages'])) for k, v in font_data.items()}

    def is_paragraph_text(self, element: Dict) -> bool:
        font_size = element.get('font_size', 12)
        is_bold = element.get('bold', False)
        text = element.get('text', '').strip()
        if font_size == self.paragraph_font_size and not is_bold:
            return True
        if font_size == self.paragraph_font_size and is_bold:
            if '\n' in text or len(text.split()) > 15:
                return True
        return False

    def identify_title(self, elements: List[Dict]) -> Optional[Dict]:
        candidates = []
        for e in elements:
            if self.is_header_footer(e) or self.is_version_or_date(e) or self.is_dots_or_dashes(e) or self.is_paragraph_text(e):
                continue
            txt = e.get('text', '').strip()
            if len(txt) >= 3:
                candidates.append((e.get('font_size', 12), e.get('page', 1), txt, e))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][3]

    def classify_header_level(self, element: Dict) -> Optional[str]:
        if self.is_paragraph_text(element):
            return None
        font_size = element.get('font_size', 12)
        is_bold = element.get('bold', False)
        text = element.get('text', '').strip()
        title_font_size = self.title.get('font_size', 16) if self.title else 16
        if font_size >= title_font_size:
            return None
        elif font_size > self.paragraph_font_size:
            return "H1"
        elif font_size == self.paragraph_font_size and is_bold and len(text.split()) <= 10:
            return "H2"
        return None

    def extract_clean_title(self, title_element: Dict) -> str:
        return re.sub(r'\s+', ' ', title_element.get('text', '').strip()) if title_element else "Untitled Document"

    def should_include_header(self, text: str, page: int) -> bool:
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        if normalized in {'overview', 'introduction', 'summary'}:
            if normalized in self.seen_headers:
                return False
            self.seen_headers.add(normalized)
        key = f"{normalized}_{page}"
        if key in self.seen_headers:
            return False
        self.seen_headers.add(key)
        return True

    def parse_pdf_data(self, elements: List[Dict]) -> Dict:
        self.__init__()
        self.detect_table_elements(elements)
        self.analyze_font_characteristics(elements)
        self.title = self.identify_title(elements)
        self.title_page = self.title.get('page', 1) if self.title else None

        for i, e in enumerate(elements):
            text = e.get('text', '').strip()
            page = e.get('page', 1)
            if not text or i in self.table_elements:
                continue
            if (self.is_header_footer(e) or self.is_version_or_date(e) or self.is_dots_or_dashes(e)):
                continue
            if self.title and text == self.title.get('text') and page == self.title.get('page'):
                continue
            if self.is_table_of_contents_header(e):
                self.in_toc_section = True
                level = self.classify_header_level(e)
                if level and self.should_include_header(text, page):
                    self.outline.append({"level": level, "text": text, "page": page})
                continue
            if self.in_toc_section:
                if self.is_toc_content(e):
                    continue
                else:
                    level = self.classify_header_level(e)
                    if level:
                        self.in_toc_section = False
                    else:
                        continue
            level = self.classify_header_level(e) if page != self.title_page else None
            if level and self.should_include_header(text, page):
                self.outline.append({"level": level, "text": text, "page": page})
            self.content.append({"text": text, "page": page, "type": "paragraph"})

        return {
            "title": self.extract_clean_title(self.title),
            "outline": self.outline
        }


def extract_elements_from_pdf(file_path: str) -> List[Dict]:
    doc = fitz.open(file_path)
    elements = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                text = ""
                max_font = 0
                bold = False
                for span in line.get("spans", []):
                    if span["text"].strip():
                        text += span["text"].strip() + " "
                        max_font = max(max_font, span["size"])
                        if "bold" in span["font"].lower():
                            bold = True
                if text.strip():
                    elements.append({
                        "text": text.strip(),
                        "font_size": round(max_font, 1),
                        "bold": bold,
                        "page": page_num + 1
                    })
    return elements


def process_pdfs():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in input_dir.glob("*.pdf"):
        output_path = output_dir / f"{pdf_path.stem}.json"
        print(f"📄 Processing: {pdf_path.name}")
        elements = extract_elements_from_pdf(str(pdf_path))
        parser = PDFTitleHeaderParser()
        result = parser.parse_pdf_data(elements)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved to: {output_path}\n")


if __name__ == "__main__":
    process_pdfs()
