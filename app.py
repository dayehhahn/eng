"""학업중단: '생각'과 '실제 사유' 비교 웹앱 (Streamlit)
실행: streamlit run app.py   (GitHub + Streamlit Community Cloud에서는 Main file path = app.py)
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

# ------------------------------------------------------------------ 사이드바
st.sidebar.header("비교 조건")
features = [f for f in df[(df["조사연도"] == 2025) & (df["구분"] == "생각여부")]["특성"].unique()
            if f != "전체"]
default_i = features.index("학업성적별") if "학업성적별" in features else 0
feature = st.sidebar.selectbox("① 특성 선택 (2025)", features, index=default_i)
groups = list(C.yesno(df, feature)["집단"])
ga = st.sidebar.selectbox("비교 집단 A", groups, index=0)
gb = st.sidebar.selectbox("비교 집단 B", groups, index=len(groups) - 1)
excl = st.sidebar.toggle("표본 주의 집단 제외·회색 표시", value=True,
                         help="계획서에서 0.0 칸·큰 값이 있어 해석을 보류하기로 한 집단(가족유형별 조손가정·기타)")
st.sidebar.caption("⚠ 표본 크기·오차는 원자료에 없어 '유의하다'는 표현을 쓰지 않습니다.")

st.title("📊 학업중단, 생각과 실제는 어디까지 겹칠까?")
st.caption("자료: 2025 '학업중단 생각 여부 및 이유'(초·중·고) / 2023 '학업 중단 사유' · 단위: % · 상관은 인과가 아님")

tab0, tab1, tab2, tab3, tab4 = st.tabs(
    ["개요·한계", "Q① '있다' 비율", "Q② 이유 순위", "Q③ 생각 vs 실제", "데이터·검증"])

# ------------------------------------------------------------------ 개요
with tab0:
    st.subheader("연구 질문")
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

# ------------------------------------------------------------------ Q①
with tab1:
    st.subheader("Q① 학업중단을 생각한 적 '있다' 비율")
    st.plotly_chart(C.fig_q1_gap(df, excl))
    st.plotly_chart(C.fig_q1_bar(df, feature, excl))
    va = float(C.yesno(df, feature).set_index("집단").loc[ga, "값"])
    vb = float(C.yesno(df, feature).set_index("집단").loc[gb, "값"])
    m1, m2, m3 = st.columns(3)
    m1.metric(ga, "%.1f%%" % va)
    m2.metric(gb, "%.1f%%" % vb)
    m3.metric("A − B", "%+.1f%%p" % (va - vb))
    st.caption("말할 수 있는 것: 집단별 비율 차이 / 말할 수 없는 것: 그 특성이 생각의 원인이라는 결론")

# ------------------------------------------------------------------ Q②
with tab2:
    st.subheader("Q② 학업중단을 생각한 이유 (1순위)")
    kind = st.radio("그래프", ["범프 영역 (순위+크기)", "범프 선 (순위만)"], horizontal=True)
    etc = st.toggle("'기타' 포함", value=(kind != "범프 선 (순위만)"),
                    help="'기타'는 이유가 아닌 묶음 항목이라 순위 비교에서는 빼는 편이 해석하기 좋습니다.")
    if kind.startswith("범프 영역"):
        mode = st.radio("두께 기준", ["전체 학생 중 환산(%)", "'있다' 응답자 중 비율(%)"], horizontal=True)
        md = "환산" if mode.startswith("전체") else "이유내"
        st.plotly_chart(C.fig_q2_area(df, md, etc))
        if md == "환산":
            st.warning("환산값 = '있다' 비율 × 이유 비율 ÷ 100. 이유 비율이 '있다'고 답한 학생만을 대상으로 한 "
                       "비율일 때만 성립하므로, 원본 통계표의 주석에서 응답 대상을 확인한 뒤 사용하세요.")
    else:
        st.plotly_chart(C.fig_q2_bump(df, etc))
        st.caption("같은 비율이면 같은 순위(동점)로 표시하고 점을 약간 벌려 그렸습니다. 선은 같은 학생의 이동이 아니라 학교급별 집단 구성의 변화입니다.")

    wide = C.level_reasons(df, include_etc=False)
    hs = wide["고등학교"].idxmax()
    st.info("고등학교에서 1순위 비율이 가장 높은 항목('기타' 제외): **%s** (%.1f%%). 2위 **%s** (%.1f%%)." % (
        hs, wide.loc[hs, "고등학교"],
        wide["고등학교"].drop(hs).idxmax(), wide["고등학교"].drop(hs).max()))
    tbl = C.level_reasons(df, include_etc=True).copy()
    tbl.columns = [c + " (%)" for c in tbl.columns]
    st.dataframe(tbl)
    st.plotly_chart(C.fig_q2_hs_type(df))

# ------------------------------------------------------------------ Q③
with tab3:
    st.subheader("Q③ 실제 중단 사유(2023) ↔ 중단 생각 이유(2025)")
    tier = st.selectbox("대응 기준", ["엄격", "기본", "완화"], index=1,
                        help="엄격=문구가 사실상 같은 4개 / 기본=계획서의 5개 / 완화=교사 관련 항목까지 6개")
    view = st.radio("표시 방식", ["원자료 비율", "대응 항목 안 상대비중"], horizontal=True)
    st.plotly_chart(C.fig_q3_dumbbell(df, mapping, tier, "원자료" if view == "원자료 비율" else "상대"))
    mt = C.match_table(df, mapping, tier)
    st.dataframe(mt[["표시이름", "대응강도", "2023 값(%)", "2025 값(%)", "차이(%p)",
                     "2023 순위", "2025 순위", "상대비중 차(%p)", "판정근거"]], hide_index=True)
    st.warning("두 조사는 연도·응답 대상·선택지 구성이 달라 '줄었다/늘었다'가 아니라 "
               "대응 항목의 순위와 비중의 방향만 비교합니다. 값이 비슷한 항목은 순위가 바뀔 수 있어 순위 차이를 크게 해석하지 않습니다.")
    st.markdown("**대응되지 않는 항목** (한쪽 조사에만 있는 선택지)")
    st.dataframe(C.unmatched(df, mapping), hide_index=True)

# ------------------------------------------------------------------ 데이터·검증
with tab4:
    st.subheader("가공 데이터 (long.csv)")
    year = st.selectbox("조사연도", sorted(df["조사연도"].unique()))
    st.dataframe(df[df["조사연도"] == year], hide_index=True)
    st.download_button("long.csv 내려받기", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="long.csv", mime="text/csv")
    st.subheader("합계 검증 (1순위·'있다/없다' 합 ≈ 100)")
    chk = df[(df["순위기준"].isin(["1순위", "-"])) & (df["값"].notna())]
    s = (chk.groupby(["조사연도", "구분", "특성", "집단"])["값"].sum().round(1).reset_index())
    s["100과의 차"] = (s["값"] - 100).round(1)
    s["판정"] = s["100과의 차"].abs().apply(lambda x: "정상(±1.0 이내)" if x <= 1.0 else "원본 확인")
    st.write("정상 %d / 전체 %d 집단" % ((s["판정"] == "정상(±1.0 이내)").sum(), len(s)))
    st.dataframe(s[s["판정"] != "정상(±1.0 이내)"], hide_index=True)
    st.caption("2023의 '1+2순위'·'1+2+3순위' 전체 합은 160.8·195.0으로 200·300이 아니어서 합계 검증에서 제외하고, "
               "'1순위 ≤ 1+2순위 ≤ 1+2+3순위' 관계로 대신 검증했습니다(위반 0건).")
    st.subheader("대응 매핑표")
    st.dataframe(mapping, hide_index=True)
