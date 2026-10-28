"""학업중단: '생각'과 '실제 사유' 비교 웹앱 (Streamlit - 최종 완벽 수정 버전)
실행: streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import charts as C

st.set_page_config(page_title="학업중단 생각 vs 실제 사유", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")
BASE = Path(__file__).parent

st.html("""
<style>
    .app-fixed-header {
        position: fixed;
        z-index: 999990;
        top: 0;
        left: 0;
        right: 0;
        height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: flex-start;
        padding: 0 100px 0 24px;
        background: #fff;
        border-bottom: 1px solid #e4e5e9;
        color: #262730;
        font-size: 20px;
        font-weight: 700;
        line-height: 1.2;
    }
    .app-fixed-header .header-source {
        margin-top: 5px;
        font-size: 12px;
        font-weight: 400;
        color: #687080;
    }
    section[data-testid="stSidebar"] {
        top: 80px !important;
        height: calc(100vh - 80px) !important;
        width: 300px !important;
        min-width: 300px !important;
        margin-left: 0 !important;
        transform: none !important;
        visibility: visible !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    .stMainBlockContainer { padding-top: 100px; }
    @media (max-width: 640px) {
        .app-fixed-header { height: 100px; padding-left: 16px; padding-right: 16px; font-size: 15px; }
        .app-fixed-header .header-source { font-size: 11px; }
        [data-testid="stAppViewContainer"] {
            flex-direction: column !important;
            padding-top: 100px;
        }
        section[data-testid="stSidebar"] {
            position: relative !important;
            top: 0 !important;
            width: 100% !important;
            min-width: 100% !important;
            height: 290px !important;
            min-height: 290px !important;
            z-index: 1 !important;
        }
        [data-testid="stSidebarHeader"],
        [data-testid="stSidebarUserContent"] h1 { display: none !important; }
        [data-testid="stMain"] { position: relative !important; top: auto !important; }
        .stMainBlockContainer { padding-top: 24px !important; }
    }
</style>
<div class="app-fixed-header">
    <div>📊 학업중단, 생각과 실제는 어디까지 겹칠까?</div>
    <div class="header-source">자료: 2025 '학업중단 생각 여부 및 이유'(초·중·고) / 2023 '학업 중단 사유' · 단위: % · 상관은 인과가 아님</div>
</div>
""")


@st.cache_data
def load():
    df = pd.read_csv(BASE / "long.csv", encoding="utf-8-sig")
    mp = pd.read_csv(BASE / "mapping.csv", encoding="utf-8-sig")
    return df, mp


df, mapping = load()

# ------------------------------------------------------------------ 세션 상태 초기화 (사이드바 제어용)
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

if "selected_tab_idx" not in st.session_state:
    st.session_state.selected_tab_idx = -1


def add_bookmark(title, tab_idx):
    item = {"title": title, "tab_idx": tab_idx}
    if item not in st.session_state.bookmarks:
        st.session_state.bookmarks.append(item)
        st.toast(f"📌 '{title}' (이)가 북마크에 추가되었습니다!")


def remove_bookmark(idx):
    st.session_state.bookmarks.pop(idx)
    st.rerun()


# ------------------------------------------------------------------ 사이드바 구성

st.sidebar.title("🧭 바로가기 & 탐색")

# 1. 연구 목차
tab_titles = {
    -1: "연구 개요 및 한계",
    0: "Q1 '있다' 비율 분석",
    1: "Q2 이유 순위 (범프 차트)",
    2: "Q3 생각 vs 실제 사유",
    3: "데이터 무결성 검증",
}
st.sidebar.subheader("목차")
selected_tab = st.session_state.selected_tab_idx
st.sidebar.markdown("""
    <style>
    section[data-testid="stSidebar"] div[class*="st-key-toc_"] button {
        justify-content: flex-start !important;
        border: 0;
        padding: 0.35rem 0.75rem !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-toc_"] button > div,
    section[data-testid="stSidebar"] div[class*="st-key-toc_"] button p {
        width: 100%;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-toc_"] button:hover {
        color: #e34b4b;
        background: rgba(227, 75, 75, 0.07);
    }
    section[data-testid="stSidebar"] div.st-key-toc_active button {
        color: #d63333;
        background: rgba(227, 75, 75, 0.1);
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)
with st.sidebar.container(gap=None):
    for tab_idx, title in tab_titles.items():
        key = "toc_active" if tab_idx == selected_tab else f"toc_{tab_idx}"
        st.button(
            title, key=key, type="tertiary", use_container_width=True,
            on_click=lambda idx=tab_idx: st.session_state.update(selected_tab_idx=idx),
        )

st.sidebar.divider()

# 2. 저장된 북마크 바로가기
st.sidebar.subheader("📌 내가 저장한 북마크")
if not st.session_state.bookmarks:
    st.sidebar.caption("저장된 북마크가 없습니다. 그래프 옆의 ⭐ 버튼을 눌러 추가하세요.")
else:
    for b_idx, b_item in enumerate(st.session_state.bookmarks):
        col_b1, col_b2 = st.sidebar.columns([4, 1])
        with col_b1:
            st.button(
                f"🔗 {b_item['title']}", key=f"nav_bm_{b_idx}", use_container_width=True,
                on_click=lambda idx=b_item["tab_idx"]: st.session_state.update(selected_tab_idx=idx),
            )
        with col_b2:
            if st.button("❌", key=f"del_bm_{b_idx}"):
                remove_bookmark(b_idx)

st.sidebar.divider()

# 4. 사이드바 맨 하단: 전역 설정 (테마 및 표본 처리)
st.sidebar.subheader("🎨 대시보드 전역 설정")
theme_choice = st.sidebar.selectbox(
    "🌈 테마 선택",
    ["기본 (Streamlit Standard)", "미드나잇 다크 네온 (Midnight Neon)", "소프트 라벤더 베이지 (Lavender Warm)", "오션 브리즈 다크 (Ocean Breeze)"],
    index=0
)

theme_css = {
    "기본 (Streamlit Standard)": "",
    "미드나잇 다크 네온 (Midnight Neon)": """
        <style>
        .stApp { background-color: #0b0f19; color: #f3f4f6; }
        section[data-testid="stSidebar"] { background-color: #111827; }
        div[data-testid="stMetricValue"] { color: #38bdf8 !important; }
        h1, h2, h3 { color: #38bdf8 !important; }
        </style>
    """,
    "소프트 라벤더 베이지 (Lavender Warm)": """
        <style>
        .stApp { background-color: #faf5ff; color: #3b0764; }
        section[data-testid="stSidebar"] { background-color: #f3e8ff; }
        div[data-testid="stMetricValue"] { color: #7e22ce !important; }
        h1, h2, h3 { color: #6b21a8 !important; }
        </style>
    """,
    "오션 브리즈 다크 (Ocean Breeze)": """
        <style>
        .stApp { background-color: #022c22; color: #ccfbf1; }
        section[data-testid="stSidebar"] { background-color: #064e3b; }
        div[data-testid="stMetricValue"] { color: #2dd4bf !important; }
        h1, h2, h3 { color: #2dd4bf !important; }
        </style>
    """
}
st.markdown(theme_css[theme_choice], unsafe_allow_html=True)

excl = st.sidebar.toggle("표본 주의 집단 제외·회색 표시", value=True,
                         help="계획서에서 0.0 칸·큰 값이 있어 해석을 보류하기로 한 집단(가족유형별 조손가정·기타)")
st.sidebar.caption("⚠ 표본 크기·오차는 원자료에 없어 '유의하다'는 표현을 쓰지 않습니다.")


# ------------------------------------------------------------------ 메인 화면 출력

if selected_tab == -1:
    st.subheader("📖 연구 개요 및 한계")
    st.markdown(
        "- **Q①** 학업중단을 생각한 적 '있다'는 비율은 학교급·학업성적·경제적 수준에 따라 몇 %p 다른가?\n"
        "- **Q②** 학업중단 생각 이유 1순위는 초·중·고에서 어떻게 달라지며, 고등학교에서 가장 높은 항목은?\n"
        "- **Q③** 2023 실제 중단 사유와 2025 중단 생각 이유에서 대응되는 항목의 비율은 각각 얼마인가?")
    c1, c2 = st.columns(2)
    with c1:
        st.success("**말할 수 있는 것**\n\n- 2025 안에서 집단별 '있다' 비율의 차이(%p)\n- 학교급별 이유의 순위·비율 변화\n- 의미가 비슷한 항목의 순위·비중 방향")
    with c2:
        st.error("**말할 수 없는 것**\n\n- 2023과 2025의 단순 '증감'\n- 집단 차이의 '원인'(상관 ≠ 인과)\n- '생각한 학생이 그대로 중단한다'는 연결")

elif selected_tab == 3:
    st.subheader("🔍 데이터 무결성 검증")
    st.subheader("가공 데이터 및 합계 검증")
    year = st.selectbox("조사연도 선택", sorted(df["조사연도"].unique()), key="val_year")
    st.dataframe(df[df["조사연도"] == year], hide_index=True, use_container_width=True)
    st.download_button("long.csv 내려받기", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="long.csv", mime="text/csv")

# ------------------------------------------------------------------ 탭 0: Q① '있다' 비율 분석
if selected_tab == 0:
    col_t1, col_bm1 = st.columns([10, 1])
    with col_t1:
        st.subheader("Q① 학업중단을 생각한 적 '있다' 비율 격차 분석")
    with col_bm1:
        if st.button("⭐", key="bm_q1_top", help="이 섹션 북마크에 추가"):
            add_bookmark("Q① 생각 '있다' 비율 분석", 0)

    c_g1, col_bm_g1 = st.columns([10, 1])
    with col_bm_g1:
        if st.button("⭐", key="bm_q1_c1", help="차트 북마크"):
            add_bookmark("Q① 격차 비교 바차트", 0)
    with c_g1:
        st.plotly_chart(C.fig_q1_gap(df, excl), use_container_width=True)

    st.subheader("특성별 집단 비교")
    for feature in C.gap_table(df, excl)["특성"]:
        st.plotly_chart(C.fig_q1_bar(df, feature, excl), use_container_width=True,
                        key=f"q1_detail_{feature}")

# ------------------------------------------------------------------ 탭 1: Q② 이유 순위 (범프 영역 y축 1위 상단 고정)
elif selected_tab == 1:
    col_t2, col_bm2 = st.columns([10, 1])
    with col_t2:
        st.subheader("Q② 학교급별 학업중단 생각 이유 순위 변화")
    with col_bm2:
        if st.button("⭐", key="bm_q2_top", help="이 섹션 북마크에 추가"):
            add_bookmark("Q② 학교급별 이유 순위", 1)

    c_q2_ch, c_bm_q2 = st.columns([10, 1])
    with c_bm_q2:
        if st.button("⭐", key="bm_q2_chart", help="차트 북마크"):
            add_bookmark("Q② 범프/영역 순위 차트", 1)
    kind = st.radio("그래프 형식 선택", ["범프 영역 (순위+크기)", "범프 선 (순위만)"], horizontal=True)
    etc = st.toggle("'기타' 포함", value=(kind != "범프 선 (순위만)"),
                    help="'기타'는 이유가 아닌 묶음 항목이라 순위 비교에서는 빼는 편이 해석하기 좋습니다.")
    if kind.startswith("범프 영역"):
        mode = st.radio("두께 기준 선택", ["전체 학생 중 환산(%)", "'있다' 응답자 중 비율(%)"], horizontal=True)

    with c_q2_ch:
        if kind.startswith("범프 영역"):
            md = "환산" if mode.startswith("전체") else "이유내"
            fig_q2 = C.fig_q2_area(df, md, etc)
            st.plotly_chart(fig_q2, use_container_width=True)
        else:
            fig_q2 = C.fig_q2_bump(df, etc)
            # 1위가 상단에 오도록 y축 반전
            fig_q2.update_layout(yaxis=dict(autorange="reversed", dtick=1))
            st.plotly_chart(fig_q2, use_container_width=True)

    wide = C.level_reasons(df, include_etc=False)
    hs = wide["고등학교"].idxmax()
    st.info("고등학교에서 1순위 비율이 가장 높은 항목('기타' 제외): **%s** (%.1f%%). 2위 **%s** (%.1f%%)." % (
        hs, wide.loc[hs, "고등학교"],
        wide["고등학교"].drop(hs).idxmax(), wide["고등학교"].drop(hs).max()))
    
    tbl = C.level_reasons(df, include_etc=True).copy()
    tbl.columns = [c + " (%)" for c in tbl.columns]
    st.dataframe(tbl, use_container_width=True)

# ------------------------------------------------------------------ 탭 2: Q③ 생각 vs 실제 (범프 영역 차트 선택 시 실제 시각화 구현)
elif selected_tab == 2:
    col_t3, col_bm3 = st.columns([10, 1])
    with col_t3:
        st.subheader("Q③ 실제 중단 사유(2023) ↔ 중단 생각 이유(2025) 격차 비교")
    with col_bm3:
        if st.button("⭐", key="bm_q3_top", help="이 섹션 북마크에 추가"):
            add_bookmark("Q③ 생각 vs 실제 비교 분석", 2)

    c_q3_ch, c_bm_q3 = st.columns([10, 1])
    with c_bm_q3:
        if st.button("⭐", key="bm_q3_chart", help="차트 북마크"):
            add_bookmark("Q③ 시각화 비교 차트", 2)

    view = st.radio("표시 방식 선택", ["원자료 비율", "대응 항목 안 상대비중"], horizontal=True)
    st.subheader("대응 항목별 비율")
    tier = "완화"
    sort_year = "2025"
    display_mode = "원자료" if view == "원자료 비율" else "상대"
    with c_q3_ch:
        st.caption("각 연도 안에서 비율이 높은 항목부터 위에 표시합니다.")
        fig = C.fig_q3_area(df, mapping, tier, display_mode, sort_year)
        st.plotly_chart(fig, use_container_width=True)

    mt = C.match_table(df, mapping, tier).sort_values(
        f"{sort_year} 값(%)", ascending=False, kind="stable")

    item_colors = {trace.name: trace.fillcolor for trace in fig.data}
    dark_colors = {"#4E79A7", "#E15759", "#59A14F", "#B07AA1", "#9C755F"}
    correspondence = mt[["표시이름", "항목_2023", "항목_2025", "차이(%p)",
                         "2023 순위", "2025 순위", "상대비중 차(%p)"]].copy()
    correspondence["항목_2023"] = [f"{item} ({value:.1f}%)" for item, value in zip(mt["항목_2023"], mt["2023 값(%)"])]
    correspondence["항목_2025"] = [f"{item} ({value:.1f}%)" for item, value in zip(mt["항목_2025"], mt["2025 값(%)"])]
    correspondence = correspondence.rename(
        columns={"표시이름": "대응 항목", "항목_2023": "2023 실제 중단 사유", "항목_2025": "2025 중단 생각 이유"})
    def correspondence_color(item):
        color = item_colors[item]
        text_color = "white" if color in dark_colors else "#202020"
        return f"background-color: {color}; color: {text_color}"
    styled = correspondence.style.map(correspondence_color, subset=["대응 항목"]).format(
        {"차이(%p)": "{:.1f}", "상대비중 차(%p)": "{:.1f}"})
    st.dataframe(styled,
                 hide_index=True, use_container_width=True)
    
    st.warning("두 조사는 연도·응답 대상·선택지 구성이 달라 '줄었다/늘었다'가 아니라 "
               "대응 항목의 순위와 비중의 방향만 비교합니다.")
