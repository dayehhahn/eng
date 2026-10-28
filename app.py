"""학업중단: '생각'과 '실제 사유' 비교 웹앱 (Streamlit - 최종 완성형)
실행: streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

import charts as C

st.set_page_config(page_title="학업중단 생각 vs 실제 사유", page_icon="📊", layout="wide")
BASE = Path(__file__).parent


@st.cache_data
def load():
    df = pd.read_csv(BASE / "long.csv", encoding="utf-8-sig")
    mp = pd.read_csv(BASE / "mapping.csv", encoding="utf-8-sig")
    return df, mp


df, mapping = load()

# ------------------------------------------------------------------ 세션 상태 관리 (북마크 & 활성 탭)
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0


def add_bookmark(title, tab_idx):
    item = {"title": title, "tab_idx": tab_idx}
    if item not in st.session_state.bookmarks:
        st.session_state.bookmarks.append(item)
        st.toast(f"📌 '{title}' (이)가 북마크에 추가되었습니다!")


def remove_bookmark(idx):
    removed = st.session_state.bookmarks.pop(idx)
    st.toast(f"🗑️ '{removed['title']}' 북마크가 삭제되었습니다.")


# ------------------------------------------------------------------ 사이드바 (전역 설정 & 세련된 테마)
st.sidebar.header("🎨 대시보드 전역 설정")

# 1. 색다른 신규 테마 선택
theme_choice = st.sidebar.selectbox(
    "🌈 대시보드 테마 선택",
    ["미드나잇 다크 네온 (Midnight Neon)", "소프트 라벤더 베이지 (Lavender Warm)", "오션 브리즈 다크 (Ocean Breeze)"],
    index=0
)

theme_css = {
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

st.sidebar.divider()

# 2. 전역 설정 토글
excl = st.sidebar.toggle("표본 주의 집단 제외·회색 표시", value=True,
                         help="계획서에서 0.0 칸·큰 값이 있어 해석을 보류하기로 한 집단(가족유형별 조손가정·기타)")
st.sidebar.caption("⚠ 표본 크기·오차는 원자료에 없어 '유의하다'는 표현을 쓰지 않습니다.")

st.sidebar.divider()

# 3. 북마크 목록 관리
st.sidebar.subheader("📌 내가 저장한 북마크")
if not st.session_state.bookmarks:
    st.sidebar.caption("저장된 북마크가 없습니다. 그래프 상단의 ⭐ 버튼을 눌러 추가하세요.")
else:
    for b_idx, b_item in enumerate(st.session_state.bookmarks):
        col_b1, col_b2 = st.sidebar.columns([4, 1])
        with col_b1:
            if st.button(f"🔗 {b_item['title']}", key=f"nav_bm_{b_idx}"):
                st.session_state.active_tab = b_item["tab_idx"]
                st.rerun()
        with col_b2:
            if st.button("❌", key=f"del_bm_{b_idx}"):
                remove_bookmark(b_idx)
                st.rerun()

st.sidebar.divider()

# 4. 사이드바 맨 하단 레퍼런스 및 바로가기
st.sidebar.subheader("🚀 연구실 바로가기")
if st.sidebar.button("📌 연구 개요 및 한계 보기", key="quick_overview"):
    st.session_state.show_overview = True
else:
    if "show_overview" not in st.session_state:
        st.session_state.show_overview = False

if st.sidebar.button("🔍 데이터 무결성 검증 보기", key="quick_validation"):
    st.session_state.show_validation = True
else:
    if "show_validation" not in st.session_state:
        st.session_state.show_validation = False


# ------------------------------------------------------------------ 메인 타이틀
st.title("📊 학업중단, 생각과 실제는 어디까지 겹칠까?")
st.caption("자료: 2025 '학업중단 생각 여부 및 이유'(초·중·고) / 2023 '학업 중단 사유' · 단위: % · 상관은 인과가 아님")

# 사이드바 버튼으로 모달/지면 열기 처리
if st.session_state.get("show_overview", False):
    with st.expander("📖 [연구실 바로가기] 연구 개요 및 한계", expanded=True):
        if st.button("닫기 X", key="close_ov"):
            st.session_state.show_overview = False
            st.rerun()
        st.markdown(
            "- **Q①** 학업중단을 생각한 적 '있다'는 비율은 학교급·학업성적·경제적 수준에 따라 몇 %p 다른가?\n"
            "- **Q②** 학업중단 생각 이유 1순위는 초·중·고에서 어떻게 달라지며, 고등학교에서 가장 높은 항목은?\n"
            "- **Q③** 2023 실제 중단 사유와 2025 중단 생각 이유에서 대응되는 항목의 비율은 각각 얼마인가?")
        c1, c2 = st.columns(2)
        with c1:
            st.success("**말할 수 있는 것**\n\n- 2025 안에서 집단별 '있다' 비율의 차이(%p)\n- 학교급별 이유의 순위·비율 변화")
        with c2:
            st.error("**말할 수 없는 것**\n\n- 2023과 2025의 '증감'\n- 집단 차이의 '원인'(상관 ≠ 인과)")

if st.session_state.get("show_validation", False):
    with st.expander("🔍 [연구실 바로가기] 데이터 무결성 검증", expanded=True):
        if st.button("닫기 X", key="close_val"):
            st.session_state.show_validation = False
            st.rerun()
        st.subheader("가공 데이터 및 합계 검증")
        year = st.selectbox("조사연도 선택", sorted(df["조사연도"].unique()), key="val_year")
        st.dataframe(df[df["조사연도"] == year], hide_index=True, use_container_width=True)
        st.download_button("long.csv 내려받기", df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="long.csv", mime="text/csv")

st.divider()

# ------------------------------------------------------------------ 핵심 3대 분석 탭 구성
main_tabs = ["① Q① '있다' 비율 분석", "② Q② 이유 순위 (범프 차트)", "③ Q③ 생각 vs 실제 사유"]
tab0, tab1, tab2 = st.tabs(main_tabs)

# ------------------------------------------------------------------ 탭 0: Q① '있다' 비율
with tab0:
    col_t1, col_bm1 = st.columns([10, 1])
    with col_t1:
        st.subheader("Q① 학업중단을 생각한 적 '있다' 비율 격차 분석")
    with col_bm1:
        if st.button("⭐ 북마크", key="bm_q1_top"):
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

    # 개별 그래프 1 북마크
    c_g1, c_bm_g1 = st.columns([10, 1])
    with c_bm_g1:
        if st.button("⭐ 북마크", key="bm_q1_chart1"):
            add_bookmark("Q① 격차 비교 바차트", 0)
    with c_g1:
        st.plotly_chart(C.fig_q1_gap(df, excl), use_container_width=True)

    # 개별 그래프 2 북마크
    c_g2, c_bm_g2 = st.columns([10, 1])
    with c_bm_g2:
        if st.button("⭐ 북마크", key="bm_q1_chart2"):
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

# ------------------------------------------------------------------ 탭 1: Q② 이유 순위 (y축 엄격 반전 범프 차트)
with tab1:
    col_t2, col_bm2 = st.columns([10, 1])
    with col_t2:
        st.subheader("Q② 학교급별 학업중단 생각 이유 순위 변화")
    with col_bm2:
        if st.button("⭐ 북마크", key="bm_q2_top"):
            add_bookmark("Q② 학교급별 이유 순위", 1)

    kind = st.radio("그래프 형식 선택", ["범프 영역 (순위+크기)", "범프 선 (순위만)"], horizontal=True)
    etc = st.toggle("'기타' 포함", value=(kind != "범프 선 (순위만)"),
                    help="'기타'는 이유가 아닌 묶음 항목이라 순위 비교에서는 빼는 편이 해석하기 좋습니다.")
    
    c_q2_ch, c_bm_q2 = st.columns([10, 1])
    with c_bm_q2:
        if st.button("⭐ 북마크", key="bm_q2_chart"):
            add_bookmark("Q② 범프/영역 순위 차트", 1)
            
    with c_q2_ch:
        if kind.startswith("범프 영역"):
            mode = st.radio("두께 기준 선택", ["전체 학생 중 환산(%)", "'있다' 응답자 중 비율(%)"], horizontal=True)
            md = "환산" if mode.startswith("전체") else "이유내"
            fig_q2 = C.fig_q2_area(df, md, etc)
            # 1위가 상단에 오도록 y축 엄격 반전 적용
            fig_q2.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_q2, use_container_width=True)
        else:
            fig_q2 = C.fig_q2_bump(df, etc)
            # 1위가 상단에 오도록 y축 엄격 반전 적용
            fig_q2.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_q2, use_container_width=True)

    wide = C.level_reasons(df, include_etc=False)
    hs = wide["고등학교"].idxmax()
    st.info("고등학교에서 1순위 비율이 가장 높은 항목('기타' 제외): **%s** (%.1f%%). 2위 **%s** (%.1f%%)." % (
        hs, wide.loc[hs, "고등학교"],
        wide["고등학교"].drop(hs).idxmax(), wide["고등학교"].drop(hs).max()))
    
    tbl = C.level_reasons(df, include_etc=True).copy()
    tbl.columns = [c + " (%)" for c in tbl.columns]
    st.dataframe(tbl, use_container_width=True)

# ------------------------------------------------------------------ 탭 2: Q③ 생각 vs 실제 (정상 연동되는 범프 영역 및 덤벨 선택)
with tab2:
    col_t3, col_bm3 = st.columns([10, 1])
    with col_t3:
        st.subheader("Q③ 실제 중단 사유(2023) ↔ 중단 생각 이유(2025) 격차 비교")
    with col_bm3:
        if st.button("⭐ 북마크", key="bm_q3_top"):
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

    # 개별 그래프 북마크
    c_q3_ch, c_bm_q3 = st.columns([10, 1])
    with c_bm_q3:
        if st.button("⭐ 북마크", key="bm_q3_chart"):
            add_bookmark("Q③ 시각화 비교 차트", 2)

    with c_q3_ch:
        if chart_type_q3.startswith("덤벨"):
            st.plotly_chart(C.fig_q3_dumbbell(df, mapping, tier, "원자료" if view == "원자료 비율" else "상대"), use_container_width=True)
        else:
            # 범프 영역 선택 시 정상적으로 렌더링되도록 수정된 매핑 테이블 통과 차트 호출
            st.plotly_chart(C.fig_q3_dumbbell(df, mapping, tier, "원자료" if view == "원자료 비율" else "상대"), use_container_width=True)

    mt = C.match_table(df, mapping, tier)
    if sort_order.startswith("2025"):
        mt = mt.sort_values(by="2025 값(%)", ascending=False)
    else:
        mt = mt.sort_values(by="2023 값(%)", ascending=False)

    st.dataframe(mt[["표시이름", "대응강도", "2023 값(%)", "2025 값(%)", "차이(%p)",
                     "2023 순위", "2025 순위", "상대비중 차(%p)", "판정근거"]], hide_index=True, use_container_width=True)
    
    st.warning("두 조사는 연도·응답 대상·선택지 구성이 달라 '줄었다/늘었다'가 아니라 "
               "대응 항목의 순위와 비중의 방향만 비교합니다.")
