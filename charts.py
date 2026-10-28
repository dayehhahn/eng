"""charts.py - 데이터 계산 + 그래프(Plotly) 함수 모음.
app.py(웹앱)와 Colab 미리보기가 같이 쓴다.
long.csv 열: 조사연도, 자료, 특성, 집단, 구분, 순위기준, 분류, 항목, 값, 결측
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

LEVELS = ["초등학교", "중학교", "고등학교"]

# 표본 주의 집단: 계획서에서 '0.0 칸과 큰 값이 있어 해석 보류'로 정한 집단
CAUTION = {("가족유형별", "조손가정"), ("가족유형별", "기타")}

C23 = "#E15759"   # 2023 (실제 사유)
C25 = "#4E79A7"   # 2025 (생각 이유)
GRAY = "#B8B8B8"

SHORT = {
    "괴롭힘을 당해서": "괴롭힘",
    "성적이 좋지 않아서": "성적",
    "선생님이 불공평한 대우를 해서": "교사의 불공평",
    "가정이 경제적으로 어려워서": "가정 경제",
    "공부가 하기 싫어서": "공부 하기 싫음",
    "학교 규율이 엄격하고 자유롭지 않아서": "엄격한 규율",
    "내가 배우고 싶은 내용이 없어서": "배울 내용 없음",
    "귀찮고 아무것도 하기 싫어서": "귀찮고 하기 싫음",
    "기타": "기타",
}
PALETTE = ["#E15759", "#F28E2B", "#EDC948", "#76B7B2", "#4E79A7",
           "#59A14F", "#B07AA1", "#9C755F"]
_COLOR = {}


def short(name):
    return SHORT.get(name, name)


def color_of(name):
    if name == "기타":
        return GRAY
    if name not in _COLOR:
        _COLOR[name] = PALETTE[len(_COLOR) % len(PALETTE)]
    return _COLOR[name]


# ---------------------------------------------------------------- 데이터 꺼내기
def yesno(df, feature=None):
    """2025 '학업중단 생각 있다' 비율"""
    d = df[(df["조사연도"] == 2025) & (df["구분"] == "생각여부") & (df["항목"] == "있다")]
    if feature is not None:
        d = d[d["특성"] == feature]
    return d[["특성", "집단", "값"]].reset_index(drop=True)


def is_caution(feature, group, on=True):
    return on and ((feature, group) in CAUTION)


def gap_table(df, exclude_caution=True):
    """특성별로 '있다' 비율의 최고 집단 - 최저 집단 격차(%p)"""
    rows = []
    d = yesno(df)
    for f, g in d.groupby("특성", sort=False):
        if f == "전체":
            continue
        if exclude_caution:
            g = g[[not is_caution(f, x) for x in g["집단"]]]
        hi = g.loc[g["값"].idxmax()]
        lo = g.loc[g["값"].idxmin()]
        rows.append({"특성": f, "최고 집단": hi["집단"], "최고(%)": hi["값"],
                     "최저 집단": lo["집단"], "최저(%)": lo["값"],
                     "격차(%p)": round(float(hi["값"] - lo["값"]), 1)})
    out = pd.DataFrame(rows)
    return out.sort_values("격차(%p)", ascending=False).reset_index(drop=True)


def level_reasons(df, include_etc=True):
    """학교급별 이유(1순위) 표: 행=이유, 열=초·중·고"""
    d = df[(df["조사연도"] == 2025) & (df["구분"] == "생각이유") & (df["특성"] == "학교급별")]
    wide = d.pivot(index="항목", columns="집단", values="값")
    wide = wide.reindex(index=list(dict.fromkeys(d["항목"])), columns=LEVELS)
    if not include_etc:
        wide = wide.drop(index="기타", errors="ignore")
    return wide


def level_yes(df):
    d = yesno(df, "학교급별").set_index("집단")["값"]
    return d.reindex(LEVELS)


def hs_type_reasons(df):
    d = df[(df["조사연도"] == 2025) & (df["구분"] == "생각이유") & (df["특성"] == "고교유형별")]
    wide = d.pivot(index="항목", columns="집단", values="값")
    return wide.reindex(index=list(dict.fromkeys(d["항목"])))


def match_table(df, mapping, tier="기본"):
    """2023 실제 사유(1순위, 전체) ↔ 2025 생각 이유(1순위, 전체) 대응표"""
    a = df[(df["조사연도"] == 2023) & (df["구분"] == "사유") & (df["순위기준"] == "1순위")
           & (df["특성"] == "전체")].set_index("항목")["값"]
    b = df[(df["조사연도"] == 2025) & (df["구분"] == "생각이유") & (df["특성"] == "전체")
           ].set_index("항목")["값"]
    order = {"엄격": 1, "기본": 2, "완화": 3}
    m = mapping[mapping["대응강도"] != "없음"].copy()
    m = m[m["최소단계"].map(order) <= order[tier]]
    m["2023 값(%)"] = m["항목_2023"].map(a)
    m["2025 값(%)"] = m["항목_2025"].map(b)
    m["차이(%p)"] = (m["2025 값(%)"] - m["2023 값(%)"]).round(1)
    m["2023 상대비중(%)"] = (m["2023 값(%)"] / m["2023 값(%)"].sum() * 100).round(1)
    m["2025 상대비중(%)"] = (m["2025 값(%)"] / m["2025 값(%)"].sum() * 100).round(1)
    m["상대비중 차(%p)"] = (m["2025 상대비중(%)"] - m["2023 상대비중(%)"]).round(1)
    m["2023 순위"] = m["2023 값(%)"].rank(ascending=False, method="min").astype(int)
    m["2025 순위"] = m["2025 값(%)"].rank(ascending=False, method="min").astype(int)
    return m.reset_index(drop=True)


def unmatched(df, mapping):
    """대응되지 않는 항목(한쪽 조사에만 있는 선택지)과 그 값"""
    a = df[(df["조사연도"] == 2023) & (df["구분"] == "사유") & (df["순위기준"] == "1순위")
           & (df["특성"] == "전체")].set_index("항목")["값"]
    b = df[(df["조사연도"] == 2025) & (df["구분"] == "생각이유") & (df["특성"] == "전체")
           ].set_index("항목")["값"]
    u = mapping[mapping["대응강도"] == "없음"]
    rows = []
    for _, r in u.iterrows():
        if isinstance(r["항목_2023"], str) and r["항목_2023"]:
            rows.append({"조사": "2023 실제 사유", "항목": r["항목_2023"],
                         "1순위(%)": a.get(r["항목_2023"], np.nan), "비고": r["판정근거"]})
        if isinstance(r["항목_2025"], str) and r["항목_2025"]:
            rows.append({"조사": "2025 생각 이유", "항목": r["항목_2025"],
                         "1순위(%)": b.get(r["항목_2025"], np.nan), "비고": r["판정근거"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 그래프
def _base_layout(fig, title, height=460, **kw):
    layout = dict(title=dict(text=title, x=0.01), height=height, plot_bgcolor="white",
                  margin=dict(l=20, r=20, t=70, b=40), font=dict(size=13))
    layout.update(kw)          # 그래프마다 다른 설정(여백 등)은 덮어쓴다
    fig.update_layout(**layout)
    return fig


def fig_q1_bar(df, feature, exclude_caution=True):
    """Q① 막대 그래프: 선택한 특성의 집단별 '있다' 비율"""
    d = yesno(df, feature)
    total = float(yesno(df, "전체")["값"].iloc[0])
    ok = d[[not is_caution(feature, g, exclude_caution) for g in d["집단"]]]
    hi = ok.loc[ok["값"].idxmax()]
    lo = ok.loc[ok["값"].idxmin()]
    gap = float(hi["값"] - lo["값"])
    colors, labels = [], []
    for g, v in zip(d["집단"], d["값"]):
        warn = is_caution(feature, g, exclude_caution)
        colors.append(C25 if not warn and v == hi["값"] else GRAY)
        labels.append("%.1f%%%s" % (v, " ⚠" if warn else ""))
    fig = go.Figure(go.Bar(x=d["집단"], y=d["값"], marker_color=colors, text=labels,
                           textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
    fig.add_hline(y=total, line_dash="dot", line_color="#C7CBD1", line_width=1,
                  layer="below", annotation_text="전체 %.1f%%" % total,
                  annotation_position="top left", annotation_font=dict(size=11, color="#A1A7B0"))
    fig.update_yaxes(range=[0, max(float(d["값"].max()) * 1.25, total * 1.25)],
                     title="'학업중단을 생각한 적 있다' 응답 비율(%)", showgrid=False)
    note = "최고 %s − 최저 %s = %.1f%%p" % (hi["집단"], lo["집단"], gap)
    fig.add_annotation(x=0, y=-0.25, xref="paper", yref="paper", text=note,
                       showarrow=False, xanchor="left", yanchor="top",
                       font=dict(size=12, color="#737b8c"))
    return _base_layout(fig, "<b>%s</b>" % feature, height=450,
                        margin=dict(l=20, r=20, t=70, b=90),
                        title_font=dict(size=21))


def fig_q1_gap(df, exclude_caution=True):
    """특성별 격차 한눈에 보기(가로 막대)"""
    g = gap_table(df, exclude_caution)
    text = ["%.1f%%p (%s %.1f%% − %s %.1f%%)" % (r["격차(%p)"], r["최고 집단"], r["최고(%)"],
                                              r["최저 집단"], r["최저(%)"]) for _, r in g.iterrows()]
    fig = go.Figure(go.Bar(x=g["격차(%p)"], y=g["특성"], orientation="h", text=text,
                           textposition="outside", cliponaxis=False, marker_color=C25,
                           hovertemplate="%{y}: %{x:.1f}%p<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(range=[0, float(g["격차(%p)"].max()) * 2.1], title="최고 집단 − 최저 집단 (%p)",
                     gridcolor="#EEE")
    return _base_layout(fig, "어느 특성에서 집단 간 차이가 가장 큰가", height=420,
                        margin=dict(l=20, r=20, t=70, b=40))


def _spread_ties(ranks):
    """같은 순위(동점)가 겹쳐 보이지 않도록 y위치를 조금씩 벌린다"""
    pos = {}
    groups = {}
    for item, r in ranks.items():
        groups.setdefault(r, []).append(item)
    for r, items in groups.items():
        n = len(items)
        for i, item in enumerate(items):
            pos[item] = r + (i - (n - 1) / 2.0) * 0.45
    return pos


def fig_q2_bump(df, include_etc=False):
    """Q② 범프 차트: 초→중→고 순위 변화(점 안 숫자=비율)"""
    wide = level_reasons(df, include_etc)
    rk = wide.rank(ascending=False, method="min")
    n = len(wide.index)
    fig = go.Figure()
    ypos = {lv: _spread_ties(rk[lv].to_dict()) for lv in LEVELS}
    for item in wide.index:
        xs = LEVELS
        ys = [ypos[lv][item] for lv in LEVELS]
        vals = [float(wide.loc[item, lv]) for lv in LEVELS]
        col = color_of(item)
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers+text", name=short(item),
            line=dict(width=5, color=col), marker=dict(size=34, color=col),
            text=["%.1f" % v for v in vals], textposition="middle center",
            textfont=dict(color="white", size=11),
            hovertemplate=short(item) + " | %{x}: %{text}%<extra></extra>"))
        fig.add_annotation(x=LEVELS[0], y=ys[0], text=short(item), showarrow=False,
                           xanchor="right", xshift=-26, font=dict(size=12, color=col))
        fig.add_annotation(x=LEVELS[-1], y=ys[-1], text=short(item), showarrow=False,
                           xanchor="left", xshift=26, font=dict(size=12, color=col))
    fig.update_yaxes(range=[n + 0.6, 0.4], dtick=1, title="순위 (1위가 위)",
                     showgrid=False, zeroline=False)
    fig.update_xaxes(showgrid=False, type="category")
    return _base_layout(fig, "학교급별 '학업중단을 생각한 이유' 순위 변화 (점 안 숫자 = 비율 %)",
                        height=560, showlegend=False, margin=dict(l=130, r=130, t=70, b=40))


def _smooth(n=25):
    t = np.linspace(0, 1, n)
    return t * t * (3 - 2 * t)


def fig_q2_area(df, mode="환산", include_etc=True):
    """Q② 범프 영역 그래프: 순위(위쪽일수록 높음) + 크기(띠 두께) 동시 표시
    mode='환산'  : 띠 두께 = '있다' 비율 × 이유 비율 (전체 학생 중 %)  → 전체 높이 = '있다' 비율
    mode='이유내': 띠 두께 = 이유 비율(%) (그 학교급에서 '있다'고 답한 학생 중)"""
    wide = level_reasons(df, include_etc)
    yes = level_yes(df)
    vals = wide.mul(yes, axis=1) / 100.0 if mode == "환산" else wide.copy()
    if mode == "환산":
        ytitle = "전체 학생 중 비율(%)"
        title = "학교급별 학업중단 생각 이유: 순위와 전체 학생 중 비율"
    else:
        ytitle = "'있다' 응답자 중 비율(%)"
        title = "학교급별 학업중단 생각 이유: 순위와 응답자 중 비율"
    return _ranked_area(vals, title, ytitle, LEVELS[0])


def _ranked_area(vals, title, ytitle, palette_column):
    levels = list(vals.columns)
    k = len(levels)
    lower, upper = {}, {}
    for j, lv in enumerate(levels):
        col = vals[lv]
        order = col.sort_values(ascending=False, kind="stable").index  # 위→아래 (큰 값부터)
        base = 0.0
        for item in order:
            lower[(item, j)] = base
            base += float(col[item])
            upper[(item, j)] = base
    # 각 학교급의 너비를 확보하고 학교급 사이에서만 순위를 연결한다.
    palette = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2",
               "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7"]
    rank_order = vals[palette_column].sort_values(ascending=False, kind="stable").index
    colors = dict(zip(rank_order, palette + ["#9C755F"]))
    fig = go.Figure()
    ymax = max(upper.values())
    half_width = 0.34
    transition = _smooth(30)
    for item in vals.index:
        X, U, L = [], [], []
        for j in range(k):
            X.extend([j - half_width, j + half_width])
            U.extend([upper[(item, j)]] * 2)
            L.extend([lower[(item, j)]] * 2)
            if j < k - 1:
                X.extend(j + half_width + (1 - 2 * half_width) * np.linspace(0, 1, len(transition)))
                U.extend(upper[(item, j)] + (upper[(item, j + 1)] - upper[(item, j)]) * transition)
                L.extend(lower[(item, j)] + (lower[(item, j + 1)] - lower[(item, j)]) * transition)
        hover = short(item) + "<br>" + "<br>".join(
            "%s: %.1f%%" % (lv, vals.loc[item, lv]) for lv in levels)
        fig.add_trace(go.Scatter(
            x=X + X[::-1], y=U + L[::-1], fill="toself", mode="lines", hoveron="fills",
            line=dict(color="white", width=1), fillcolor=colors[item], opacity=0.9,
            name=short(item), text=hover, hoverinfo="text"))
        for j, lv in enumerate(levels):
            lo, up = lower[(item, j)], upper[(item, j)]
            thickness = up - lo
            if thickness >= ymax * 0.055:
                text_color = "white" if colors[item] in ("#4E79A7", "#E15759", "#59A14F", "#B07AA1", "#9C755F") else "#202020"
                secondary_color = "#e4e4e4" if text_color == "white" else "#555555"
                label = "<b>%s</b><br><span style='font-size:11px;color:%s'>%.1f%%</span>" % (
                    short(item), secondary_color, vals.loc[item, lv])
                fig.add_annotation(x=j, y=(lo + up) / 2, text=label,
                                   showarrow=False,
                                   font=dict(color=text_color, size=14))
    fig.update_xaxes(tickvals=list(range(k)), ticktext=levels, range=[-0.42, k - 1 + 0.42],
                     side="top", showgrid=False, zeroline=False, tickfont=dict(size=15))
    fig.update_yaxes(title=ytitle, gridcolor="#EEE", autorange="reversed", rangemode="tozero")
    return _base_layout(fig, title, height=720, showlegend=True,
                        legend=dict(orientation="h", yanchor="top", y=-0.08, x=0),
                        margin=dict(l=65, r=25, t=100, b=100))


def fig_q2_hs_type(df):
    """고등학교 유형별(일반계고·특성화계고) 이유 비교: 막대 그래프"""
    w = hs_type_reasons(df)
    w = w.sort_values(w.columns[0], ascending=True)
    fig = go.Figure()
    for col, c in zip(w.columns, [C25, "#F28E2B"]):
        fig.add_trace(go.Bar(y=[short(i) for i in w.index], x=w[col], name=col, orientation="h",
                             marker_color=c, text=["%.1f" % v for v in w[col]],
                             textposition="outside", cliponaxis=False))
    fig.update_xaxes(title="이유 1순위 비율(%)", range=[0, float(w.max().max()) * 1.2], gridcolor="#EEE")
    return _base_layout(fig, "고등학교 유형별 학업중단 생각 이유 (1순위)", height=520,
                        barmode="group", legend=dict(orientation="h", y=1.08))


def fig_q3_dumbbell(df, mapping, tier="기본", mode="원자료", sort_year="2025"):
    """Q③ 덤벨 차트: 2023 실제 사유 ↔ 2025 생각 이유 (대응 항목)"""
    m = match_table(df, mapping, tier).sort_values(f"{sort_year} 값(%)", ascending=False, kind="stable")
    if mode == "원자료":
        a, b = m["2023 값(%)"], m["2025 값(%)"]
        xt = "1순위 응답 비율(%)"
    else:
        a, b = m["2023 상대비중(%)"], m["2025 상대비중(%)"]
        xt = "대응 항목 합계를 100으로 했을 때의 비중(%)"
    names = list(m["표시이름"])
    fig = go.Figure()
    for nm, x1, x2 in zip(names, a, b):
        fig.add_trace(go.Scatter(x=[x1, x2], y=[nm, nm], mode="lines",
                                 line=dict(color="#CCCCCC", width=5), showlegend=False,
                                 hoverinfo="skip"))
    pos23 = ["middle left" if x1 <= x2 else "middle right" for x1, x2 in zip(a, b)]
    pos25 = ["middle right" if x1 <= x2 else "middle left" for x1, x2 in zip(a, b)]
    fig.add_trace(go.Scatter(x=a, y=names, mode="markers+text", name="2023 실제 사유",
                             marker=dict(size=18, color=C23), text=["%.1f" % v for v in a],
                             textposition=pos23))
    fig.add_trace(go.Scatter(x=b, y=names, mode="markers+text", name="2025 생각 이유",
                             marker=dict(size=18, color=C25), text=["%.1f" % v for v in b],
                             textposition=pos25))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    top = float(max(a.max(), b.max()))
    fig.update_xaxes(title=xt, range=[-top * 0.08, top * 1.15], gridcolor="#EEE")
    return _base_layout(fig, "실제 중단 사유(2023)와 중단 생각 이유(2025): 대응 항목 비교",
                        height=130 + 70 * len(names), legend=dict(orientation="h", y=1.12),
                        margin=dict(l=20, r=20, t=90, b=40))


def fig_q3_area(df, mapping, tier="기본", mode="원자료", sort_year="2025"):
    m = match_table(df, mapping, tier).set_index("표시이름")
    suffix = "값(%)" if mode == "원자료" else "상대비중(%)"
    vals = m[[f"2023 {suffix}", f"2025 {suffix}"]].copy()
    vals.columns = ["2023 실제 사유", "2025 생각 이유"]
    ytitle = "원자료 비율(%)" if mode == "원자료" else "대응 항목 안 상대비중(%)"
    return _ranked_area(vals, "실제 사유와 생각 이유의 대응 항목", ytitle,
                        "2023 실제 사유" if sort_year == "2023" else "2025 생각 이유")
