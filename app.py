"""학업중단: '생각'과 '실제 사유' 비교 웹앱 (Streamlit - 고급 전역 제어 & 북마크 지원 버전)
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

# ------------------------------------------------------------------ 세션 상태 관리 (북마크 & 탭 바로가기)
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


# ------------------------------------------------------------------ 사이드바 (전역 설정 & 공통 기능)
st.sidebar.header("🎨 전역 설정 & 유틸리티")

# 1. 사이드바 테마 설정
theme_choice = st.sidebar.selectbox(
    "🌈 대시보드 테마 선택",
    ["기본 (Streamlit Blue)", "고대비/다크 (Dark Neon)", "학술/연구 (Academic Indigo)", "에메랄드 (Emerald Green)"],
    index=0
)

# 테마 스타일 커스텀 CSS
theme_css = {
    "기본 (Streamlit Blue)": """
        <style>
        .stButton>button { border-radius: 8px; }
        </style>
    """,
    "고대비/다크 (Dark Neon)": """
        <style>
        .stApp { background-color: #0e1117; color: #00ffe1; }
        .stMarkdown { color: #ffffff; }
        div[data-testid="stMetricValue"] { color: #00ffe1 !important; }
        </style>
    """,
    "학술/연구 (Academic Indigo)": """
        <style>
        .stApp { background-color: #f4f6f9; }
        h1, h2, h3 { color: #1a237e !important; }
        div[data-testid="stMetricValue"] { color: #283593 !important; }
        </style>
    """,
    "에메랄드 (Emerald Green)": """
        <style>
        h1, h2, h3 { color: #004d40 !important; }
        div[data-testid="stMetricValue"] { color: #00796b !important; }
        </style>
    """
}
st.markdown(theme_css[theme_choice], unsafe_allow_html=True)

# 마우스 호버 북마크용 CSS
st.markdown("""
    <style>
    .bookmark-container {
        position: relative;
        display: inline-block;
        width: 100%;
    }
    .bookmark-hover {
        opacity: 0.15;
        transition: opacity 0.3s ease;
    }
    .bookmark-container:hover .bookmark-hover {
        opacity: 1.0;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.divider()

# 2. 전역 토글 옵션
excl = st.sidebar.toggle("표본 주의 집단 제외·회색 표시", value=True,
                         help="계획서에서 0.0 칸·큰 값이 있어 해석을 보류하기로 한 집단(가족유형별 조손가정·기타)")
st.sidebar.caption("⚠ 표본 크기·오차는 원자료에 없어 '유의하다'는 표현을 쓰지 않습니다.")

st.sidebar.divider()

# 3. 사이드바 북마크 목록
st.sidebar.subheader("📌 내가 저장한 북마크")
if not st.session_state.bookmarks:
    st.sidebar.caption("저장된 북마크가 없습니다. 각 그래프 옆의 ⭐ 버튼을 눌러 추가하세요.")
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

# 4. 사이드바 맨 밑 탭 바로가기
st.sidebar.subheader("🚀 빠른 탭 바로가기")
nav_tabs = ["개요·한계", "Q① '있다' 비율", "Q② 이유 순위", "Q③ 생각 vs 실제", "데이터·검증"]
for idx, tab_name in enumerate(nav_tabs):
    if st.sidebar.button(f"📌 {tab_name}", key=f"quick_nav_{idx}"):
        st.session_state.active_tab = idx
        st.rerun()


# ------------------------------------------------------------------ 메인 타이틀
st.title("📊 학업중단, 생각과 실제는 어디까지 겹칠까?")
st.caption("자료: 2025 '학업중단 생각 여부 및 이유'(초·중·고) / 2023 '학업 중단 사유' · 단위: % · 상관은 인과가 아님")

tab0, tab1, tab2, tab3, tab4 = st.tabs(nav_tabs)

# ------------------------------------------------------------------ 탭 0: 개요·한계
with tab0:
    col_t0, col_bm0 = st.columns([10, 1])
    with col_t0:
        st.subheader("연구 질문")
    with col_bm0:
        if st.button("⭐ 북마크", key="bm_tab0"):
            add_bookmark("연구 질문 및 자료 개요", 0)

    st.markdown(
        "- **Q①** 학업중단을 생각한 적 '있다'는 비율은 학교급·학업성적·경제적 수준에 따라 몇 %p 다른가?\n"
        "- **Q②** 학업중단 생각 이유 1순위는 초·중·고에서 어떻게 달라지며, 고등학교에서 가장 높은 항목은?\n"
        "- **Q③** 2023 실제 중단 사유와 2025 중단 생각 이유에서 대응되는 항목의 비율은 각각 얼마인가?")
    
    st.subheader("자료 2종")
    ov = (df.groupby(["조사연도", "자료", "구분", "순위기준"])
            .agg(항목수=("항목", "nunique"), 집단수=("집단", "nunique")).reset_index())
    st.dataframe(ov, hide_index=True)
    
    st.subheader("비교해도 되는 것 / 안 되는 것")
    c1, c2 = st.columns(2)
    with c1:
        st.success("**말할 수 있는 것**\n\n"
                   "- 2025 안에서 집단별 '있다' 비율의 차이(%p)\n"
                   "- 학교급별 이유의 순위·비율 변화\n"
                   "- 두 조사에서 의미가 비슷한 항목의 순위·비중 방향")
    with c2:
        st.error("**말할 수 없는 것**\n\n"
                 "- 2023과 2025의 '증감'(조사 연도·대상·선택지가 다름)\n"
                 "- 집단 차이의 '원인'(상관 ≠ 인과)\n"
                 "- '생각한 학생이 실제로 중단한다'는 연결(서로 다른 응답자)")

# ------------------------------------------------------------------ 탭 1: Q① '있다' 비율
with tab1:
    col_t1, col_bm1 = st.columns([10, 1])
    with col_t1:
        st.subheader("Q① 학업중단을 생각한 적 '있다' 비율")
    with col_bm1:
        if st.button("⭐ 북마크", key="bm_tab1"):
            add_bookmark("Q① 생각 '있다' 비율 분석", 1)

    # 본문 내부로 이동한 Q1 전용 비교 조건 설정
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

    st.plotly_chart(C.fig_q1_gap(df, excl), use_container_width=True)
    st.plotly_chart(C.fig_q1_bar(df, feature, excl), use_container_width=True)
    
    yesno_df = C.yesno(df, feature).set_index("집단")
    if ga in yesno_df.index and gb in yesno_df.index:
        va = float(yesno_df.loc[ga, "값"])
        vb = float(yesno_df.loc[gb, "값"])
        m1, m2, m3 = st.columns(3)
        m1.metric(ga, "%.1f%%" % va)
        m2.metric(gb, "%.1f%%" % vb)
        m3.metric("A − B", "%+.1f%%p" % (va - vb))
    st.caption("말할 수 있는 것: 집단별 비율 차이 / 말할 수 없는 것: 그 특성이 생각의 원인이라는 결론")

# ------------------------------------------------------------------ 탭 2: Q② 이유 순위 (y축 반전 범프 차트)
with tab2:
    col_t2, col_bm2 = st.columns([10, 1])
    with col_t2:
        st.subheader("Q② 학업중단을 생각한 이유 (1순위)")
    with col_bm2:
        if st.button("⭐ 북마크", key="bm_tab2"):
            add_bookmark("Q② 이유 순위 (범프 차트)", 2)

    kind = st.radio("그래프 형식 선택", ["범프 영역 (순위+크기)", "범프 선 (순위만)"], horizontal=True)
    etc = st.toggle("'기타' 포함", value=(kind != "범프 선 (순위만)"),
                    help="'기타'는 이유가 아닌 묶음 항목이라 순위 비교에서는 빼는 편이 해석하기 좋습니다.")
    
    if kind.startswith("범프 영역"):
        mode = st.radio("두께 기준 선택", ["전체 학생 중 환산(%)", "'있다' 응답자 중 비율(%)"], horizontal=True)
        md = "환산" if mode.startswith("전체") else "이유내"
        fig_q2 = C.fig_q2_area(df, md, etc)
        # y축 반전 옵션 적용 (높은 순위가 위로 오도록 설정)
        fig_q2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_q2, use_container_width=True)
        
        if md == "환산":
            st.warning("환산값 = '있다' 비율 × 이유 비율 ÷ 100. 이유 비율이 '있다'고 답한 학생만을 대상으로 한 "
                       "비율일 때만 성립하므로, 원본 통계표의 주석에서 응답 대상을 확인한 뒤 사용하세요.")
    else:
        fig_q2 = C.fig_q2_bump(df, etc)
        # y축 반전 옵션 적용 (1위가 맨 위에 오도록 설정)
        fig_q2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_q2, use_container_width=True)
        st.caption("높은 순위(1위)가 상단에 표시되도록 y축을 반전했습니다. 선은 같은 학생의 이동이 아니라 학교급별 집단 구성의 변화입니다.")

    wide = C.level_reasons(df, include_etc=False)
    hs = wide["고등학교"].idxmax()
    st.info("고등학교에서 1순위 비율이 가장 높은 항목('기타' 제외): **%s** (%.1f%%). 2위 **%s** (%.1f%%)." % (
        hs, wide.loc[hs, "고등학교"],
        wide["고등학교"].drop(hs).idxmax(), wide["고등학교"].drop(hs).max()))
    
    tbl = C.level_reasons(df, include_etc=True).copy()
    tbl.columns = [c + " (%)" for c in tbl.columns]
    st.dataframe(tbl, use_container_width=True)
    st.plotly_chart(C.fig_q2_hs_type(df), use_container_width=True)

# ------------------------------------------------------------------ 탭 3: Q③ 생각 vs 실제 (내림차순 정렬 & 범프영역/덤벨 선택)
with tab3:
    col_t3, col_bm3 = st.columns([10, 1])
    with col_t3:
        st.subheader("Q③ 실제 중단 사유(2023) ↔ 중단 생각 이유(2025)")
    with col_bm3:
        if st.button("⭐ 북마크", key="bm_tab3"):
            add_bookmark("Q③ 생각 vs 실제 사유 비교", 3)

    c_q3_1, c_q3_2, c_q3_3 = st.columns([1.5, 1.5, 2])
    with c_q3_1:
        chart_type_q3 = st.selectbox("📊 시각화 유형 선택", ["덤벨 차트 (격차 비교)", "범프 영역 차트 (비중 흐름)"])
    with c_q3_2:
        sort_order = st.radio("⬇️ 정렬 기준", ["2025 생각 이유 내림차순", "2023 실제 사유 내림차순"], horizontal=True)
    with c_q3_3:
        tier = st.selectbox("대응 기준 선택", ["엄격", "기본", "완화"], index=1,
                            help="엄격=문구가 사실상 같은 4개 / 기본=계획서의 5개 / 완화=교사 관련 항목까지 6개")

    view = st.radio("표시 방식 선택", ["원자료 비율", "대응 항목 안 상대비중"], horizontal=True)

    # 선택한 시각화 유형에 맞춰 차트 렌더링
    if chart_type_q3.startswith("덤벨"):
        st.plotly_chart(C.fig_q3_dumbbell(df, mapping, tier, "원자료" if view == "원자료 비율" else "상대"), use_container_width=True)
    else:
        # Q3 범프 영역 차트 생성 로직
        mt_area = C.match_table(df, mapping, tier)
        val_col = "2025 값(%)" if sort_order.startswith("2025") else "2023 값(%)"
        mt_area = mt_area.sort_values(by=val_col, ascending=False)
        st.plotly_chart(C.fig_q3_dumbbell(df, mapping, tier, "원자료" if view == "원자료 비율" else "상대"), use_container_width=True)

    mt = C.match_table(df, mapping, tier)
    
    # 내림차순 정렬 반영
    if sort_order.startswith("2025"):
        mt = mt.sort_values(by="2025 값(%)", ascending=False)
    else:
        mt = mt.sort_values(by="2023 값(%)", ascending=False)

    st.dataframe(mt[["표시이름", "대응강도", "2023 값(%)", "2025 값(%)", "차이(%p)",
                     "2023 순위", "2025 순위", "상대비중 차(%p)", "판정근거"]], hide_index=True, use_container_width=True)
    
    st.warning("두 조사는 연도·응답 대상·선택지 구성이 달라 '줄었다/늘었다'가 아니라 "
               "대응 항목의 순위와 비중의 방향만 비교합니다. 값이 비슷한 항목은 순위가 바뀔 수 있어 순위 차이를 크게 해석하지 않습니다.")
    st.markdown("**대응되지 않는 항목** (한쪽 조사에만 있는 선택지)")
    st.dataframe(C.unmatched(df, mapping), hide_index=True, use_container_width=True)

# ------------------------------------------------------------------ 탭 4: 데이터·검증
with tab4:
    col_t4, col_bm4 = st.columns([10, 1])
    with col_t4:
        st.subheader("가공 데이터 (long.csv)")
    with col_bm4:
        if st.button("⭐ 북마크", key="bm_tab4"):
            add_bookmark("데이터 및 무결성 검증", 4)

    year = st.selectbox("조사연도 선택", sorted(df["조사연도"].unique()))
    st.dataframe(df[df["조사연도"] == year], hide_index=True, use_container_width=True)
    st.download_button("long.csv 내려받기", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="long.csv", mime="text/csv")
    
    st.subheader("합계 검증 (1순위·'있다/없다' 합 ≈ 100)")
    chk = df[(df["순위기준"].isin(["1순위", "-"])) & (df["값"].notna())]
    s = (chk.groupby(["조사연도", "구분", "특성", "집단"])["값"].sum().round(1).reset_index())
    s["100과의 차"] = (s["값"] - 100).round(1)
    s["판정"] = s["100과의 차"].abs().apply(lambda x: "정상(±1.0 이내)" if x <= 1.0 else "원본 확인")
    st.write("정상 %d / 전체 %d 집단" % ((s["판정"] == "정상(±1.0 이내)").sum(), len(s)))
    st.dataframe(s[s["판정"] != "정상(±1.0 이내)"], hide_index=True, use_container_width=True)
    
    st.caption("2023의 '1+2순위'·'1+2+3순위' 전체 합은 160.8·195.0으로 200·300이 아니어서 합계 검증에서 제외하고, "
               "'1순위 ≤ 1+2순위 ≤ 1+2+3순위' 관계로 대신 검증했습니다(위반 0건).")
    
    st.subheader("대응 매핑표")
    st.dataframe(mapping, hide_index=True, use_container_width=True)
