import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
import time
import datetime
import requests
import tqdm


# 크롬 드라이버 경로 설정
# path = r"C:\Users\NT551_11TH\Downloads\chromedriver-win64\chromedriver.exe"


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


# 카드 단일 정보 수집 및 파싱 함수
def collect_cards_batch(card_id_list, desc="카드 데이터 수집"):
    """
    카드 ID 리스트를 입력받아 API를 호출하고 데이터를 일괄 수집합니다.
    반환값: (성공한 데이터 리스트, 실패한 카드ID 리스트)
    실패(404 등) 시: (False, 에러상태코드_또는_None)
    """
    card_data_list = []
    fail_list = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://www.card-gorilla.com/' 
    }
    for card_id in tqdm.tqdm(card_id_list, desc=desc):
        url = f"https://api.card-gorilla.com:8080/v1/cards/{card_id}"

        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                raw_data = response.json()
    
                # 연회비
                raw_fee_str = raw_data.get('annual_fee_basic', '')
                parsed_fee = parse_annual_fee(raw_fee_str)
    
                # 카테고리 추출
                category_list = []
                if 'key_benefit' in raw_data and raw_data['key_benefit']:
                    for benefit in raw_data['key_benefit']:
                        if 'cate' in benefit and 'name' in benefit['cate']:
                            cate_name = benefit['cate']['name']
                            if cate_name not in ['기타', '유의사항'] and cate_name not in category_list:
                                category_list.append(cate_name)
    
                # 주요혜택 추출
                top_tags_list = []
                if 'top_benefit' in raw_data and raw_data['top_benefit']:
                    for top in raw_data['top_benefit']:
                        if 'tags' in top and top['tags']:
                            top_tags_list.append(" ".join(top['tags']))
    
                # 발급가능여부
                is_discontinued = raw_data.get('is_discon', False)
                issuable_status = 'X' if is_discontinued else 'O'
    
                card_info = {
                    '카드번호': card_id,
                    '카드명': raw_data.get('name', '이름없음'),
                    '카드사': raw_data.get('corp', {}).get('name', '알수없음'),
                    '카드타입': raw_data.get('cate', '알수없음'),
                    '출시일': raw_data.get('release_dt', '알수없음'),
                    '연회비': parsed_fee,
                    '전월실적': raw_data.get('pre_month_money', 0),
                    '카테고리': ", ".join(category_list),
                    '주요혜택': ", ".join(top_tags_list),
                    '발급가능여부': issuable_status
                }
                card_data_list.append(card_info)
                
            elif response.status_code == 404:
                pass
            else:
                fail_list.append(card_id)
                
        except Exception as e:
            print(f"[오류] {card_id}번 카드 정보 요청 중 예외 발생: {e}")

        time.sleep(0.1)
        
    return card_data_list, fail_list