#!/usr/bin/env python3
"""report.html -> report.pdf (Chromium 인쇄 엔진 사용)"""
import os
from playwright.sync_api import sync_playwright

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, '..', 'report.pdf')
footer = ("<div style=\"width:100%;font-size:8px;color:#7a8a83;text-align:center;"
          "font-family:'Noto Sans CJK KR',sans-serif;\"><span class=\"pageNumber\"></span> / "
          "<span class=\"totalPages\"></span></div>")

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto('file://' + os.path.join(here, 'report.html'))
    pg.wait_for_load_state('networkidle')
    pg.pdf(path=out, format='A4', print_background=True, prefer_css_page_size=True,
           display_header_footer=True, header_template='<div></div>', footer_template=footer,
           margin={'top': '17mm', 'bottom': '18mm', 'left': '19mm', 'right': '19mm'})
    b.close()
print('saved', os.path.abspath(out))
