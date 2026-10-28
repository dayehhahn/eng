"""학업중단: '생각'과 '실제 사유' 비교 웹앱 (Streamlit - 최종 완벽 수정 버전)
실행: streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import charts as C

st.set_page_config(page_title="학업중단 생각 vs 실제 사유", page_icon="📊", layout="wide")
BASE = Path(__file__).parent


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
    st.session_state.selected_tab_idx = 0

if "show_overview" not in st.session_state:
    st.session_state.show_overview = False

if "show_validation" not in st.session_state:
    st.session_state.show_validation = False


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

# 1. 사이드바 핵심 질문 3개 바로가기 (클릭 시 세션 변수 변경 및 즉시 이동)
st.sidebar.subheader("🎯 질문 바로가기")
col_q1, col_q2, col_q3 = st.sidebar.columns(3)
if col_q1.button("Q①", use_container_width=True, help="Q① '있다' 비율 분석"):
    st.session_state.selected_tab_idx = 0
    st.rerun()
if col_q2.button("Q②", use_container_width=True, help="Q② 학교급별 이유 순위"):
    st.session_state.selected_tab_idx = 1
    st.rerun()
if col_q3.button("Q③", use_container_width=True, help="Q③ 생각 vs 실제 사유"):
    st.session_state.selected_tab_idx = 2
    st.rerun()

st.sidebar.divider()

# 2. 저장된 북마크 바로가기
st.sidebar.subheader("📌 내가 저장한 북마크")
if not st.session_state.bookmarks:
    st.sidebar.caption("저장된 북마크가 없습니다. 그래프 옆의 ⭐ 버튼을 눌러 추가하세요.")
else:
    for b_idx, b_item in enumerate(st.session_state.bookmarks):
        col_b1, col_b2 = st.sidebar.columns([4, 1])
        with col_b1:
            if st.button(f"🔗 {b_item['title']}", key=f"nav_bm_{b_idx}", use_container_width=True):
                st.session_state.selected_tab_idx = b_item["tab_idx"]
                st.rerun()
        with col_b2:
            if st.button("❌", key=f"del_bm_{b_idx}"):
                remove_bookmark(b_idx)

st.sidebar.divider()

# 3. 사이드바 하단: 연구실 레퍼런스 (개요 & 검증 모달)
st.sidebar.subheader("🚀 연구실 레퍼런스")
if st.sidebar.button("📖 연구 개요 및 한계 보기", key="quick_overview", use_container_width=True):
    st.session_state.show_overview = not st.session_state.show_overview
    st.rerun()

if st.sidebar.button("🔍 데이터 무결성 검증 보기", key="quick_validation", use_container_width=True):
    st.session_state.show_validation = not st.session_state.show_validation
    st.rerun()

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

st.title("📊 학업중단, 생각과 실제는 어디까지 겹칠까?")
st.caption("자료: 2025 '학업중단 생각 여부 및 이유'(초·중·고) / 2023 '학업 중단 사유' · 단위: % · 상관은 인과가 아님")

# 사이드바 레퍼런스 클릭 시 토글 표시
if st.session_state.show_overview:
    with st.expander("📖 [연구실 레퍼런스] 연구 개요 및 한계", expanded=True):
        if st.button("닫기 ❌", key="close_ov"):
            st.session_state.show_overview = False
            st.rerun()
        st.markdown(
            "- **Q①** 학업중단을 생각한 적 '있다'는 비율은 학교급·학업성적·경제적 수준에 따라 몇 %p 다른가?\n"
            "- **Q②** 학업중단 생각 이유 1순위는 초·중·고에서 어떻게 달라지며, 고등학교에서 가장 높은 항목은?\n"
            "- **Q③** 2023 실제 중단 사유와 2025 중단 생각 이유에서 대응되는 항목의 비율은 각각 얼마인가?")
        c1, c2 = st.columns(2)
        with c1:
            st.success("**말할 수 있는 것**\n\n- 2025 안에서 집단별 '있다' 비율의 차이(%p)\n- 학교급별 이유의 순위·비율 변화\n- 의미가 비슷한 항목의 순위·비중 방향")
        with c2:
            st.error("**말할 수 없는 것**\n\n- 2023과 2025의 단순 '증감'\n- 집단 차이의 '원인'(상관 ≠ 인과)\n- '생각한 학생이 그대로 중단한다'는 연결")

if st.session_state.show_validation:
    with st.expander("🔍 [연구실 레퍼런스] 데이터 무결성 검증", expanded=True):
        if st.button("닫기 ❌", key="close_val"):
            st.session_state.show_validation = False
            st.rerun()
        st.subheader("가공 데이터 및 합계 검증")
        year = st.selectbox("조사연도 선택", sorted(df["조사연도"].unique()), key="val_year")
        st.dataframe(df[df["조사연도"] == year], hide_index=True, use_container_width=True)
        st.download_button("long.csv 내려받기", df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="long.csv", mime="text/csv")

st.divider()

# 메인 3대 질문 탭 (세션 상태와 라디오 동기화)
tab_titles = ["① Q① '있다' 비율 분석", "② Q② 이유 순위 (범프 차트)", "③ Q③ 생각 vs 실제 사유"]

selected_tab = st.radio(
    "분석 질문 선택",
    options=list(range(len(tab_titles))),
    format_func=lambda x: tab_titles[x],
    index=st.session_state.selected_tab_idx,
    horizontal=True,
    key="main_tab_radio"
)

# 세션 인덱스 업데이트
st.session_state.selected_tab_idx = selected_tab

st.divider()

# ------------------------------------------------------------------ 탭 0: Q① '있다' 비율 분석
if selected_tab == 0:
    col_t1, col_bm1 = st.columns([10, 1])
    with col_t1:
        st.subheader("Q① 학업중단을 생각한 적 '있다' 비율 격차 분석")
    with col_bm1:
        if st.button("⭐", key="bm_q1_top", help="이 섹션 북마크에 추가"):
            add_bookmark("Q① 생각 '있다' 비율 분석", 0)

    with st.expander("⚙️ Q① 세부 비교 조건 설정 (클릭하여 열기)", expanded=True):
        features = [f for f in df[(df["조사연도"] == 2025) & (df["구분"] == "생각여부")]["특성"].unique()
                    if f != "전체"]
        default_i = features.index("학업성적별") if "학업성적별" in features else 0
        feature = st.selectbox("① 비교 특성 선택 (2025년 기준)", features, index=default_i)
        
        groups = list(C.yesno(df, feature)["집단"])
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            ga = st.selectbox("비교 집단 A", groups, index=0)
        with col_g2:
            gb = st.selectbox("비교 집단 B", groups, index=len(groups) - 1)

    c_g1, col_bm_g1 = st.columns([10, 1])
    with col_bm_g1:
        if st.button("⭐", key="bm_q1_c1", help="차트 북마크"):
            add_bookmark("Q① 격차 비교 바차트", 0)
    with c_g1:
        st.plotly_chart(C.fig_q1_gap(df, excl), use_container_width=True)

    c_g2, col_bm_g2 = st.columns([10, 1])
    with col_bm_g2:
        if st.button("⭐", key="bm_q1_c2", help="차트 북마크"):
            add_bookmark("Q① 특성별 세부 바차트", 0)
    with c_g2:
        st.plotly_chart(C.fig_q1_bar(df, feature, excl), use_container_width=True)
    
    yesno_df = C.yesno(df, feature).set_index("집단")
    if ga in yesno_df.index and gb in yesno_df.index:
        va = float(yesno_df.loc[ga, "값"])
        vb = float(yesno_df.loc[gb, "값"])
        m1, m2, m3 = st.columns(3)
        m1.metric(ga, "%.1f%%" % va)
        m2.metric(gb, "%.1f%%" % vb)
        m3.metric("A − B", "%+.1f%%p" % (va - vb))

# ------------------------------------------------------------------ 탭 1: Q② 이유 순위 (범프 영역 y축 1위 상단 고정)
elif selected_tab == 1:
    col_t2, col_bm2 = st.columns([10, 1])
    with col_t2:
        st.subheader("Q② 학교급별 학업중단 생각 이유 순위 변화")
    with col_bm2:
        if st.button("⭐", key="bm_q2_top", help="이 섹션 북마크에 추가"):
            add_bookmark("Q② 학교급별 이유 순위", 1)

    kind = st.radio("그래프 형식 선택", ["범프 영역 (순위+크기)", "범프 선 (순위만)"], horizontal=True)
    etc = st.toggle("'기타' 포함", value=(kind != "범프 선 (순위만)"),
                    help="'기타'는 이유가 아닌 묶음 항목이라 순위 비교에서는 빼는 편이 해석하기 좋습니다.")
    
    c_q2_ch, c_bm_q2 = st.columns([10, 1])
    with c_bm_q2:
        if st.button("⭐", key="bm_q2_chart", help="차트 북마크"):
            add_bookmark("Q② 범프/영역 순위 차트", 1)
            
    with c_q2_ch:
        if kind.startswith("범프 영역"):
            mode = st.radio("두께 기준 선택", ["전체 학생 중 환산(%)", "'있다' 응답자 중 비율(%)"], horizontal=True)
            md = "환산" if mode.startswith("전체") else "이유내"
            fig_q2 = C.fig_q2_area(df, md, etc)
            # 순위가 높은(두꺼운 1위) 항목이 맨 위에 오도록 y축 반전
            fig_q2.update_layout(yaxis=dict(autorange="reversed"))
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

    c_q3_1, c_q3_2, c_q3_3 = st.columns([1.5, 1.5, 2])
    with c_q3_1:
        chart_type_q3 = st.selectbox("📊 시각화 유형 선택", ["덤벨 차트 (격차 비교)", "범프 영역 차트 (비중 흐름)"])
    with c_q3_2:
        sort_order = st.radio("⬇️ 정렬 기준", ["2025 생각 이유 내림차순", "2023 실제 사유 내림차순"], horizontal=True)
    with c_q3_3:
        tier = st.selectbox("대응 기준 선택", ["엄격", "기본", "완화"], index=1,
                            help="엄격=문구가 사실상 같은 4개 / 기본=계획서의 5개 / 완화=교사 관련 항목까지 6개")

    view = st.radio("표시 방식 선택", ["원자료 비율", "대응 항목 안 상대비중"], horizontal=True)

    c_q3_ch, c_bm_q3 = st.columns([10, 1])
    with col_bm_q3:
        if st.button("⭐", key="bm_q3_chart", help="차트 북마크"):
            add_bookmark("Q③ 시각화 비교 차트", 2)

    with c_q3_ch:
        if chart_type_q3.startswith("덤벨"):
            st.plotly_chart(C.fig_q3_dumbbell(df, mapping, tier, "원자료" if view == "원자료 비율" else "상대"), use_container_width=True)
        else:
            # Q③ 범프 영역 차트 전용 Plotly 시각화 로직
            mt_q3 = C.match_table(df, mapping, tier).copy()
            val_col = "2025 값(%)" if sort_order.startswith("2025") else "2023 값(%)"
            mt_q3 = mt_q3.sort_values(by=val_col, ascending=False)
            
            fig_q3_area = go.Figure()
            for idx, row in mt_q3.iterrows():
                fig_q3_area.add_trace(go.Scatter(
                    x=["2023년 (실제 사유)", "2025년 (생각 이유)"],
                    y=[row["2023 값(%)"], row["2025 값(%)"]],
                    mode="lines+markers",
                    name=row["표시이름"],
                    line=dict(width=4),
                    marker=dict(size=10),
                    fill='tonexty' if idx > 0 else 'tozeroy'
                ))
            fig_q3_area.update_layout(
                title="2023년 실제 사유 vs 2025년 생각 이유 대응 항목 비중 흐름 (Area/Bump)",
                xaxis_title="조사 연도",
                yaxis_title="비율 (%)",
                hovermode="x unified"
            )
            st.plotly_chart(fig_q3_area, use_container_width=True)

    mt = C.match_table(df, mapping, tier)
    if sort_order.startswith("2025"):
        mt = mt.sort_values(by="2025 값(%)", ascending=False)
    else:
        mt = mt.sort_values(by="2023 값(%)", ascending=False)

    st.dataframe(mt[["표시이름", "대응강도", "2023 값(%)", "2025 값(%)", "차이(%p)",
                     "2023 순위", "2025 순위", "상대비중 차(%p)", "판정근거"]], hide_index=True, use_container_width=True)
    
    st.warning("두 조사는 연도·응답 대상·선택지 구성이 달라 '줄었다/늘었다'가 아니라 "
               "대응 항목의 순위와 비중의 방향만 비교합니다.")
