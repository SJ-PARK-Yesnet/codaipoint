import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# 데이터 저장 파일 경로
CUSTOMERS_FILE = 'customers.json'
TRANSACTIONS_FILE = 'transactions.json'
ITEMS_FILE = 'items.json'

# 초기 데이터 로드 또는 생성
def load_or_create_data():
    if not os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'w') as f:
            json.dump([], f)
            
    if not os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, 'w') as f:
            json.dump({}, f)
    
    with open(CUSTOMERS_FILE, 'r') as f:
        customers = json.load(f)
    
    with open(TRANSACTIONS_FILE, 'r') as f:
        transactions = json.load(f)
        
    with open(ITEMS_FILE, 'r') as f:
        items = json.load(f)
    
    return customers, transactions, items

# 데이터 저장
def save_data(customers, transactions, items):
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump(customers, f)
    
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(transactions, f)
        
    with open(ITEMS_FILE, 'w') as f:
        json.dump(items, f)

# 고객 정보 검색
def find_customer(id_number):
    return st.session_state.customers.get(id_number, {})

# 품목 정보 검색
def find_item(item_code):
    return st.session_state.items.get(item_code, {})

# 세션 상태 초기화
if 'customers' not in st.session_state:
    st.session_state.customers, st.session_state.transactions, st.session_state.items = load_or_create_data()

# 페이지 설정
st.set_page_config(page_title="거래 관리 시스템", layout="wide")
st.title("거래 관리 시스템")

# 탭 생성
tab1, tab2 = st.tabs(["거래 등록", "품목 관리"])

with tab1:
    # 상단부 - 날짜, 거래처, 포인트 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_date = st.date_input("거래일자", datetime.now())
        
    with col2:
        customer_name = st.text_input("거래처(고객명)")
        
    with col3:
        id_number = st.text_input("사업자번호 또는 핸드폰번호")
        
    # 거래처 정보 표시
    if customer_name and id_number:
        customer_info = find_customer(id_number)
        if customer_info:
            if customer_info.get('name') != customer_name:
                st.warning("⚠️ 등록된 사업자/핸드폰번호의 거래처명이 다릅니다!")
                if st.button("거래처 정보 업데이트"):
                    st.session_state.customers[id_number]['name'] = customer_name
                    save_data(st.session_state.customers, st.session_state.transactions, st.session_state.items)
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
                save_data(st.session_state.customers, st.session_state.transactions, st.session_state.items)
                st.success(f"{points_to_use:,} 포인트가 사용되었습니다.")
                st.rerun()

    # 하단부 - 거래 정보 입력
    st.markdown("---")
    st.subheader("거래 정보")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        item_code = st.text_input("품목코드")
        if item_code:
            item_info = find_item(item_code)
            if item_info:
                st.success(f"품목명: {item_info['name']}")
            else:
                st.error("등록되지 않은 품목코드입니다.")
    with col2:
        quantity = st.number_input("수량", min_value=0)
    with col3:
        price = st.number_input("단가", min_value=0)
    with col4:
        supply_value = quantity * price
        st.write("공급가액")
        st.write(f"{supply_value:,}")
    with col5:
        vat = supply_value * 0.1
        st.write("부가세")
        st.write(f"{vat:,}")
    with col6:
        total = supply_value + vat
        st.write("합계")
        st.write(f"{total:,}")

    # 거래 등록 버튼
    if st.button("거래 등록"):
        if not customer_name or not id_number:
            st.error("거래처(고객명)와 사업자/핸드폰번호를 입력해주세요.")
        elif not item_code or not find_item(item_code):
            st.error("올바른 품목코드를 입력해주세요.")
        elif quantity == 0 or price == 0:
            st.error("수량과 단가를 입력해주세요.")
        else:
            # 포인트 적립 (총액의 1%)
            points = int(total * 0.01)
            
            # 거래 정보 저장
            transaction = {
                "date": selected_date.strftime("%Y-%m-%d"),
                "customer_name": customer_name,
                "customer_id": id_number,
                "item_code": item_code,
                "item_name": st.session_state.items[item_code]['name'],
                "quantity": quantity,
                "price": price,
                "supply_value": supply_value,
                "vat": vat,
                "total": total,
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
            save_data(st.session_state.customers, st.session_state.transactions, st.session_state.items)
            
            st.success(f"거래가 등록되었습니다. {points:,} 포인트가 적립되었습니다.")
            st.rerun()

with tab2:
    st.subheader("품목 관리")
    
    # 품목 등록 폼
    with st.form("item_registration"):
        col1, col2 = st.columns(2)
        with col1:
            new_item_code = st.text_input("품목코드")
        with col2:
            new_item_name = st.text_input("품목명")
            
        submitted = st.form_submit_button("품목 등록/수정")
        if submitted:
            if not new_item_code or not new_item_name:
                st.error("품목코드와 품목명을 모두 입력해주세요.")
            else:
                st.session_state.items[new_item_code] = {
                    "name": new_item_name
                }
                save_data(st.session_state.customers, st.session_state.transactions, st.session_state.items)
                st.success(f"품목이 등록/수정되었습니다: [{new_item_code}] {new_item_name}")
                st.rerun()
    
    # 등록된 품목 목록
    st.markdown("---")
    st.subheader("등록된 품목 목록")
    if st.session_state.items:
        items_df = pd.DataFrame([
            {"품목코드": code, "품목명": info["name"]}
            for code, info in st.session_state.items.items()
        ])
        st.dataframe(items_df, use_container_width=True) 