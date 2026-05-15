import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
import time
import datetime
import requests
import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


# 크롬 드라이버 경로 설정
path = r"C:\Users\NT551_11TH\Downloads\chromedriver-win64\chromedriver.exe"


def parse_annual_fee(fee_str):
    """
    텍스트 형태의 연회비에서 숫자만 추출하는 함수
    우선순위: 1. 국내전용 -> 2. 해외겸용 -> 3. 일반 숫자 -> 4. 0
    """
    if not fee_str: # 데이터가 아예 없거나 None일 경우
        return 0
    
    # 1. '국내전용' 글자 뒤에 나오는 숫자(쉼표 포함)를 찾음
    domestic_match = re.search(r'국내전용[^0-9]*([0-9,]+)', fee_str)
    if domestic_match:
        return int(domestic_match.group(1).replace(',', '')) # 쉼표 제거 후 정수로 변환
    
    # 2. 국내전용이 없다면 '해외겸용' 글자 뒤에 나오는 숫자를 찾음
    overseas_match = re.search(r'해외겸용[^0-9]*([0-9,]+)', fee_str)
    if overseas_match:
        return int(overseas_match.group(1).replace(',', ''))
        
    # 3. (예외처리) '국내/해외' 구분 없이 "15,000원" 처럼 숫자만 덜렁 있는 경우
    any_num_match = re.search(r'([0-9,]+)[ ]*원', fee_str)
    if any_num_match:
        return int(any_num_match.group(1).replace(',', ''))
        
    # 4. 연회비가 없거나("연회비 없음") 위 조건에 다 안 맞으면 0 반환
    return 0