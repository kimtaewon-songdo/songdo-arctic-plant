import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

# ---------- 한글 폰트 설정 ----------
def setup_korean_font():
    """한글 폰트가 깨지지 않도록 matplotlib에 한글 폰트를 등록"""
    for font in fm.findSystemFonts():
        if "Nanum" in font or "Gothic" in font or "Malgun" in font:
            fm.fontManager.addfont(font)
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False

setup_korean_font()

# ---------- CSV 인코딩 자동 감지 ----------
def read_csv_auto(file):
    """utf-8-sig로 먼저 읽고 실패하면 cp949로 다시 읽기"""
    try:
        data = file.getvalue()
        return pd.read_csv(pd.io.common.StringIO(data.decode("utf-8-sig")))
    except UnicodeDecodeError:
        data = file.getvalue()
        return pd.read_csv(pd.io.common.StringIO(data.decode("cp949")))

# ---------- 제목 ----------
st.set_page_config(page_title="극지식물 생육 분석 대시보드", layout="wide")
st.title("🌿 극지식물 개체별 생육 차이 분석 대시보드")

# ---------- 사이드바 ----------
st.sidebar.header("📂 데이터 업로드")
env_file = st.sidebar.file_uploader("환경 데이터 (CSV)", type=["csv"], key="env")
grow_file = st.sidebar.file_uploader("생육 결과 데이터 (CSV/XLSX)", type=["csv", "xlsx"], key="grow")

# 생육 측정 항목 선택 (생육 컬럼 중 선택 가능한 항목)
growth_columns = ["잎 수(장)", "지상부 길이(mm)", "지하부길이(mm)", "생중량(g)", "지상부질량(g)", "지하부질량(g)"]
if grow_file is not None:
    grow_df = read_csv_auto(grow_file) if grow_file.name.endswith(".csv") else pd.read_excel(grow_file)
    # 생육 결과 데이터에 열 이름 정리 (단위·띄어쓰기 문제로 KeyError 방지)
    grow_df.columns = grow_df.columns.str.strip()
    growth_options = [c for c in growth_columns if c in grow_df.columns]
    selected_growth = st.sidebar.multiselect("생육 측정 항목 선택", options=growth_options, default=growth_options)
else:
    grow_df = None
    selected_growth = []

# 학교명 (파일명 앞부분에서 추출, 하드코딩 금지)
school = os.path.splitext(os.path.basename(env_file.name))[0] if env_file is not None else "학교명"
if grow_file is not None:
    school = os.path.splitext(os.path.basename(grow_file.name))[0]
st.sidebar.text(f"학교명: {school}")

# ---------- 안내 문구 ----------
if env_file is None and grow_file is None:
    st.info("CSV 파일을 업로드해 주세요. 환경 데이터와 생육 결과 데이터를 각각 업로드하면 대시보드가 실행됩니다.")

# ---------- 탭 구성 ----------
tab1, tab2, tab3 = st.tabs(["환경 데이터 요약", "생육 결과 분석", "환경 vs 생육 상관 분석"])

with tab1:
    st.header("환경 데이터 요약")
    if env_file is not None:
        env_df = read_csv_auto(env_file)
        env_df.columns = env_df.columns.str.strip()
        st.subheader(f"📊 {school} 환경 데이터 개요")
        st.write(f"총 {len(env_df)}개 행, {env_df.shape[1]}개 열")

        # 시간 열 처리 (학교마다 다른 형식 지원)
        time_cols = [c for c in env_df.columns if "time" in c.lower()]
        if time_cols:
            env_df[time_cols[0]] = pd.to_datetime(env_df[time_cols[0]], errors="coerce")
            env_df = env_df.dropna(subset=[time_cols[0]])

        st.write("### 환경 데이터 통계")
        st.write(env_df.describe())

        st.write("### 시간별 환경 변화 추이")
        if time_cols:
            fig, ax = plt.subplots(figsize=(10, 4))
            for col in env_df.columns:
                if col != time_cols[0]:
                    ax.plot(env_df[time_cols[0]], env_df[col], label=col, marker="o", markersize=3)
            ax.set_xlabel("시간")
            ax.set_ylabel("값")
            ax.set_title("환경 데이터 시계열")
            ax.legend(loc="upper left", fontsize=8)
            st.pyplot(fig)
    else:
        st.info("환경 데이터가 업로드되면 여기에 그래프가 표시됩니다.")

with tab2:
    st.header("생육 결과 분석")
    if grow_df is not None:
        st.subheader(f"📊 {school} 생육 결과 개요")
        st.write(f"총 {len(grow_df)}개 개체")

        # 생중량(g) 열이 없는 경우 지상부질량 + 지하부질량으로 계산
        if "생중량(g)" not in grow_df.columns:
            if "지상부질량(g)" in grow_df.columns and "지하부질량(g)" in grow_df.columns:
                grow_df["생중량(g)"] = grow_df["지상부질량(g)"] + grow_df["지하부질량(g)"]
                st.info("생체중량(g) 열이 없어 지상부질량 + 지하부질량으로 계산했습니다.")
            else:
                st.warning("생체중량과 관련된 열(지상부질량/지하부질량)이 없습니다. 확인할 수 없습니다.")

        # 뿌리 관련 지표 계산 (없는 경우 자동 계산)
        if "지하부길이(mm)" not in grow_df.columns:
            if "지상부길이(mm)" in grow_df.columns and "지하부길이(mm)" in grow_df.columns:
                grow_df["뿌리길이(mm)"] = grow_df["지상부길이(mm)"] - grow_df["지하부길이(mm)"]
                st.info("지하부길이 열이 없어 지상부길이 - 지하부길이로 계산했습니다.")
            else:
                st.warning("지하부길이 열을 찾을 수 없습니다.")

        # 개체번호는 분석 항목에서 제외
        numeric_cols = grow_df.select_dtypes(include="number").columns
        numeric_cols = [c for c in numeric_cols if c != "개체번호"]

        if selected_growth:
            selected_data = grow_df[selected_growth]
            st.write("### 선택한 생육 항목 통계")
            st.write(selected_data.describe())

            # 개체별 비교
            st.write("### 개체별 생육 비교 (개체번호 제외, 전체 개체 비교)")
            col1, col2 = st.columns(2)
            with col1:
                if "생체중량(g)" in selected_data.columns:
                    fig, ax = plt.subplots()
                    ax.bar(selected_data.index, selected_data["생체중량(g)"], color="green", alpha=0.7)
                    ax.set_xlabel("개체 번호")
                    ax.set_ylabel("생체중량(g)")
                    ax.set_title("개체별 생체중량 비교")
                    st.pyplot(fig)
            with col2:
                if "지상부길이(mm)" in selected_data.columns:
                    fig, ax = plt.subplots()
                    ax.bar(selected_data.index, selected_data["지상부길이(mm)"], color="blue", alpha=0.7)
                    ax.set_xlabel("개체 번호")
                    ax.set_ylabel("지상부 길이(mm)")
                    ax.set_title("개체별 지상부 길이 비교")
                    st.pyplot(fig)

            # 평균·표준편차 기술 통계
            st.write("### 평균·표준편차 (중심 경향 및 분산)")
            stats = selected_data.describe().loc[["mean", "std"]]
            st.write(stats)
        else:
            st.info("사이드바에서 생육 측정 항목을 선택해 주세요.")
    else:
        st.info("생육 결과 데이터가 업로드되면 개체별 생육 비교가 표시됩니다.")

with tab3:
    st.header("환경 vs 생육 상관 분석")
    if env_file is not None and grow_file is not None:
        # 환경 데이터 다시 로드
        env_df = read_csv_auto(env_file)
        env_df.columns = env_df.columns.str.strip()
        time_cols = [c for c in env_df.columns if "time" in c.lower()]
        if time_cols:
            env_df[time_cols[0]] = pd.to_datetime(env_df[time_cols[0]], errors="coerce")
            env_df = env_df.dropna(subset=[time_cols[0]])

        # 환경 데이터 집계 (학교마다 시간 형식 다름)
        env_numeric = env_df.select_dtypes(include="number")
        env_summary = env_numeric.mean().to_frame("환경 평균")
        env_summary["환경 표준편차"] = env_numeric.std()
        st.write("### 환경 데이터 요약 통계")
        st.write(env_summary)

        # 생육 데이터와 병합 가능한 경우 상관 분석
        if grow_df is not None:
            st.write("### 환경 요인과 생육 요인 상관 분석")
            # 개체별 생육 데이터를 시간별로 집계할 수 없으므로, 환경 평균은 그대로 사용하고
            # 생육 데이터는 전체 평균 기준으로 비교
            grow_numeric = grow_df.select_dtypes(include="number")
            grow_rate = grow_numeric.mean().to_frame("생육 평균")
            combined = pd.concat([env_summary, grow_rate], axis=1)

            # 상관 계수 계산 (환경 평균과 생육 평균 간 상관)
            corr = combined.corr()
            st.write("### 상관 계수 행렬")
            st.write(corr)

            # 산점도
            if "생체중량(g)" in combined.columns and "temperature" in combined.columns:
                fig, ax = plt.subplots()
                ax.scatter(combined["temperature"], combined["생체중량(g)"], alpha=0.7, color="purple")
                ax.set_xlabel("온도(°C)")
                ax.set_ylabel("생체중량(g)")
                ax.set_title("온도와 생체중량 상관")
                st.pyplot(fig)
    else:
        st.info("환경 데이터와 생육 결과 데이터를 모두 업로드하면 상관 분석 결과가 표시됩니다.")
