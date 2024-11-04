import os
import re
import time

import pandas as pd
from langchain_loader.document.convert.pdf_converter import PdfConverter
from pdfminer.high_level import extract_pages
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Spacer, PageBreak, Table, TableStyle, Paragraph

from services.kgpt_llm import root_path
from personaai_default import get_logger

log = get_logger()

class EnvConverter(PdfConverter):
    def __init__(self, path):
        super().__init__(path)

    def first_process(self):
        pass

    def pdf_to_df(self):
        pass

    def pdf_to_save_pdf(self, save_path):
        pass

    # ['국민신문고 민원 내용(', '민원처리 답변', '1. 민원 신청인 정보', '2. 민원 처리 결과']
    def dict_df(self, dict):
        pass

    def change_dot(self, text):
        pass


    def is_pdf(self, path):
        pass


    def pdf_df(self):
        pass



    # 입력받은 데이터프레임 리스트 전체를 컬럼 내용 형식으로 변환
    def df_all(self, dfs):
        pass

    # 입력받은 데이터프레임리스트 하나를 컬럼 내용 형식으로 변환
    def df_one(self, dfs):
        pass

    # 데이터 프레임을 주면 해당 데이터 프레임을 품질 향상 폼으로 변경
    def fin_pdf(self, df, file_path = 'save_pdf.pdf', font_name = 'Malgun', font_size = 7):        
        pass