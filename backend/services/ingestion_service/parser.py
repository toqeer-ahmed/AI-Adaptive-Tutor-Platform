import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple

class DocumentParser:
    @staticmethod
    def parse_pdf(content: bytes) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Parses PDF content page by page.
        Returns (pages_data, needs_ocr).
        Each page_data contains {"page_number": int, "text": str, "section": str}.
        """
        pages = []
        needs_ocr = False

        text_content = content.decode("latin1", errors="ignore")
        page_splits = re.split(r"/Type\s*/Page\b", text_content)

        if len(page_splits) <= 1:
            raw_text_blocks = re.findall(r"\((.*?)\)\s*TJ|\((.*?)\)\s*Tj", text_content)
            extracted_text = " ".join([b[0] or b[1] for b in raw_text_blocks if (b[0] or b[1])])
            if not extracted_text.strip():
                needs_ocr = True
                extracted_text = "[Scanned document page - OCR required]"
            pages.append({"page_number": 1, "text": extracted_text, "section": "Page 1"})
        else:
            page_num = 1
            for page_str in page_splits[1:]:
                raw_text_blocks = re.findall(r"\((.*?)\)\s*TJ|\((.*?)\)\s*Tj", page_str)
                extracted_text = " ".join([b[0] or b[1] for b in raw_text_blocks if (b[0] or b[1])])
                if len(extracted_text.strip()) < 10:
                    needs_ocr = True
                    extracted_text = f"[Scanned page {page_num} - OCR required]"
                pages.append({"page_number": page_num, "text": extracted_text, "section": f"Page {page_num}"})
                page_num += 1

        return pages, needs_ocr

    @staticmethod
    def parse_docx(content: bytes) -> List[Dict[str, Any]]:
        """
        Parses DOCX document paragraphs and headings.
        """
        pages = []
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                xml_content = z.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                
                paragraphs = []
                current_section = "General"
                
                for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                    full_p = ''.join(texts).strip()
                    if full_p:
                        if len(full_p) < 60 and (full_p.isupper() or "Chapter" in full_p or "Section" in full_p):
                            current_section = full_p
                        paragraphs.append({"text": full_p, "section": current_section})

                page_size = 5
                page_num = 1
                for i in range(0, len(paragraphs), page_size):
                    chunk_ps = paragraphs[i:i+page_size]
                    page_text = "\n".join([p["text"] for p in chunk_ps])
                    sec = chunk_ps[0]["section"]
                    pages.append({"page_number": page_num, "text": page_text, "section": sec})
                    page_num += 1
        except Exception as e:
            txt = content.decode("utf-8", errors="ignore")
            pages.append({"page_number": 1, "text": txt, "section": "Main"})

        return pages

    @staticmethod
    def parse_txt(content: bytes) -> List[Dict[str, Any]]:
        text = content.decode("utf-8", errors="ignore")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        pages = []
        chunk_size = 10
        page_num = 1
        for i in range(0, len(lines), chunk_size):
            block = "\n".join(lines[i:i+chunk_size])
            pages.append({"page_number": page_num, "text": block, "section": f"Section {page_num}"})
            page_num += 1
        return pages

class DocumentChunker:
    @staticmethod
    def chunk_pages(pages: List[Dict[str, Any]], target_chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Structure-aware chunker preserving page_number and section metadata.
        """
        chunks = []
        chunk_index = 0

        for page in pages:
            text = page["text"]
            page_num = page["page_number"]
            section = page["section"]

            if len(text) <= target_chunk_size:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": text,
                    "page_number": page_num,
                    "section": section
                })
                chunk_index += 1
            else:
                start = 0
                while start < len(text):
                    end = start + target_chunk_size
                    chunk_text = text[start:end]
                    chunks.append({
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "page_number": page_num,
                        "section": section
                    })
                    chunk_index += 1
                    start += (target_chunk_size - overlap)

        return chunks
