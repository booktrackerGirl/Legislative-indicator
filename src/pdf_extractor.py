import requests
import fitz
import pytesseract
import threading
import time
import numpy as np
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# Timeout Wrapper (Safe)
# ============================================================

def run_with_timeout(func, args=(), timeout=60):
    result = [None]

    def target():
        try:
            result[0] = func(*args)
        except Exception:
            result[0] = None

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return None

    return result[0]


# ============================================================
# Smart Request
# ============================================================

def smart_get(url, timeout=30, verify=True):

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/pdf,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    try:
        session = requests.Session()
        r = session.get(url, headers=headers, timeout=timeout, verify=verify)

        if r.status_code == 200:
            return r

        headers["Referer"] = url
        r = session.get(url, headers=headers, timeout=timeout, verify=verify)

        if r.status_code == 200:
            return r

        return None

    except:
        return None


# ============================================================
#                  PRODUCTION PDF EXTRACTOR
# ============================================================

class PDFExtractor:

    def __init__(self):
        self.failed_urls = []

    # ============================================================
    # PUBLIC ENTRY
    # ============================================================

    def extract(self, url, fallback_url=None):

        urls_to_try = [url]
        if fallback_url and fallback_url != url:
            urls_to_try.append(fallback_url)

        for current_url in urls_to_try:

            # ===============================
            # 1️⃣ Domain-Specific Handlers
            # ===============================
            if "parliament.gov.zm" in current_url:
                result = self._extract_zambia_parliament_pdf(current_url)
                if self._valid(result):
                    return result

            if "planalto.gov.br" in current_url:
                result = self._extract_brazil_planalto(current_url)
                if self._valid(result):
                    return result

            if "suin-juriscol.gov.co" in current_url:
                result = self._extract_colombia_suin(current_url)
                if self._valid(result):
                    return result

            if current_url.lower().endswith((".doc", ".docx")):
                result = self._extract_doc_file(current_url)
                if self._valid(result):
                    return result

            # ===============================
            # 2️⃣ Fast PDF Methods
            # ===============================
            for method in [
                self._extract_direct_pdf,
                self._extract_google_redirect_pdf,
                self._extract_pdf_with_retries,
                self._extract_pdf_ignore_ssl,
                self._extract_via_pdf_links,
            ]:
                result = run_with_timeout(method, args=(current_url,), timeout=45)
                if self._valid(result):
                    return result

            # ===============================
            # 3️⃣ HTML Fallback
            # ===============================
            result = run_with_timeout(self._extract_html_page, args=(current_url,), timeout=30)
            if self._valid(result):
                return result

            # ===============================
            # 4️⃣ Browser Last Resort
            # ===============================
            result = run_with_timeout(self._extract_with_browser, args=(current_url,), timeout=60)
            if self._valid(result):
                return result

        self.failed_urls.append(url)
        return None

    # ============================================================
    # VALIDATION
    # ============================================================

    def _valid(self, result):
        if not result or not isinstance(result, dict):
            return False
        text = result.get("text", "")
        return isinstance(text, str) and len(text.strip()) > 600

    # ============================================================
    # DIRECT PDF
    # ============================================================

    def _extract_direct_pdf(self, url):
        r = smart_get(url)
        if not r:
            return None

        if not r.content.startswith(b"%PDF"):
            return None

        result = self._smart_pdf_extract(r.content)
        if result:
            result["metadata"]["ssl_bypassed"] = True
        return result

    # ============================================================
    # GOOGLE REDIRECT
    # ============================================================

    def _extract_google_redirect_pdf(self, url):
        if "google.com" not in url:
            return None
        return self._extract_direct_pdf(url)

    # ============================================================
    # RETRY
    # ============================================================

    def _extract_pdf_with_retries(self, url):
        for _ in range(2):
            result = self._extract_direct_pdf(url)
            if result:
                return result
        return None

    # ============================================================
    # SSL BYPASS
    # ============================================================

    def _extract_pdf_ignore_ssl(self, url):
        r = smart_get(url, verify=False)
        if not r:
            return None

        if not r.content.startswith(b"%PDF"):
            return None

        return self._smart_pdf_extract(r.content)

    # ============================================================
    # HTML → FIND PDF LINK
    # ============================================================

    def _extract_via_pdf_links(self, url):
        r = smart_get(url)
        if not r:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        for link in soup.find_all("a", href=True):
            if ".pdf" in link["href"].lower():
                pdf_url = urljoin(url, link["href"])
                return self._extract_direct_pdf(pdf_url)

        return None

    # ============================================================
    # HTML PAGE TEXT
    # ============================================================

    def _extract_html_page(self, url):
        r = smart_get(url)
        if not r:
            return None

        if r.content.startswith(b"%PDF"):
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n")

        if len(text.strip()) > 1000:
            return {
                "text": text.strip(),
                "metadata": {"source": "html"}
            }

        return None

    # ============================================================
    # SMART PDF CORE (Embedded → Controlled OCR)
    # ============================================================

    def _smart_pdf_extract(self, pdf_bytes):

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            if len(doc) > 80:
                doc.close()
                return None

            # Embedded first
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())

            embedded = "\n".join(text_parts)

            if len(embedded.strip()) > 1500:
                doc.close()
                return {
                    "text": embedded.strip(),
                    "metadata": {"source": "embedded_pdf"}
                }

            # Controlled OCR fallback
            MAX_OCR_PAGES = 15
            DPI = 150

            ocr_parts = []

            for i in range(min(len(doc), MAX_OCR_PAGES)):
                page = doc[i]
                pix = page.get_pixmap(dpi=DPI)
                img = Image.open(BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img)
                ocr_parts.append(text)
                img.close()

            doc.close()

            ocr_text = "\n".join(ocr_parts)

            if len(ocr_text.strip()) > 800:
                return {
                    "text": ocr_text.strip(),
                    "metadata": {"source": "ocr_pdf"}
                }

            return None

        except:
            return None

    # ============================================================
    # PLACEHOLDER SPECIAL HANDLERS
    # (Keep your existing implementations here)
    # ============================================================

    def _extract_zambia_parliament_pdf(self, url):
        return None

    def _extract_brazil_planalto(self, url):
        return None

    def _extract_colombia_suin(self, url):
        return None

    def _extract_doc_file(self, url):
        return None

    # ============================================================
    # LIGHTWEIGHT BROWSER (LAST RESORT)
    # ============================================================

    def _extract_with_browser(self, url):

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=60000)
                page.wait_for_timeout(3000)

                content = page.content()
                browser.close()

            soup = BeautifulSoup(content, "html.parser")
            text = soup.get_text(separator="\n")

            if len(text.strip()) > 1000:
                return {
                    "text": text.strip(),
                    "metadata": {"source": "browser"}
                }

            return None

        except:
            return None