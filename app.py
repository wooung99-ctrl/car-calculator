import math
import streamlit as st

st.set_page_config(
    page_title="중고차 경매 실전 입찰가 & 캠핑카 개조 세금 계산기",
    layout="wide",
)

st.title("🚗 중고차 경매 실전 입찰가 & 캠핑카 개조 세금 계산기")
st.markdown("업로드해주신 엑셀 파일의 모든 수식과 로직을 완벽하게 구현한 웹 계산기입니다.")

st.sidebar.header("1. 핵심 조건 입력")

car_model = st.sidebar.selectbox(
    "차량명 / 모델 (선택)",
    [
        "스타리아 7-9인승",
        "스타리아 3-5인승",
        "스타리아 11인승",
        "스타렉스 3-5인승",
        "스타렉스 9인승",
        "스타렉스 11-12인승",
    ],
)

# 차종 구분 자동 연동
if car_model in ["스타리아 3-5인승", "스타렉스 3-5인승"]:
  car_type = "화물"
elif car_model in ["스타리아 7-9인승", "스타렉스 9인승"]:
  car_type = "승용"
else:
  car_type = "승합"

st.sidebar.text(f"차종 구분 (자동연동): {car_type}")

# 기본 취득세율 자동 연동 (화물·승합 5%, 승용 7%)
tax_rate = 0.05 if car_type in ["화물", "승합"] else 0.07
st.sidebar.text(f"기본 취득세율: {tax_rate * 100:.1f}%")

auction_type = st.sidebar.selectbox(
    "경매 출품 거래 형태", ["법인(부가세 별도)", "법인(부가세 포함)", "개인(특례)"]
)

market_price = st.sidebar.number_input(
    "플랫폼 시세가 (참고용)", value=40000000, step=1000000
)
customer_price = st.sidebar.number_input(
    "고객 판매가 (실제 적용가)", value=10000000, step=500000
)

supply_price = customer_price / 1.1
st.sidebar.text(f"공급가액 (부가세 제외): {supply_price:,.2f} 원")

target_margin = st.sidebar.number_input(
    "목표 순수 마진", value=1000000, step=100000
)

st.sidebar.header("2. 부대비용 설정 (고정)")
refurb_cost = st.sidebar.number_input("예상 상품화 비용", value=800000, step=50000)
delivery_fee = st.sidebar.number_input(
    "탁송비 (입고+출고)", value=150000, step=10000
)
transfer_fee = st.sidebar.number_input("이전 대행료", value=100000, step=10000)
misc_fee = st.sidebar.number_input("주유비 및 기타잡비", value=50000, step=10000)


# 3. 입찰가 산정 로직 (엑셀 C17 수식 완벽 구현)
def calc_base_bid(c10, c13, c14, c15, c16, c12, c7, c8_type):
  term = (c10 / 1.1) - c13 - c14 - c15 - c16 - c12
  if c8_type == "법인(부가세 별도)":
    if (term - 110000) < 5000000:
      return term - 110000
    elif (term / 1.022) <= 20000000:
      return term / 1.022
    elif (term - 440000) * c7 <= 2000000:
      return term - 440000
    else:
      return (term - 440000) / (1 + 0.15 * c7)
  else:
    if (1.1 * (term - 110000)) < 5000000:
      return 1.1 * (term - 110000)
    elif term / ((1 / 1.1) + 0.022) <= 20000000:
      return term / ((1 / 1.1) + 0.022)
    elif (1.1 * (term - 440000)) * c7 <= 2000000:
      return 1.1 * (term - 440000)
    else:
      return (1.1 * (term - 440000)) / (1 + 0.15 * c7)


base_bid = calc_base_bid(
    customer_price,
    refurb_cost,
    delivery_fee,
    transfer_fee,
    misc_fee,
    target_margin,
    tax_rate,
    auction_type,
)
final_bid = math.floor(base_bid / 50000) * 50000

# 4. 실제 비용 확정
vat_separate = final_bid * 0.1 if auction_type == "법인(부가세 별도)" else 0
auction_fee = min(max(final_bid * 0.022, 110000), 440000)
total_paid = final_bid + vat_separate + auction_fee

calc_tax = (
    (final_bid / 1.1) * tax_rate
    if auction_type == "법인(부가세 포함)"
    else final_bid * tax_rate
)
tax_applied = 0 if calc_tax <= 2000000 else calc_tax * 0.15

sales_vat = (customer_price / 1.1) * 0.1
purch_vat = (
    final_bid * 0.1
    if auction_type == "법인(부가세 별도)"
    else (final_bid / 1.1) * 0.1
)
vat_settlement = max(0, sales_vat - purch_vat)

total_expense = (
    total_paid
    + refurb_cost
    + delivery_fee
    + transfer_fee
    + misc_fee
    + tax_applied
    + vat_settlement
)
expected_profit = customer_price - total_expense

st.header("📊 중고차 경매 입찰가 산정 및 정산 결과")
col1, col2, col3 = st.columns(3)
col1.metric("기준 입찰가", f"{base_bid:,.0f} 원")
col2.metric("최종 입찰가 (5만 원 단위)", f"{final_bid:,.0f} 원")
col3.metric("예상 순이익", f"{expected_profit:,.0f} 원")

st.markdown("---")
st.subheader("상세 비용 내역")
st.write(f"- **경매 수수료 (확정):** {auction_fee:,.0f} 원")
st.write(f"- **최종 납부 금액 (경매업체):** {total_paid:,.0f} 원")
st.write(f"- **산출 취득세:** {calc_tax:,.0f} 원 (적용액: {tax_applied:,.0f} 원)")
st.write(f"- **부가세 정산액 (추가납부):** {vat_settlement:,.0f} 원")
st.write(f"- **예상 총 지출 비용:** {total_expense:,.0f} 원")

# 캠핑카 개조 구조변경 세금 계산기
st.markdown("---")
st.header("🚐 구조변경(캠핑카 개조) 세금 계산기")

col_c1, col_c2 = st.columns(2)
with col_c1:
  car_value = st.number_input(
      "차량가액 (개조 전, 부가세 제외)", value=14310000, step=100000
  )
  tuning_cost = st.number_input(
      "개조(튜닝) 비용 (부가세 별도)", value=7500000, step=100000
  )
with col_c2:
  individual_tax_rate = st.selectbox(
      "개별소비세율", ["5%", "3.5%"], index=0
  )
  tax_history = st.selectbox(
      "최초 구입 시 개별소비세 납부 이력",
      [
          "면제 차량(화물·승합 등) - 개소세 부과 대상",
          "기납부 차량(승용 등) - 개소세 재부과 없음",
      ],
  )

rate_val = 0.035 if individual_tax_rate == "3.5%" else 0.05
if tax_history == "기납부 차량(승용 등) - 개소세 재부과 없음":
  individual_tax = 0
else:
  individual_tax = (car_value + tuning_cost) * rate_val

education_tax = individual_tax * 0.3
vat_tuning = (tuning_cost + individual_tax + education_tax) * 0.1
tuning_tax_subtotal = individual_tax + education_tax + vat_tuning
plate_fee = st.number_input("번호판 교체비용", value=28000, step=1000)
total_tuning_cost = tuning_tax_subtotal + plate_fee

st.subheader("구조변경 세금 산정 결과")
st.write(f"- **개별소비세:** {individual_tax:,.0f} 원")
st.write(f"- **교육세:** {education_tax:,.0f} 원")
st.write(f"- **부가가치세:** {vat_tuning:,.0f} 원")
st.write(f"- **튜닝 관련 세금 소계:** {tuning_tax_subtotal:,.0f} 원")
st.metric("구조변경 총비용", f"{total_tuning_cost:,.0f} 원")
