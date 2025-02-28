import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import requests  # API 호출을 위한 라이브러리 추가

# 데이터 저장 파일 경로
CUSTOMERS_FILE = 'customers.json'
TRANSACTIONS_FILE = 'transactions.json'
ITEMS_FILE = 'items.json'
API_CONFIG_FILE = 'api_config.json'  # API 설정 파일 추가

# API 엔드포인트 설정
def get_zone_info(code):
    """Zone 정보를 가져오는 함수"""
    api_url = "https://sboapi.ecount.com/OAPI/V2/Zone"
    request_data = {"COM_CODE": code}
    
    try:
        response = requests.post(
            api_url,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()["Data"]["ZONE"]
        else:
            return None
    except Exception as e:
        st.error(f"Zone 정보 조회 중 오류 발생: {str(e)}")
        return None

def get_session_id(code, user_id, api_key, zone, is_test=False):
    """세션 ID를 가져오는 함수"""
    # TestKey는 sboapi로, APIKey는 oapi로 연결
    base_url = f"https://{'sboapi' if is_test else 'oapi'}{zone}.ecount.com/OAPI/V2/OAPILogin"
    
    request_data = {
        "COM_CODE": code,
        "USER_ID": user_id,
        "API_CERT_KEY": api_key,
        "LAN_TYPE": "ko-KR",
        "ZONE": zone
    }
    
    try:
        response = requests.post(
            base_url,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        response_data = response.json()
        
        # 오류 메시지 처리
        if response_data.get("Error") and response_data["Error"].get("Message"):
            st.error(f"API 오류: {response_data['Error']['Message']}")
            return None
            
        if response_data.get("Errors"):
            error_msg = response_data["Errors"][0].get("Message", "알 수 없는 오류가 발생했습니다.")
            st.error(f"API 오류: {error_msg}")
            return None
            
        # 데이터 확인
        if response_data.get("Data"):
            if response_data["Data"].get("Datas") and response_data["Data"]["Datas"].get("SESSION_ID"):
                return response_data["Data"]["Datas"]["SESSION_ID"]
            elif response_data["Data"].get("Message"):
                st.error(f"API 오류: {response_data['Data']['Message']}")
                return None
                
        st.error("세션 ID를 찾을 수 없습니다.")
        return None
            
    except Exception as e:
        st.error(f"세션 ID 조회 중 오류 발생: {str(e)}")
        return None

def get_products_list(session_id, zone, is_test=True):
    """품목 목록을 가져오는 함수"""
    # 마지막 API 호출 시간 확인
    last_call_time = getattr(st.session_state, 'last_api_call_time', None)
    if last_call_time and datetime.now() - last_call_time < timedelta(minutes=10):
        remaining_time = timedelta(minutes=10) - (datetime.now() - last_call_time)
        st.error(f"API 호출 제한: {remaining_time.seconds // 60}분 {remaining_time.seconds % 60}초 후에 다시 시도해주세요.")
        return None

    # TestKey로 받은 세션ID는 sboapi로, APIKey로 받은 세션ID는 oapi로 연결
    api_url = f"https://{'sboapi' if is_test else 'oapi'}{zone}.ecount.com/OAPI/V2/InventoryBasic/GetBasicProductsList"
    st.info(f"연결 URL: {api_url}")  # URL 확인을 위한 로그
    
    params = {
        "SESSION_ID": session_id
    }
    
    request_data = {
        "PROD_CD": ""
    }
    
    try:
        response = requests.post(
            api_url,
            params=params,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("Data") and response_data["Data"].get("Result"):
                # API 호출 시간 업데이트
                st.session_state.last_api_call_time = datetime.now()
                return response_data["Data"]["Result"]
            else:
                st.error(f"API 응답 오류: {response_data.get('Error', {}).get('Message', '알 수 없는 오류가 발생했습니다.')}")
                st.error(f"전체 응답: {response_data}")  # 전체 응답 확인을 위한 로그
        else:
            st.error(f"API 요청 실패: {response.status_code}")
            st.error(f"응답 내용: {response.text}")  # 응답 내용 확인을 위한 로그
        return None
    except Exception as e:
        st.error(f"품목 목록 조회 중 오류 발생: {str(e)}")
        return None

# 초기 데이터 로드 또는 생성
def load_or_create_data():
    if not os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False)
    
    if not os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)
            
    if not os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False)
            
    if not os.path.exists(API_CONFIG_FILE):  # API 설정 파일 생성
        with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "CODE": "",
                "ID": "",
                "TestKey": "",
                "APIKey": ""
            }, f, ensure_ascii=False)
    
    with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
        customers = json.load(f)
    
    with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
        transactions = json.load(f)
        
    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)
        
    with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:  # API 설정 로드
        api_config = json.load(f)
    
    # 고객 데이터 구조 확인 및 수정
    for customer_id, info in customers.items():
        if isinstance(info, int):
            customers[customer_id] = {
                "name": "Unknown",
                "points": info
            }
    
    return customers, transactions, items, api_config  # API 설정 추가

# 데이터 저장
def save_data(customers, transactions, items, api_config=None):  # API 설정 저장 추가
    with open(CUSTOMERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(customers, f, ensure_ascii=False, indent=2)
    
    with open(TRANSACTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)
        
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        
    if api_config is not None:  # API 설정 저장
        with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(api_config, f, ensure_ascii=False, indent=2)

# 고객 정보 검색
def find_customer(id_number):
    customer = st.session_state.customers.get(id_number, {})
    if isinstance(customer, int):  # 이전 형식의 데이터인 경우
        customer = {
            "name": "Unknown",
            "points": customer
        }
        st.session_state.customers[id_number] = customer
    return customer

# 품목 정보 검색
def find_item(search_term):
    """품목코드나 품목명으로 품목을 검색하는 함수"""
    matches = []
    
    # 품목코드로 직접 검색
    if search_term in st.session_state.item_data:
        matches.append((search_term, st.session_state.item_data[search_term]))
    
    # 품목명으로 검색
    for code, info in st.session_state.item_data.items():
        if search_term.lower() in info['name'].lower() and (code, info) not in matches:
            matches.append((code, info))
    
    return matches

# 거래처명으로 사업자번호 찾기 함수 추가
def find_customer_by_name(name):
    """거래처명으로 사업자번호 목록을 찾는 함수"""
    matches = []
    for id_number, info in st.session_state.customers.items():
        if info.get('name', '').lower() == name.lower():
            matches.append((id_number, info))
    return matches

# 세션 상태 초기화
if 'customers' not in st.session_state:
    customers, transactions, items, api_config = load_or_create_data()
    st.session_state.customers = customers
    st.session_state.transactions = transactions
    st.session_state.item_data = items
    st.session_state.api_config = api_config

# 페이지 설정
st.set_page_config(
    page_title="코다이포인트 v1.0",
    page_icon="💰",
    layout="wide"
)
st.title("코다이포인트 (CodaiPoint) v1.0")

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["거래 등록", "거래처 관리", "거래 내역 조회", "품목 관리"])

with tab1:
    # 상단부 - 날짜, 거래처, 포인트 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_date = st.date_input("거래일자", datetime.now())
        
    with col2:
        customer_name = st.text_input("거래처(고객명)", key="customer_name_input")
        if customer_name:
            matches = find_customer_by_name(customer_name)
            if matches:
                if len(matches) == 1:
                    # 일치하는 거래처가 하나인 경우
                    id_number = matches[0][0]
                    st.session_state.selected_customer_id = id_number
                elif len(matches) > 1:
                    # 중복된 거래처가 있는 경우
                    options = [f"{m[0]} - {m[1]['name']}" for m in matches]
                    selected_option = st.selectbox(
                        "중복된 거래처가 있습니다. 선택해주세요:",
                        options=options,
                        key="duplicate_customer_select"
                    )
                    if selected_option:
                        id_number = selected_option.split(" - ")[0]
                        st.session_state.selected_customer_id = id_number
        
    with col3:
        # 자동으로 선택된 사업자번호 표시
        default_id = st.session_state.get('selected_customer_id', '')
        id_number = st.text_input("사업자번호 또는 핸드폰번호", 
                                value=default_id,
                                key="id_number_input")
        
    # 거래처 정보 표시
    if customer_name and id_number:
        customer_info = find_customer(id_number)
        if customer_info:
            if customer_info.get('name') != customer_name:
                st.warning("⚠️ 등록된 사업자/핸드폰번호의 거래처명이 다릅니다!")
                if st.button("거래처 정보 업데이트"):
                    st.session_state.customers[id_number]['name'] = customer_name
                    save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                    st.success("거래처 정보가 업데이트되었습니다.")
                    st.rerun()
            current_points = customer_info.get('points', 0)
            st.info(f"현재 적립 포인트: {current_points:,} 점")
        else:
            st.info("새로운 거래처입니다. 거래 등록 시 자동으로 등록됩니다.")
            current_points = 0

    # 중간부 - 포인트 사용
    if customer_name and id_number and current_points > 0:
        st.markdown("---")
        points_to_use = st.number_input("사용할 포인트", min_value=0, max_value=current_points)
        if st.button("포인트 사용"):
            if points_to_use > 0:
                st.session_state.customers[id_number]['points'] -= points_to_use
                save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                st.success(f"{points_to_use:,} 포인트가 사용되었습니다.")
                st.rerun()

    # 하단부 - 거래 정보 입력
    st.markdown("---")
    st.subheader("거래 정보")
    
    # 품목 입력 관리를 위한 세션 상태 초기화
    if 'item_rows' not in st.session_state:
        st.session_state.item_rows = [{"id": 0}]
    if 'next_row_id' not in st.session_state:
        st.session_state.next_row_id = 1
    
    # 전체 합계를 저장할 변수들
    total_supply_value = 0
    total_vat = 0
    total_amount = 0
    
    # 각 품목 행 표시
    for i, row in enumerate(st.session_state.item_rows):
        st.markdown(f"##### 품목 {i+1}")
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3,2,2,2,2,2,1])  # 컬럼 비율 조정
        
        with col1:
            item_search = st.text_input(
                "품목코드 또는 품목명",
                key=f"item_code_input_{row['id']}",
                help="품목코드나 품목명을 입력하세요"
            )
            if item_search:
                matches = find_item(item_search)
                if matches:
                    if len(matches) == 1:
                        item_code, item_info = matches[0]
                        st.success(f"품목코드: {item_code}\n품목명: {item_info['name']}")
                        st.session_state[f"selected_item_code_{row['id']}"] = item_code
                    else:
                        options = [f"{code} - {info['name']}" for code, info in matches]
                        selected_option = st.selectbox(
                            "일치하는 품목이 여러 개 있습니다. 선택해주세요:",
                            options=options,
                            key=f"item_select_{row['id']}"
                        )
                        if selected_option:
                            item_code = selected_option.split(" - ")[0]
                            st.session_state[f"selected_item_code_{row['id']}"] = item_code
                else:
                    st.error("등록되지 않은 품목입니다.")
                    if f"selected_item_code_{row['id']}" in st.session_state:
                        del st.session_state[f"selected_item_code_{row['id']}"]
        
        with col2:
            quantity = st.number_input("수량", min_value=0, key=f"quantity_input_{row['id']}")
        with col3:
            price = st.number_input("단가", min_value=0, key=f"price_input_{row['id']}")
        with col4:
            supply_value = quantity * price
            st.write("공급가액")
            st.write(f"{supply_value:,}")
            total_supply_value += supply_value
        with col5:
            vat = supply_value * 0.1
            st.write("부가세")
            st.write(f"{vat:,}")
            total_vat += vat
        with col6:
            total = supply_value + vat
            st.write("합계")
            st.write(f"{total:,}")
            total_amount += total
        with col7:
            # 삭제 버튼 (첫 번째 행은 삭제 불가)
            if i > 0 and st.button("삭제", key=f"delete_item_{row['id']}"):
                st.session_state.item_rows = [r for r in st.session_state.item_rows if r['id'] != row['id']]
                st.rerun()
        
        st.markdown("---")
    
    # 새로운 품목 행 추가 버튼
    if st.button("품목 추가"):
        st.session_state.item_rows.append({"id": st.session_state.next_row_id})
        st.session_state.next_row_id += 1
        st.rerun()
    
    # 전체 합계 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 공급가액", f"{total_supply_value:,}")
    with col2:
        st.metric("총 부가세", f"{total_vat:,}")
    with col3:
        st.metric("총 합계", f"{total_amount:,}")

    # 거래 등록 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("거래 등록", key="register_transaction"):
            if not customer_name or not id_number:
                st.error("거래처(고객명)와 사업자/핸드폰번호를 입력해주세요.")
            else:
                # 각 품목 행의 유효성 검사
                valid_items = []
                for row in st.session_state.item_rows:
                    item_code = st.session_state.get(f"selected_item_code_{row['id']}")
                    quantity = st.session_state.get(f"quantity_input_{row['id']}", 0)
                    price = st.session_state.get(f"price_input_{row['id']}", 0)
                    
                    if item_code and quantity > 0 and price > 0:
                        valid_items.append({
                            "item_code": item_code,
                            "item_name": st.session_state.item_data[item_code]['name'],
                            "quantity": quantity,
                            "price": price,
                            "supply_value": quantity * price,
                            "vat": quantity * price * 0.1,
                            "total": quantity * price * 1.1
                        })
                
                if not valid_items:
                    st.error("최소한 하나의 유효한 품목을 입력해주세요.")
                    st.stop()
                
                # 포인트 적립 (총액의 1%)
                points = int(total_amount * 0.01)
                
                # 거래 정보 저장
                transaction = {
                    "date": selected_date.strftime("%Y-%m-%d"),
                    "customer_name": customer_name,
                    "customer_id": id_number,
                    "items": valid_items,
                    "total_supply_value": total_supply_value,
                    "total_vat": total_vat,
                    "total_amount": total_amount,
                    "points": points
                }
                st.session_state.transactions.append(transaction)
                
                # 고객 정보 저장/업데이트
                if id_number not in st.session_state.customers:
                    st.session_state.customers[id_number] = {
                        "name": customer_name,
                        "points": 0
                    }
                st.session_state.customers[id_number]['points'] += points
                
                # 데이터 저장
                save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                
                # 품목 입력 초기화
                st.session_state.item_rows = [{"id": 0}]
                st.session_state.next_row_id = 1
                
                st.success(f"거래가 등록되었습니다. {points:,} 포인트가 적립되었습니다.")
                st.rerun()
    
    with col2:
        # 이카운트 전송 버튼
        is_api_connected = getattr(st.session_state, 'api_session_id', None) is not None or getattr(st.session_state, 'test_session_id', None) is not None
        if st.button("이카운트 전송 및 거래등록", disabled=not is_api_connected):
            if not customer_name or not id_number:
                st.error("거래처(고객명)와 사업자/핸드폰번호를 입력해주세요.")
            else:
                # 각 품목 행의 유효성 검사
                valid_items = []
                for row in st.session_state.item_rows:
                    item_code = st.session_state.get(f"selected_item_code_{row['id']}")
                    quantity = st.session_state.get(f"quantity_input_{row['id']}", 0)
                    price = st.session_state.get(f"price_input_{row['id']}", 0)
                    
                    if item_code and quantity > 0 and price > 0:
                        valid_items.append({
                            "PROD_CD": item_code,
                            "PROD_DES": st.session_state.item_data[item_code]['name'],
                            "QTY": str(quantity),  # 수량을 문자열로 변환
                            "PRICE": str(price),  # 단가를 문자열로 변환
                            "SUPPLY_AMT": str(quantity * price),  # 공급가액을 문자열로 변환
                            "VAT_AMT": str(int(quantity * price * 0.1)),  # 부가세를 정수로 변환 후 문자열로 변환
                            "U_MEMO1": str(customer_info.get('points', 0))  # 현재 적립 포인트
                        })
                
                if not valid_items:
                    st.error("최소한 하나의 유효한 품목을 입력해주세요.")
                    st.stop()
                
                # 이카운트 API 요청 데이터 구성
                request_data = {
                    "SaleList": []
                }
                
                # 각 품목을 별도의 BulkDatas로 추가
                for item in valid_items:
                    request_data["SaleList"].append({
                        "BulkDatas": {
                            "UPLOAD_SER_NO": "",  # 필수
                            "WH_CD": "100",     # 필수
                            "CUST": id_number,    # 거래처코드
                            "CUST_DES": customer_name,  # 거래처명
                            "PROD_CD": item["PROD_CD"],  # 필수
                            "QTY": item["QTY"],          # 필수
                            "PRICE": item["PRICE"],      # 단가
                            "SUPPLY_AMT": item["SUPPLY_AMT"],  # 공급가액
                            "VAT_AMT": item["VAT_AMT"],   # 부가세
                            "U_MEMO1": item["U_MEMO1"]  # 현재 적립 포인트
                        }
                    })
                
                # API 호출
                session_id = st.session_state.get('api_session_id') or st.session_state.get('test_session_id')
                zone = st.session_state.zone
                is_test = bool(st.session_state.get('test_session_id'))  # TestKey로 받은 세션ID인지 확인
                
                api_url = f"https://{'sboapi' if is_test else 'oapi'}{zone}.ecount.com/OAPI/V2/Sale/SaveSale"
                
                # 디버깅 정보 출력
                st.write("API 디버깅 정보:")
                st.write(f"- Zone: {zone}")
                st.write(f"- Session ID: {session_id}")
                st.write(f"- API URL: {api_url}")
                st.write("- Request Data:", request_data)
                
                try:
                    response = requests.post(
                        f"{api_url}?SESSION_ID={session_id}",
                        json=request_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    st.write("- Response Status:", response.status_code)
                    st.write("- Response Headers:", dict(response.headers))
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        st.write("- Response Data:", response_data)
                        
                        # 오류 응답 체크
                        if response_data is None:
                            st.error("이카운트 API로부터 응답을 받지 못했습니다.")
                            st.stop()
                            
                        if response_data.get("Error"):
                            st.error(f"이카운트 API 오류: {response_data['Error'].get('Message', '알 수 없는 오류가 발생했습니다.')}")
                            st.stop()
                            
                        if response_data.get("Errors"):
                            error_msg = response_data["Errors"][0].get("Message", "알 수 없는 오류가 발생했습니다.")
                            st.error(f"이카운트 API 오류: {error_msg}")
                            st.stop()
                        
                        # 상세 오류 메시지 체크
                        if response_data.get("Data"):
                            if response_data["Data"].get("FailCnt", 0) > 0 and response_data["Data"].get("ResultDetails"):
                                error_details = response_data["Data"]["ResultDetails"][0]
                                if not error_details.get("IsSuccess"):
                                    error_messages = []
                                    for error in error_details.get("Errors", []):
                                        error_messages.append(error.get("Message", ""))
                                    
                                    st.error("이카운트 전송 실패:")
                                    for msg in error_messages:
                                        st.error(f"- {msg}")
                                    st.stop()
                        
                        # 성공 응답 체크
                        if response_data.get("Data") and response_data["Data"].get("SuccessCnt", 0) > 0:
                            # 포인트 적립 (총액의 1%)
                            points = int(total_amount * 0.01)
                            
                            # 거래 정보 저장
                            transaction = {
                                "date": selected_date.strftime("%Y-%m-%d"),
                                "customer_name": customer_name,
                                "customer_id": id_number,
                                "items": [{
                                    "item_code": item["PROD_CD"],
                                    "item_name": item["PROD_DES"],
                                    "quantity": item["QTY"],
                                    "price": item["PRICE"],
                                    "supply_value": item["SUPPLY_AMT"],
                                    "vat": item["VAT_AMT"],
                                    "total": item["SUPPLY_AMT"] + item["VAT_AMT"]
                                } for item in valid_items],
                                "total_supply_value": total_supply_value,
                                "total_vat": total_vat,
                                "total_amount": total_amount,
                                "points": points
                            }
                            st.session_state.transactions.append(transaction)
                            
                            # 고객 정보 저장/업데이트
                            if id_number not in st.session_state.customers:
                                st.session_state.customers[id_number] = {
                                    "name": customer_name,
                                    "points": 0
                                }
                            st.session_state.customers[id_number]['points'] += points
                            
                            # 데이터 저장
                            save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                            
                            # 품목 입력 초기화
                            st.session_state.item_rows = [{"id": 0}]
                            st.session_state.next_row_id = 1
                            
                            # 성공 메시지 표시
                            st.success("✅ 이카운트 전송이 완료되었습니다!")
                            st.success(f"💰 포인트 적립: {points:,}점")
                            st.balloons()  # 축하 효과 표시
                            st.rerun()
                        else:
                            st.error(f"이카운트 전송 실패: {response_data.get('Error', {}).get('Message', '알 수 없는 오류가 발생했습니다.')}")
                    else:
                        st.error(f"이카운트 전송 실패: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"이카운트 전송 중 오류 발생: {str(e)}")

with tab2:
    st.subheader("거래처 관리")
    
    # 거래처 등록/수정 폼
    with st.form("customer_registration"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_customer_id = st.text_input("사업자번호 또는 핸드폰번호", key="new_customer_id")
        with col2:
            new_customer_name = st.text_input("거래처(고객명)", key="new_customer_name")
        with col3:
            initial_points = st.number_input("초기 포인트", min_value=0, key="initial_points")
            
        submitted = st.form_submit_button("거래처 등록/수정")
        if submitted:
            if not new_customer_id or not new_customer_name:
                st.error("사업자번호/핸드폰번호와 거래처명을 모두 입력해주세요.")
            else:
                if new_customer_id in st.session_state.customers:
                    current_points = st.session_state.customers[new_customer_id].get('points', 0)
                    st.session_state.customers[new_customer_id] = {
                        "name": new_customer_name,
                        "points": current_points
                    }
                    st.success(f"거래처 정보가 수정되었습니다: [{new_customer_id}] {new_customer_name}")
                else:
                    st.session_state.customers[new_customer_id] = {
                        "name": new_customer_name,
                        "points": initial_points
                    }
                    st.success(f"새로운 거래처가 등록되었습니다: [{new_customer_id}] {new_customer_name}")
                save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                st.rerun()
    
    # 등록된 거래처 목록
    st.markdown("---")
    st.subheader("등록된 거래처 목록")
    if st.session_state.customers:
        customers_df = pd.DataFrame([
            {
                "사업자번호/핸드폰번호": id_number,
                "거래처명": info.get("name", "Unknown"),
                "적립 포인트": info.get("points", 0)
            }
            for id_number, info in st.session_state.customers.items()
        ])
        st.dataframe(customers_df.reset_index(drop=True), use_container_width=True, hide_index=True)
        
        # 거래처 수정/삭제
        col1, col2 = st.columns(2)
        with col1:
            customer_to_edit = st.selectbox(
                "수정/삭제할 거래처 선택",
                options=list(st.session_state.customers.keys()),
                format_func=lambda x: f"{x} - {st.session_state.customers[x]['name']}"
            )
        with col2:
            action = st.radio("작업 선택", ["수정", "삭제"], horizontal=True)
            
        if action == "수정":
            with st.form("customer_edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_name = st.text_input("거래처명", value=st.session_state.customers[customer_to_edit]['name'])
                with col2:
                    edit_points = st.number_input("적립 포인트", value=st.session_state.customers[customer_to_edit]['points'])
                
                if st.form_submit_button("수정"):
                    st.session_state.customers[customer_to_edit]['name'] = edit_name
                    st.session_state.customers[customer_to_edit]['points'] = edit_points
                    save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                    st.success("거래처 정보가 수정되었습니다.")
                    st.rerun()
        else:  # 삭제
            if st.button("선택한 거래처 삭제"):
                if st.session_state.customers[customer_to_edit]['points'] > 0:
                    st.error("적립 포인트가 남아있는 거래처는 삭제할 수 없습니다.")
                else:
                    del st.session_state.customers[customer_to_edit]
                    save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                    st.success("거래처가 삭제되었습니다.")
                    st.rerun()

with tab3:
    st.subheader("거래 내역 조회")
    
    if st.session_state.transactions:
        # 거래처명이 비어있는 데이터 삭제
        st.session_state.transactions = [
            transaction for transaction in st.session_state.transactions 
            if transaction.get('customer_name') and transaction.get('customer_name').strip()
        ]
        save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
        
        # 거래 내역을 DataFrame으로 변환하기 전에 데이터 구조 수정
        transaction_rows = []
        for transaction in st.session_state.transactions:
            # 기본 거래 정보를 안전하게 가져오기
            base_info = {
                'date': transaction.get('date', ''),
                'customer_name': transaction.get('customer_name', ''),
                'customer_id': transaction.get('customer_id', ''),
                'total_supply_value': transaction.get('total_supply_value', 0),
                'total_vat': transaction.get('total_vat', 0),
                'total_amount': transaction.get('total_amount', 0),
                'points': transaction.get('points', 0)
            }
            
            # 품목별 정보를 개별 행으로 추가
            if transaction.get('items'):
                for item in transaction['items']:
                    row = base_info.copy()
                    row.update({
                        'item_code': item.get('item_code', ''),
                        'item_name': item.get('item_name', ''),
                        'quantity': item.get('quantity', 0),
                        'price': item.get('price', 0),
                        'supply_value': item.get('supply_value', 0),
                        'vat': item.get('vat', 0),
                        'total': item.get('total', 0)
                    })
                    transaction_rows.append(row)
            else:
                transaction_rows.append(base_info)
        
        transactions_df = pd.DataFrame(transaction_rows)
        
        if not transactions_df.empty:
            transactions_df['date'] = pd.to_datetime(transactions_df['date'])
            transactions_df = transactions_df.sort_values('date', ascending=False)
            
            # 거래처 검색 입력
            customer_name_search = st.text_input("거래처(고객명)", key="customer_search_input")
            if customer_name_search:
                matches = find_customer_by_name(customer_name_search)
                if matches:
                    if len(matches) == 1:
                        # 일치하는 거래처가 하나인 경우
                        id_number = matches[0][0]
                        transactions_df = transactions_df[transactions_df['customer_id'] == id_number]
                    elif len(matches) > 1:
                        # 중복된 거래처가 있는 경우
                        options = [f"{m[0]} - {m[1]['name']}" for m in matches]
                        selected_option = st.selectbox(
                            "중복된 거래처가 있습니다. 선택해주세요:",
                            options=options,
                            key="duplicate_customer_search"
                        )
                        if selected_option:
                            id_number = selected_option.split(" - ")[0]
                            transactions_df = transactions_df[transactions_df['customer_id'] == id_number]
                else:
                    st.warning("검색된 거래처가 없습니다.")
            
            if not transactions_df.empty:
                # 날짜 범위 선택
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("시작일", min(transactions_df['date']).date(), key="start_date")
                with col2:
                    end_date = st.date_input("종료일", max(transactions_df['date']).date(), key="end_date")
                
                mask = (transactions_df['date'].dt.date >= start_date) & (transactions_df['date'].dt.date <= end_date)
                filtered_df = transactions_df[mask]
                
                if not filtered_df.empty:
                    # 표시할 열 선택
                    display_columns = [
                        'date', 'customer_name', 'item_name', 'quantity', 'price', 
                        'supply_value', 'vat', 'total', 'points'
                    ]
                    # 실제 존재하는 열만 선택
                    display_columns = [col for col in display_columns if col in filtered_df.columns]
                    
                    st.dataframe(filtered_df[display_columns].reset_index(drop=True), use_container_width=True, hide_index=True)
                    
                    # 거래 내역 삭제 기능 추가
                    if not filtered_df.empty:
                        st.markdown("---")
                        st.subheader("거래 내역 삭제")
                        
                        # 거래 내역 선택을 위한 정보 표시
                        unique_transactions = filtered_df.groupby(['date', 'customer_name']).first().reset_index()
                        
                        selected_transaction_idx = st.selectbox(
                            "삭제할 거래 내역 선택",
                            range(len(unique_transactions)),
                            format_func=lambda x: f"{unique_transactions.iloc[x]['date'].strftime('%Y-%m-%d')} - {unique_transactions.iloc[x]['customer_name']}"
                        )
                        
                        if st.button("선택한 거래 내역 삭제"):
                            selected_transaction = unique_transactions.iloc[selected_transaction_idx]
                            selected_date = selected_transaction['date'].strftime('%Y-%m-%d')
                            selected_customer = selected_transaction['customer_name']
                            
                            # 전체 거래 내역에서 해당 거래 찾기
                            for idx, transaction in enumerate(st.session_state.transactions):
                                if (transaction.get('date') == selected_date and 
                                    transaction.get('customer_name') == selected_customer):
                                    # 포인트 차감
                                    customer_id = transaction.get('customer_id')
                                    points_to_remove = transaction.get('points', 0)
                                    
                                    if customer_id:
                                        # 고객 포인트 차감
                                        st.session_state.customers[customer_id]['points'] -= points_to_remove
                                    
                                    # 거래 내역 삭제
                                    st.session_state.transactions.pop(idx)
                                    
                                    # 데이터 저장
                                    save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                                    st.success("거래 내역이 삭제되었습니다.")
                                    st.rerun()
                                    break
                else:
                    st.info("해당 기간에 거래 내역이 없습니다.")
            else:
                st.info("선택한 거래처의 거래 내역이 없습니다.")
        else:
            st.info("거래 내역이 없습니다.")

with tab4:
    st.subheader("품목 관리")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        # API 설정 버튼
        if st.button("API 설정", key="api_settings_button"):
            st.session_state.show_api_settings = True
    with col2:
        # 품목 불러오기 버튼 (API 연동이 완료된 경우에만 활성화)
        is_api_connected = getattr(st.session_state, 'api_session_id', None) is not None or getattr(st.session_state, 'test_session_id', None) is not None
        if st.button("품목 불러오기", disabled=not is_api_connected):
            if st.session_state.zone:
                # 로딩 스피너 표시
                with st.spinner("품목 정보를 불러오는 중입니다..."):
                    # 진행 상태 표시
                    progress_bar = st.progress(0)
                    st.info("API 서버에 연결 중...")
                    progress_bar.progress(30)
                    
                    # TestKey가 있는 경우 테스트 모드로 시도
                    if getattr(st.session_state, 'test_session_id', None):
                        st.info("테스트 세션으로 연결 시도...")
                        products = get_products_list(st.session_state.test_session_id, st.session_state.zone, is_test=True)
                    elif getattr(st.session_state, 'api_session_id', None):
                        st.info("API 세션으로 연결 시도...")
                        products = get_products_list(st.session_state.api_session_id, st.session_state.zone, is_test=False)
                    
                    if products:
                        st.info("품목 데이터 처리 중...")
                        progress_bar.progress(60)
                        
                        # 기존 품목 데이터 초기화
                        st.session_state.item_data = {}
                        
                        # 새로운 품목 데이터 등록
                        total_products = len(products)
                        for i, product in enumerate(products):
                            prod_cd = product.get("PROD_CD")
                            prod_des = product.get("PROD_DES")
                            if prod_cd and prod_des:
                                st.session_state.item_data[prod_cd] = {
                                    "name": prod_des
                                }
                            # 진행률 업데이트 (60%~90%)
                            progress = 60 + (30 * (i + 1) / total_products)
                            progress_bar.progress(int(progress))
                        
                        st.info("데이터 저장 중...")
                        progress_bar.progress(90)
                        
                        # 데이터 저장
                        save_data(
                            st.session_state.customers,
                            st.session_state.transactions,
                            st.session_state.item_data,
                            st.session_state.api_config
                        )
                        
                        progress_bar.progress(100)
                        st.success(f"품목 정보가 성공적으로 업데이트되었습니다. (총 {len(st.session_state.item_data)}개 품목)")
                        st.rerun()
                    else:
                        st.error("품목 정보를 불러오는데 실패했습니다.")
            else:
                st.error("API 연동이 필요합니다. API 설정에서 연동을 완료해주세요.")
    
    # API 설정 레이어
    if getattr(st.session_state, 'show_api_settings', False):
        with st.form("api_settings_form"):
            st.subheader("API 설정")
            
            # 현재 설정값 로드
            current_api_config = getattr(st.session_state, 'api_config', {
                "CODE": "",
                "ID": "",
                "TestKey": "",
                "APIKey": ""
            })
            
            col1, col2 = st.columns(2)
            with col1:
                code = st.text_input("CODE", value=current_api_config.get("CODE", ""))
                test_key = st.text_input("TestKey", value=current_api_config.get("TestKey", ""))
            with col2:
                id_value = st.text_input("ID", value=current_api_config.get("ID", ""))
                api_key = st.text_input("APIKey", value=current_api_config.get("APIKey", ""), type="password")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("저장"):
                    st.session_state.api_config = {
                        "CODE": code,
                        "ID": id_value,
                        "TestKey": test_key,
                        "APIKey": api_key
                    }
                    save_data(
                        st.session_state.customers,
                        st.session_state.transactions,
                        st.session_state.item_data,
                        st.session_state.api_config
                    )
                    st.success("API 설정이 저장되었습니다.")
                    st.session_state.show_api_settings = False
                    st.rerun()
            with col2:
                # API 연결 상태에 따라 버튼 텍스트 변경
                button_text = "연동 완료" if getattr(st.session_state, 'api_session_id', None) else "API 연결 테스트"
                if st.form_submit_button(button_text):
                    # Zone 정보 조회
                    zone = get_zone_info(code)
                    if zone:
                        st.session_state.zone = zone
                        st.info(f"Zone 정보 조회 성공: {zone}")
                        
                        # 테스트키가 있는 경우 테스트 세션 연결 시도
                        if test_key:
                            st.info("테스트 세션 연결 시도 중...")
                            session_id = get_session_id(code, id_value, test_key, zone, is_test=True)
                            if session_id:
                                st.session_state.test_session_id = session_id
                                st.success(f"테스트 세션 연결 성공 (Session ID: {session_id})")
                            else:
                                st.error("테스트 세션 연결 실패")
                        
                        # API키가 있는 경우 실제 API 세션 연결 시도
                        if api_key:
                            st.info("API 세션 연결 시도 중...")
                            api_session_id = get_session_id(code, id_value, api_key, zone, is_test=False)
                            if api_session_id:
                                st.session_state.api_session_id = api_session_id
                                st.success(f"API 세션 연결 성공 (Session ID: {api_session_id})")
                            else:
                                st.error("API 세션 연결 실패")
                                if 'api_session_id' in st.session_state:
                                    del st.session_state.api_session_id
                    else:
                        st.error("Zone 정보 조회 실패")
                        if 'api_session_id' in st.session_state:
                            del st.session_state.api_session_id
            with col3:
                if st.form_submit_button("닫기"):
                    st.session_state.show_api_settings = False
                    st.rerun()
    
    st.markdown("---")
    
    # 품목 등록 폼
    with st.form("item_registration"):
        col1, col2 = st.columns(2)
        with col1:
            new_item_code = st.text_input("품목코드", key="new_item_code")
        with col2:
            new_item_name = st.text_input("품목명", key="new_item_name")
            
        submitted = st.form_submit_button("품목 등록/수정")
        if submitted:
            if not new_item_code or not new_item_name:
                st.error("품목코드와 품목명을 모두 입력해주세요.")
            else:
                st.session_state.item_data[new_item_code] = {
                    "name": new_item_name
                }
                save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data)
                st.success(f"품목이 등록/수정되었습니다: [{new_item_code}] {new_item_name}")
                st.rerun()
    
    # 등록된 품목 목록
    st.markdown("---")
    st.subheader("등록된 품목 목록")
    if st.session_state.item_data:
        items_df = pd.DataFrame([
            {"품목코드": code, "품목명": info["name"]}
            for code, info in st.session_state.item_data.items()
        ])
        st.dataframe(items_df.reset_index(drop=True), use_container_width=True, hide_index=True)
        
        # 품목 수정/삭제
        col1, col2 = st.columns(2)
        with col1:
            item_to_edit = st.selectbox(
                "수정/삭제할 품목 선택",
                options=list(st.session_state.item_data.keys()),
                format_func=lambda x: f"{x} - {st.session_state.item_data[x]['name']}"
            )
        with col2:
            item_action = st.radio("작업 선택", ["수정", "삭제"], horizontal=True, key="item_action")
            
        if item_action == "수정":
            with st.form("item_edit_form"):
                edit_item_name = st.text_input("품목명", value=st.session_state.item_data[item_to_edit]['name'])
                
                if st.form_submit_button("수정"):
                    st.session_state.item_data[item_to_edit]['name'] = edit_item_name
                    save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                    st.success("품목 정보가 수정되었습니다.")
                    st.rerun()
        else:  # 삭제
            if st.button("선택한 품목 삭제"):
                # 거래 내역에서 해당 품목 사용 여부 확인
                item_in_use = False
                for transaction in st.session_state.transactions:
                    for item in transaction.get('items', []):
                        if item['item_code'] == item_to_edit:
                            item_in_use = True
                            break
                    if item_in_use:
                        break
                
                if item_in_use:
                    st.error("이미 거래 내역에 사용된 품목은 삭제할 수 없습니다.")
                else:
                    del st.session_state.item_data[item_to_edit]
                    save_data(st.session_state.customers, st.session_state.transactions, st.session_state.item_data, st.session_state.api_config)
                    st.success("품목이 삭제되었습니다.")
                    st.rerun() 