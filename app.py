import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

# ---------------------------------------------------
# 1. 데이터 불러오기
# ---------------------------------------------------
#df = pd.read_csv("고양시_카페_10개시점.csv", encoding="utf-8")
csv_url = "https://raw.githubusercontent.com/jaeyong0213/goyang_cafe_analysis_1/main/goyang_cafe_10.csv"
df = pd.read_csv(csv_url, encoding='utf-8')


# 결측 제거
df = df.dropna(subset=["위도", "경도"])

# ---------------------------------------------------
# 2. 생존기간 계산 (월 단위)
# ---------------------------------------------------
def calculate_survival_months(group):
    """같은 카페(상호명 + 좌표)의 연속 출현 개수를 운영 개월 수로 계산"""
    months = len(group["연월"].unique()) * 3   # 한 시점 = 3개월 간격
    return months

survival_df = (
    df.groupby(["상호명", "위도", "경도"])
      .apply(calculate_survival_months)
      .reset_index(name="survival_months")
)

# 원본 데이터에 survival 정보 merge
df = df.merge(survival_df, on=["상호명", "위도", "경도"], how="left")

# ---------------------------------------------------
# 3. Streamlit UI
# ---------------------------------------------------
st.title("📍 고양시 카페 입지 분석 도구")

# 카페 유형 선택
cafe_choice = st.radio(
    "☕ 어떤 카페를 열고 싶은가요?",
    ["개인카페", "스타벅스", "이디야", "메가커피", "투썸", "할리스", "컴포즈", "빽다방"]
)

st.write("지도를 클릭해 입지를 선택하세요!")

# ---------------------------------------------------
# 4. 지도 표시
# ---------------------------------------------------
center_lat = df["위도"].mean()
center_lon = df["경도"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

clicked = st_folium(m, width=700, height=500)

# ---------------------------------------------------
# 5. 사용자 클릭 좌표 가져오기
# ---------------------------------------------------
if clicked["last_clicked"] is not None:

    user_lat = clicked["last_clicked"]["lat"]
    user_lon = clicked["last_clicked"]["lng"]
    user_point = (user_lat, user_lon)

    st.success(f"✅ 선택한 위치: {user_lat:.5f}, {user_lon:.5f}")

    # ---------------------------------------------------
    # 6. 반경 500m 내 카페 필터링
    # ---------------------------------------------------
    radius_km = 0.5

    def is_within_radius(row):
        return geodesic((row["위도"], row["경도"]), user_point).km <= radius_km

    df_nearby = df[df.apply(is_within_radius, axis=1)]

    st.write(f"📌 반경 500m 내 카페 수: {len(df_nearby)}개")

    if len(df_nearby) == 0:
        st.warning("반경 500m 안에 카페가 없습니다.")
    else:
        # ---------------------------------------------------
        # 7. 사용자가 선택한 카페 유형 분석
        # ---------------------------------------------------
        if cafe_choice == "개인카페":
            df_competitor = df_nearby[df_nearby["is_franchise"] == False]
        else:
            df_competitor = df_nearby[df_nearby["상호명"].str.contains(cafe_choice.upper(), na=False)]

        competitor_count = len(df_competitor)

        # ---------------------------------------------------
        # 8. 생존 기간 평균 계산
        # ---------------------------------------------------
        avg_survival = df_nearby["survival_months"].mean()
        years = int(avg_survival // 12)
        months = int(avg_survival % 12)

        # ---------------------------------------------------
        # 9. 결과 메시지 생성
        # ---------------------------------------------------
        st.subheader("📊 입지 분석 결과")

        st.info(
            f"""
            ✅ **반경 500m 내 평균 운영 기간: {years}년 {months}개월**

            ✅ 선택한 카페 유형: **{cafe_choice}**

            ✅ 해당 유형 경쟁자 수: **{competitor_count}개**
            """
        )

        # 추천 메시지 (간단 모델)
        if competitor_count == 0:
            st.success("🎉 경쟁자가 거의 없어 좋은 입지입니다!")
        elif competitor_count <= 2:
            st.info("🙂 경쟁이 심하지만 도전할 수 있는 위치입니다.")
        else:
            st.error("⚠️ 경쟁이 매우 심한 위치입니다. 신중한 검토가 필요합니다.")






