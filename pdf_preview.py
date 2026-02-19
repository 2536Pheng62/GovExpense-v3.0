"""
PDF Preview Component สำหรับ Streamlit
ใช้ PDF.js (pdfjs-dist) จาก jsDelivr CDN เพื่อแสดงตัวอย่าง PDF ในเบราว์เซอร์
"""

import base64
import streamlit.components.v1 as components

# PDF.js CDN (jsDelivr) — version 4.10.38 (legacy-compatible, works in iframe)
PDFJS_CDN_VERSION = "4.10.38"
PDFJS_CDN_BASE = f"https://cdn.jsdelivr.net/npm/pdfjs-dist@{PDFJS_CDN_VERSION}"


def render_pdf_preview(pdf_bytes: bytes, height: int = 800, page_scale: float = 1.4):
    """
    แสดงตัวอย่าง PDF ใน Streamlit ผ่าน PDF.js (jsDelivr CDN)

    Args:
        pdf_bytes: ไบต์ของไฟล์ PDF
        height: ความสูงของ component (px)
        page_scale: ขนาดการแสดงผล (1.0 = 100%, 1.5 = 150%)
    """
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, sans-serif;
                background: #e8e8e8;
                overflow-x: hidden;
            }}

            /* Toolbar */
            .toolbar {{
                position: sticky;
                top: 0;
                z-index: 100;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 6px 16px;
                background: #2d2d2d;
                color: #fff;
                font-size: 12px;
            }}
            .toolbar button {{
                background: #555;
                color: #fff;
                border: none;
                border-radius: 3px;
                padding: 4px 10px;
                cursor: pointer;
                font-size: 12px;
                transition: background 0.15s;
            }}
            .toolbar button:hover {{
                background: #777;
            }}
            .toolbar button:disabled {{
                opacity: 0.3;
                cursor: not-allowed;
            }}
            .toolbar .page-info {{
                min-width: 90px;
                text-align: center;
                font-weight: 600;
            }}
            .toolbar .sep {{
                color: #666;
                margin: 0 4px;
            }}

            /* Loading */
            #loading {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 200px;
                color: #555;
            }}
            .spinner {{
                width: 28px; height: 28px;
                border: 3px solid #ccc;
                border-top-color: #333;
                border-radius: 50%;
                animation: spin 0.7s linear infinite;
                margin-bottom: 10px;
            }}
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

            /* Error */
            #error-msg {{
                display: none;
                text-align: center;
                padding: 24px;
                color: #333;
                font-size: 13px;
            }}

            /* Canvas Container — A4 paper look */
            #pdf-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 12px;
                padding: 12px;
            }}
            .page-wrapper {{
                background: white;
                box-shadow: 0 1px 4px rgba(0,0,0,0.2);
            }}
            .page-wrapper canvas {{
                display: block;
            }}
        </style>
    </head>
    <body>

    <!-- Toolbar -->
    <div class="toolbar" id="toolbar" style="display:none;">
        <button id="btn-prev" title="หน้าก่อนหน้า">◀</button>
        <span class="page-info" id="page-info">-</span>
        <button id="btn-next" title="หน้าถัดไป">▶</button>
        <span class="sep">|</span>
        <button id="btn-zoom-out" title="ซูมออก">−</button>
        <span id="zoom-level">100%</span>
        <button id="btn-zoom-in" title="ซูมเข้า">+</button>
        <button id="btn-zoom-fit" title="พอดีหน้า">Fit</button>
    </div>

    <!-- Loading -->
    <div id="loading">
        <div class="spinner"></div>
        <span>กำลังโหลดเอกสาร PDF...</span>
    </div>

    <!-- Error -->
    <div id="error-msg"></div>

    <!-- PDF Pages -->
    <div id="pdf-container"></div>

    <!-- PDF.js from jsDelivr CDN -->
    <script src="{PDFJS_CDN_BASE}/build/pdf.min.mjs" type="module"></script>
    <script type="module">
        import * as pdfjsLib from '{PDFJS_CDN_BASE}/build/pdf.min.mjs';

        // Set worker
        pdfjsLib.GlobalWorkerOptions.workerSrc = '{PDFJS_CDN_BASE}/build/pdf.worker.min.mjs';

        // === State ===
        let pdfDoc = null;
        let currentPage = 1;
        let totalPages = 0;
        let currentScale = {page_scale};
        const SCALE_STEP = 0.2;
        const SCALE_MIN = 0.5;
        const SCALE_MAX = 3.0;

        // === DOM ===
        const container = document.getElementById('pdf-container');
        const loading = document.getElementById('loading');
        const errorMsg = document.getElementById('error-msg');
        const toolbar = document.getElementById('toolbar');
        const pageInfo = document.getElementById('page-info');
        const zoomLevel = document.getElementById('zoom-level');
        const btnPrev = document.getElementById('btn-prev');
        const btnNext = document.getElementById('btn-next');
        const btnZoomIn = document.getElementById('btn-zoom-in');
        const btnZoomOut = document.getElementById('btn-zoom-out');
        const btnZoomFit = document.getElementById('btn-zoom-fit');

        // === Helpers ===
        function showError(msg) {{
            loading.style.display = 'none';
            errorMsg.style.display = 'block';
            errorMsg.textContent = '❌ ' + msg;
        }}

        function updateToolbar() {{
            pageInfo.textContent = `หน้า ${{currentPage}} / ${{totalPages}}`;
            zoomLevel.textContent = Math.round(currentScale * 100) + '%';
            btnPrev.disabled = (currentPage <= 1);
            btnNext.disabled = (currentPage >= totalPages);
        }}

        // === Render single page (NO annotation layer — prevents red rectangles) ===
        async function renderPage(pageNum, scale) {{
            const page = await pdfDoc.getPage(pageNum);
            const viewport = page.getViewport({{ scale }});

            // Create wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'page-wrapper';
            wrapper.id = 'page-' + pageNum;

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = viewport.width;
            canvas.height = viewport.height;

            wrapper.appendChild(canvas);
            container.appendChild(wrapper);

            // Render WITHOUT annotations (annotationMode: 0 = DISABLE)
            await page.render({{
                canvasContext: ctx,
                viewport,
                annotationMode: 0
            }}).promise;
        }}

        // === Render all pages ===
        async function renderAllPages(scale) {{
            container.innerHTML = '';
            for (let i = 1; i <= totalPages; i++) {{
                await renderPage(i, scale);
            }}
            updateToolbar();
        }}

        // === Scroll to page ===
        function scrollToPage(num) {{
            const el = document.getElementById('page-' + num);
            if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}

        // === Load PDF ===
        async function loadPDF() {{
            try {{
                const raw = atob('{b64_pdf}');
                const uint8 = new Uint8Array(raw.length);
                for (let i = 0; i < raw.length; i++) uint8[i] = raw.charCodeAt(i);

                pdfDoc = await pdfjsLib.getDocument({{ data: uint8 }}).promise;
                totalPages = pdfDoc.numPages;
                currentPage = 1;

                loading.style.display = 'none';
                toolbar.style.display = 'flex';

                await renderAllPages(currentScale);
            }} catch (err) {{
                showError('ไม่สามารถโหลด PDF ได้: ' + err.message);
                console.error(err);
            }}
        }}

        // === Controls ===
        btnPrev.addEventListener('click', () => {{
            if (currentPage > 1) {{
                currentPage--;
                updateToolbar();
                scrollToPage(currentPage);
            }}
        }});

        btnNext.addEventListener('click', () => {{
            if (currentPage < totalPages) {{
                currentPage++;
                updateToolbar();
                scrollToPage(currentPage);
            }}
        }});

        btnZoomIn.addEventListener('click', async () => {{
            if (currentScale < SCALE_MAX) {{
                currentScale = Math.min(currentScale + SCALE_STEP, SCALE_MAX);
                await renderAllPages(currentScale);
                scrollToPage(currentPage);
            }}
        }});

        btnZoomOut.addEventListener('click', async () => {{
            if (currentScale > SCALE_MIN) {{
                currentScale = Math.max(currentScale - SCALE_STEP, SCALE_MIN);
                await renderAllPages(currentScale);
                scrollToPage(currentPage);
            }}
        }});

        btnZoomFit.addEventListener('click', async () => {{
            currentScale = {page_scale};
            await renderAllPages(currentScale);
            scrollToPage(1);
            currentPage = 1;
        }});

        // === Intersection Observer for page tracking ===
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const pageNum = parseInt(entry.target.id.replace('page-', ''));
                    if (!isNaN(pageNum)) {{
                        currentPage = pageNum;
                        updateToolbar();
                    }}
                }}
            }});
        }}, {{ threshold: 0.5 }});

        // Re-observe after render
        const origRender = renderAllPages;
        renderAllPages = async function(scale) {{
            await origRender(scale);
            document.querySelectorAll('.page-wrapper').forEach(el => observer.observe(el));
        }};

        // === Init ===
        loadPDF();
    </script>
    </body>
    </html>
    """

    components.html(html_content, height=height, scrolling=True)
