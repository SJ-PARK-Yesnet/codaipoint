import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# 데이터 저장 파일 경로
CUSTOMERS_FILE = 'customers.json'
TRANSACTIONS_FILE = 'transactions.json'

# 초기 데이터 로드 또는 생성
def load_or_create_data():
    if not os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'w') as f:
            json.dump([], f)
    
    with open(CUSTOMERS_FILE, 'r') as f:
        customers = json.load(f)
    
    with open(TRANSACTIONS_FILE, 'r') as f:
        transactions = json.load(f)
    
    return customers, transactions

# 데이터 저장
def save_data(customers, transactions):
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump(customers, f)
    
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(transactions, f)

# 세션 상태 초기화
if 'customers' not in st.session_state:
    st.session_state.customers, st.session_state.transactions = load_or_create_data()

# 페이지 설정
st.set_page_config(page_title="거래 관리 시스템", layout="wide")
st.title("거래 관리 시스템")

# 상단부 - 날짜, 거래처, 포인트 정보
col1, col2 = st.columns(2)

with col1:
    selected_date = st.date_input("거래일자", datetime.now())
    
with col2:
    customer_name = st.text_input("거래처(고객명)")
    if customer_name:
        current_points = st.session_state.customers.get(customer_name, 0)
        st.info(f"현재 적립 포인트: {current_points:,} 점")

# 중간부 - 포인트 사용
if customer_name:
    points_to_use = st.number_input("사용할 포인트", min_value=0, max_value=int(st.session_state.customers.get(customer_name, 0)))
    if st.button("포인트 사용"):
        if points_to_use > 0:
            st.session_state.customers[customer_name] -= points_to_use
            st.success(f"{points_to_use:,} 포인트가 사용되었습니다.")
            save_data(st.session_state.customers, st.session_state.transactions)
            st.rerun()

# 하단부 - 거래 정보 입력
st.subheader("거래 정보")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    item = st.text_input("품목")
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

# 거래 등록 버튼
if st.button("거래 등록"):
    if not customer_name:
        st.error("거래처(고객명)를 입력해주세요.")
    elif not item or quantity == 0 or price == 0:
        st.error("품목, 수량, 단가를 모두 입력해주세요.")
    else:
        # 포인트 적립 (총액의 1%)
        total_amount = supply_value + vat
        points = int(total_amount * 0.01)
        
        # 거래 정보 저장
        transaction = {
            "date": selected_date.strftime("%Y-%m-%d"),
            "customer": customer_name,
            "item": item,
            "quantity": quantity,
            "price": price,
            "supply_value": supply_value,
            "vat": vat,
            "points": points
        }
        st.session_state.transactions.append(transaction)
        
        # 포인트 적립
        if customer_name not in st.session_state.customers:
            st.session_state.customers[customer_name] = 0
        st.session_state.customers[customer_name] += points
        
        # 데이터 저장
        save_data(st.session_state.customers, st.session_state.transactions)
        
        st.success(f"거래가 등록되었습니다. {points:,} 포인트가 적립되었습니다.")
        st.rerun() 