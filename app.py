import io
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_loader

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="FTTH Analytics Hub | لوحة مؤشرات شبكات الفايبر",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Load Custom CSS Styling
# ---------------------------------------------------------
def load_css(css_file="style.css"):
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Custom Plotly Template Defaults and Styling Helper - High Contrast Theme
def apply_chart_style(
    fig,
    title_text,
    show_legend=True,
    legend_y=-0.25,
    margin_t=120,
    margin_b=85,
    margin_l=40,
    margin_r=40,
):
    fig.update_layout(
        font=dict(family="Cairo, sans-serif", color="#0f172a"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=margin_l, r=margin_r, t=margin_t, b=margin_b),
        title=dict(
            text=title_text,
            font=dict(family="Cairo, sans-serif", size=16, color="#0f172a"),
            x=0.98,
            xanchor="right",
            y=0.98,
            yanchor="top",
            pad=dict(b=30, t=10),
        ),
        showlegend=show_legend,
        xaxis=dict(
            gridcolor="#f1f5f9",
            tickfont=dict(family="Cairo, sans-serif", color="#334155", size=12),
            title_font=dict(family="Cairo, sans-serif", color="#0f172a", size=13),
        ),
        yaxis=dict(
            gridcolor="#f1f5f9",
            tickfont=dict(family="Cairo, sans-serif", color="#334155", size=12),
            title_font=dict(family="Cairo, sans-serif", color="#0f172a", size=13),
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=13,
            font_family="Cairo, sans-serif",
            font_color="#ffffff",
        ),
    )
    if show_legend:
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="top",
                y=legend_y,
                xanchor="center",
                x=0.5,
                font=dict(family="Cairo, sans-serif", size=12, color="#0f172a"),
                bgcolor="#f8fafc",
                bordercolor="#cbd5e1",
                borderwidth=1,
            )
        )
    return fig


PLOTLY_LAYOUT = dict(
    font=dict(family="Cairo, sans-serif", color="#0f172a"),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    margin=dict(l=40, r=40, t=120, b=85),
    hoverlabel=dict(
        bgcolor="#0f172a",
        font_size=13,
        font_family="Cairo, sans-serif",
        font_color="#ffffff",
    ),
)

# Standardized Harmonious Colors for Senior Sectors
SECTOR_COLORS = {
    "رئاسة المنطقة الجنوبية": "#2563eb",  # Royal Blue
    "رئاسة القاهرة الكبرى": "#0284c7",    # Electric Sky Blue
    "رئاسة المنطقة الغربية": "#7c3aed",   # Royal Purple
    "رئاسة المنطقة الشرقية": "#059669",   # Vibrant Emerald
}


# ---------------------------------------------------------
# Data Caching & Loading
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_dashboard_data(file_source):
    df_today, df_yesterday, df_summary = data_loader.load_raw_data(file_source)
    df_comp = data_loader.calculate_comparisons(df_today, df_yesterday)
    return df_today, df_yesterday, df_comp, df_summary


# ---------------------------------------------------------
# Sidebar Controls & File Upload
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: right; padding: 10px 0 20px 0;">
            <div style="font-size: 1.45rem; font-weight: 900; color: #0284c7; display: flex; align-items: center; gap: 8px;">
                <span>⚡</span> FTTH Analytics
            </div>
            <div style="font-size: 0.9rem; color: #334155; font-weight: 600;">إدارة وتحليل بيانات شبكات الألياف الضوئية</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📂 مصدر البيانات")
    uploaded_file = st.file_uploader(
        "تحميل تقرير إكسيل جديد (اختياري)",
        type=["xlsx", "xls"],
        help="يمكنك سحب أي ملف إكسيل مماثل لتحديث لوحة البيانات فورياً",
    )

    data_source = uploaded_file if uploaded_file is not None else "FTTH Report.xlsx"

    try:
        df_today, df_yesterday, df_comp, df_summary = get_dashboard_data(data_source)
        file_status = "ملف مخصص مرفوع" if uploaded_file else "ملف التقرير الافتراضي (FTTH Report.xlsx)"
        st.caption(f"✅ المصدر الحالي: {file_status}")
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف الإكسيل: {e}")
        st.stop()

    st.markdown("---")
    st.markdown("### 🎯 نطاق العرض والتركيز")
    scope_option = st.radio(
        "اختر نطاق البيانات:",
        options=[
            "🌟 رئاسة المنطقة الغربية فقط (Western Focus)",
            "🏢 كافة الرئاسات والقطاعات (All Regions)",
        ],
        index=0,  # Default to Western Region Focus as requested!
    )
    is_western_mode = "الغربية" in scope_option

    st.markdown("---")
    st.markdown("### 🔍 فلترة البيانات المتقدمة")

    # Filter 1: Senior Sector
    all_senior_sectors = sorted(df_comp["Senior_Sector"].unique().tolist())
    default_senior = ["رئاسة المنطقة الغربية"] if (is_western_mode and "رئاسة المنطقة الغربية" in all_senior_sectors) else all_senior_sectors

    selected_senior_sectors = st.multiselect(
        "رئاسة القطاع (Senior Sector)",
        options=all_senior_sectors,
        default=default_senior,
        placeholder="اختر رئاسة واحدة أو أكثر...",
    )

    if not selected_senior_sectors:
        selected_senior_sectors = all_senior_sectors

    # Filter 2: Sector (Dependent on Senior Sector)
    available_sectors = sorted(
        df_comp[df_comp["Senior_Sector"].isin(selected_senior_sectors)]["Sector"].unique().tolist()
    )
    selected_sectors = st.multiselect(
        "القطاع (Sector)",
        options=available_sectors,
        default=available_sectors,
        placeholder="اختر قطاعاً أو أكثر...",
    )

    if not selected_sectors:
        selected_sectors = available_sectors

    # Filter 3: Type
    available_types = sorted(df_comp["Type"].unique().tolist())
    selected_types = st.multiselect(
        "نوع المشروع (Type)",
        options=available_types,
        default=available_types,
    )
    if not selected_types:
        selected_types = available_types

    # Apply filters
    filtered_df = df_comp[
        (df_comp["Senior_Sector"].isin(selected_senior_sectors))
        & (df_comp["Sector"].isin(selected_sectors))
        & (df_comp["Type"].isin(selected_types))
    ].copy()

    st.markdown("---")
    st.markdown(
        f"""
        <div style="background: #f1f5f9; padding: 14px; border-radius: 12px; border: 1px solid #cbd5e1; font-size: 0.9rem; color: #0f172a; font-weight: 700;">
            <div>📊 <b>المناطق المحددة:</b> {len(filtered_df)} من {len(df_comp)}</div>
            <div>🏢 <b>الرئاسات المحددة:</b> {len(selected_senior_sectors)}</div>
            <div>📌 <b>القطاعات المحددة:</b> {len(selected_sectors)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Dynamic Hero Banner (Western Focus vs Global)
# ---------------------------------------------------------
total_completed = filtered_df["Total_Completed_YTD"].sum()
total_survey = filtered_df["Total_Survey_Done_YTD"].sum()
total_yesterday = filtered_df["Total_Yesterday"].sum()
total_last_7 = filtered_df["Total_Last_7_Days"].sum()
total_pending = filtered_df["Total_Pending_Survey"].sum()
total_flagged = filtered_df["Flagged_Total"].sum()

delta_completed = filtered_df["Delta_Total_Completed"].sum() if "Delta_Total_Completed" in filtered_df.columns else 0
delta_pending = filtered_df["Delta_Pending_Survey"].sum() if "Delta_Pending_Survey" in filtered_df.columns else 0
delta_flagged = filtered_df["Delta_Flagged"].sum() if "Delta_Flagged" in filtered_df.columns else 0

is_western_view = (len(selected_senior_sectors) == 1 and "الغربية" in selected_senior_sectors[0])

if is_western_view:
    banner_title = "منظومة متابعة وتحليل إنجاز رئاسة المنطقة الغربية (Western Region Focus)"
    banner_subtitle = "عرض تفصيلي شامل لكافة قطاعات ومناطق رئاسة المنطقة الغربية (الأسكندرية، الساحل الشمالي ومطروح، غرب ووسط الدلتا)، مع تتبع دقيق للإنجاز التراكمي وصافي التغير اليومي"
else:
    banner_title = "منظومة متابعة وتحليل شبكات الألياف الضوئية (FTTH Dashboard)"
    banner_subtitle = "تحليل ذكي ومترابط لبيانات إنجاز الفايبر، ربط المعاينات بالتنفيذ الفعلي، وتتبع الأداء اليومي والأسبوعي عبر كافة القطاعات"

st.markdown(
    f"""
    <div class="hero-banner">
        <div class="hero-title">{banner_title}</div>
        <div class="hero-subtitle">{banner_subtitle}</div>
        <div>
            <span class="badge-pill cyan">⚡ إجمالي المنفذ (YTD): {total_completed:,.0f} خط</span>
            <span class="badge-pill success">📈 صافي التغير اليومي (Delta): {delta_completed:+,.0f} خط مضاف</span>
            <span class="badge-pill purple">⚡ إنجاز الأمس الفعلي: {total_yesterday:,.0f} خط</span>
            <span class="badge-pill">🏢 عدد المناطق المشمولة: {len(filtered_df)} منطقة</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Executive KPI Cards (6 Grid Cards with Distinct Accent Ribbons)
# ---------------------------------------------------------
def render_kpi(
    col,
    title,
    value,
    icon,
    accent_color="#2563eb",
    icon_bg="#eff6ff",
    icon_color="#1d4ed8",
    icon_border="#bfdbfe",
    badge_text=None,
    badge_class="badge-green",
):
    badge_html = ""
    if badge_text:
        badge_html = f'<div class="kpi-badge {badge_class}">{badge_text}</div>'

    html = f"""
    <div class="kpi-card" style="--accent-color: {accent_color};">
        <div class="kpi-header">
            <span class="kpi-title">{title}</span>
            <div class="kpi-icon-box" style="--icon-bg: {icon_bg}; --icon-color: {icon_color}; --icon-border: {icon_border};">{icon}</div>
        </div>
        <div class="kpi-value">{value}</div>
        {badge_html}
    </div>
    """
    col.markdown(html, unsafe_allow_html=True)


kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5, kpi_c6 = st.columns(6)

conversion_rate = (total_completed / total_survey * 100) if total_survey > 0 else 0
mig_share = (filtered_df["Mig_Completed_YTD"].sum() / total_completed * 100) if total_completed > 0 else 0

render_kpi(
    kpi_c1,
    "إجمالي المنفذ (YTD)",
    f"{total_completed:,.0f}",
    "🚀",
    accent_color="#2563eb",
    icon_bg="#eff6ff",
    icon_color="#1d4ed8",
    icon_border="#bfdbfe",
    badge_text=f"▲ +{delta_completed:,.0f} نمو يومي (+{delta_completed/max(total_completed,1)*100:.2f}%)",
    badge_class="badge-green",
)

render_kpi(
    kpi_c2,
    "المعاينات المنجزة",
    f"{total_survey:,.0f}",
    "📋",
    accent_color="#0284c7",
    icon_bg="#e0f2fe",
    icon_color="#0369a1",
    icon_border="#bae6fd",
    badge_text=f"نسبة التحويل {conversion_rate:.1f}%",
    badge_class="badge-blue",
)

render_kpi(
    kpi_c3,
    "إنجاز الأمس الفعلي",
    f"{total_yesterday:,.0f}",
    "⚡",
    accent_color="#059669",
    icon_bg="#ecfdf5",
    icon_color="#047857",
    icon_border="#a7f3d0",
    badge_text="تنفيذ يومي نشط",
    badge_class="badge-green",
)

render_kpi(
    kpi_c4,
    "إنجاز آخر 7 أيام",
    f"{total_last_7:,.0f}",
    "📅",
    accent_color="#7c3aed",
    icon_bg="#f5f3ff",
    icon_color="#6d28d9",
    icon_border="#ddd6fe",
    badge_text=f"معدل ~{total_last_7/7:,.0f} خط/يوم",
    badge_class="badge-purple",
)

render_kpi(
    kpi_c5,
    "معاينات معلقة (Pending)",
    f"{total_pending:,.0f}",
    "⏳",
    accent_color="#d97706",
    icon_bg="#fffbeb",
    icon_color="#b45309",
    icon_border="#fde68a",
    badge_text=f"▼ {delta_pending:+,.0f} تراجع المعلق",
    badge_class="badge-green" if delta_pending <= 0 else "badge-red",
)

render_kpi(
    kpi_c6,
    "حالات المتابعة (Flagged)",
    f"{total_flagged:,.0f}",
    "🚩",
    accent_color="#dc2626",
    icon_bg="#fef2f2",
    icon_color="#b91c1c",
    icon_border="#fecaca",
    badge_text=f"▼ {delta_flagged:+,.0f} معالجة المشاكل",
    badge_class="badge-green" if delta_flagged <= 0 else "badge-red",
)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Tabs Navigation
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 لوحة المؤشرات التنفيذية (Overview)",
    "🔗 التحليل المقارن والربط (Correlation & Deltas)",
    "🏢 التحليل الهيكلي للقطاعات (Sectors & Deep Dive)",
    "📑 مستكشف البيانات واستخراج التقارير (Data & Export)",
])


# =========================================================
# TAB 1: EXECUTIVE OVERVIEW
# =========================================================
with tab1:
    col_left, col_right = st.columns([7, 5])

    with col_left:
        # Chart 1: Completed by Sector (if single Senior Sector/West) or Senior Sector (if multiple)
        chart1_group = "Sector" if (is_western_view or len(selected_senior_sectors) == 1) else "Senior_Sector"
        chart1_label = "قطاعات المنطقة الغربية" if is_western_view else ("قطاعات الرئاسة المحددة" if len(selected_senior_sectors) == 1 else "رئاسات القطاعات")

        senior_agg = (
            filtered_df.groupby(chart1_group)[["New_Completed_YTD", "Mig_Completed_YTD", "Total_Completed_YTD"]]
            .sum()
            .reset_index()
            .sort_values(by="Total_Completed_YTD", ascending=True)
        )

        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                y=senior_agg[chart1_group],
                x=senior_agg["New_Completed_YTD"],
                name="تركيبات جديدة (New)",
                orientation="h",
                marker=dict(color="#0284c7", line=dict(color="#ffffff", width=1.5)),
                hovertemplate="<b>%{y}</b><br>جديد: %{x:,.0f} خط<extra></extra>",
            )
        )
        fig_bar.add_trace(
            go.Bar(
                y=senior_agg[chart1_group],
                x=senior_agg["Mig_Completed_YTD"],
                name="تحويل وإحلال (Migration)",
                orientation="h",
                marker=dict(color="#7c3aed", line=dict(color="#ffffff", width=1.5)),
                hovertemplate="<b>%{y}</b><br>تحويل: %{x:,.0f} خط<extra></extra>",
            )
        )

        fig_bar.update_layout(
            barmode="stack",
            xaxis=dict(title="إجمالي الخطوط المنفذة", gridcolor="#f1f5f9"),
            yaxis=dict(title=""),
        )
        apply_chart_style(
            fig_bar,
            f"<b>مقارنة إنجاز الفايبر التراكمي حسب {chart1_label}</b> (New vs Migration)",
            show_legend=True,
            legend_y=-0.25,
            margin_t=120,
            margin_b=80,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        # Chart 2: Donut Breakdown (New vs Migration)
        new_total = filtered_df["New_Completed_YTD"].sum()
        mig_total = filtered_df["Mig_Completed_YTD"].sum()

        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=["تحويل وإحلال (Migration)", "تركيبات جديدة (New)"],
                    values=[mig_total, new_total],
                    hole=0.62,
                    marker=dict(colors=["#7c3aed", "#0284c7"], line=dict(color="#ffffff", width=2.5)),
                    textinfo="label+percent",
                    textfont=dict(family="Cairo, sans-serif", size=13, color="#ffffff"),
                    hovertemplate="<b>%{label}</b><br>العدد: %{value:,.0f} خط (%{percent})<extra></extra>",
                )
            ]
        )
        fig_donut.update_layout(
            annotations=[
                dict(
                    text=f"<b>{total_completed:,.0f}</b><br><span style='font-size:13px;color:#334155;font-weight:700;'>إجمالي المنفذ</span>",
                    x=0.5,
                    y=0.5,
                    font_size=18,
                    font_color="#0f172a",
                    showarrow=False,
                )
            ],
        )
        apply_chart_style(
            fig_donut,
            "<b>مزيج العمليات المنفذة (Operational Mix)</b>",
            show_legend=True,
            legend_y=-0.16,
            margin_t=115,
            margin_b=65,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")

    # Row 2: Velocity & Survey-to-Completion Ratio
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        # Chart 3: 7 Days Velocity by Sector (Top 10)
        top_velocity = (
            filtered_df.groupby("Sector")[["Total_Last_7_Days", "Total_Yesterday"]]
            .sum()
            .reset_index()
            .sort_values(by="Total_Last_7_Days", ascending=False)
            .head(10)
        )

        fig_vel = go.Figure()
        fig_vel.add_trace(
            go.Bar(
                x=top_velocity["Sector"],
                y=top_velocity["Total_Last_7_Days"],
                name="إنجاز آخر 7 أيام",
                marker=dict(color="#059669", line=dict(color="#ffffff", width=1)),
                hovertemplate="<b>%{x}</b><br>آخر 7 أيام: %{y:,.0f} خط<extra></extra>",
            )
        )
        fig_vel.add_trace(
            go.Scatter(
                x=top_velocity["Sector"],
                y=top_velocity["Total_Yesterday"] * 7,  # Run rate projection
                mode="lines+markers",
                name="معدل إسقاط الأمس (Run-Rate x7)",
                line=dict(color="#d97706", width=3, dash="dot"),
                marker=dict(size=7, color="#d97706"),
                hovertemplate="<b>%{x}</b><br>معدل الأمس المتوقع أسبوعياً: %{y:,.0f}<extra></extra>",
            )
        )
        fig_vel.update_layout(
            xaxis=dict(title="", tickangle=-30),
            yaxis=dict(title="الخطوط المنفذة", gridcolor="#f1f5f9"),
        )
        apply_chart_style(
            fig_vel,
            "<b>سرعة الإنجاز التشغيلي (Weekly Velocity - Top 10 Sectors)</b>",
            show_legend=True,
            legend_y=-0.44,
            margin_t=120,
            margin_b=130,
        )
        st.plotly_chart(fig_vel, use_container_width=True)

    with col_v2:
        # Chart 4: Funnel / Conversion Efficiency across Senior Sectors
        funnel_agg = (
            filtered_df.groupby("Senior_Sector")[["Total_Survey_Done_YTD", "Total_Completed_YTD", "Total_Pending_Survey"]]
            .sum()
            .reset_index()
            .sort_values(by="Total_Survey_Done_YTD", ascending=False)
        )
        funnel_agg["Conv_Rate"] = (funnel_agg["Total_Completed_YTD"] / funnel_agg["Total_Survey_Done_YTD"] * 100).round(1)

        fig_conv = go.Figure()
        fig_conv.add_trace(
            go.Bar(
                x=funnel_agg["Senior_Sector"],
                y=funnel_agg["Total_Survey_Done_YTD"],
                name="المعاينات المنجزة",
                marker=dict(color="#2563eb", line=dict(color="#ffffff", width=1)),
                hovertemplate="<b>%{x}</b><br>معاينات: %{y:,.0f}<extra></extra>",
            )
        )
        fig_conv.add_trace(
            go.Bar(
                x=funnel_agg["Senior_Sector"],
                y=funnel_agg["Total_Completed_YTD"],
                name="التنفيذ الفعلي",
                marker=dict(color="#059669", line=dict(color="#ffffff", width=1)),
                hovertemplate="<b>%{x}</b><br>منفذ: %{y:,.0f}<extra></extra>",
            )
        )
        fig_conv.add_trace(
            go.Bar(
                x=funnel_agg["Senior_Sector"],
                y=funnel_agg["Total_Pending_Survey"],
                name="معاينات معلقة",
                marker=dict(color="#d97706", line=dict(color="#ffffff", width=1)),
                hovertemplate="<b>%{x}</b><br>معلق: %{y:,.0f}<extra></extra>",
            )
        )

        fig_conv.update_layout(
            barmode="group",
            xaxis=dict(title=""),
            yaxis=dict(title="عدد الخطوط", gridcolor="#f1f5f9"),
        )
        apply_chart_style(
            fig_conv,
            "<b>مسار التحويل (المعاينات المنجزة مقابل التنفيذ الفعلي والمعلق)</b>",
            show_legend=True,
            legend_y=-0.26,
            margin_t=120,
            margin_b=85,
        )
        st.plotly_chart(fig_conv, use_container_width=True)


# =========================================================
# TAB 2: CORRELATION & TODAY VS YESTERDAY DELTAS
# =========================================================
with tab2:
    st.markdown(
        """
        <div style="background: #ffffff; padding: 18px 24px; border-radius: 16px; border: 1px solid #cbd5e1; margin-bottom: 22px; box-shadow: 0 2px 10px rgba(0,0,0,0.04);">
            <b style="color: #0284c7; font-size: 1.15rem;">🔗 الربط والتحليل المقارن (Data Correlation & Dynamics):</b>
            <div style="color: #334155; font-size: 1rem; margin-top: 6px; line-height: 1.6; font-weight: 600;">
                يقوم هذا القسم بمقارنة بيانات اليوم بالأمس مباشرة للكشف عن حركة الإنجاز الفعلية، وتحديد ما إذا كان تراكم المعاينات المعلقة أو الحالات المحددة (Flagged) يؤثر سلباً على معدل الإنجاز.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_cor1, col_cor2 = st.columns([7, 5])

    with col_cor1:
        # Correlation Bubble Plot: Survey Volume vs Completion with Pending as Bubble Size
        fig_bubble = px.scatter(
            filtered_df,
            x="Total_Survey_Done_YTD",
            y="Total_Completed_YTD",
            size="Total_Pending_Survey",
            color="Senior_Sector",
            color_discrete_map=SECTOR_COLORS,
            hover_name="Region",
            hover_data={
                "Sector": True,
                "Completion_Rate": ":.1f%",
                "Total_Yesterday": ":,",
                "Total_Pending_Survey": ":,",
                "Flagged_Total": ":,",
            },
            title="<b>العلاقة الارتباطية: المعاينات المنجزة مقابل التنفيذ الفعلي</b> (حجم الفقاعة = المعاينات المعلقة)",
            labels={
                "Total_Survey_Done_YTD": "إجمالي المعاينات المنجزة (YTD)",
                "Total_Completed_YTD": "إجمالي التنفيذ الفعلي (YTD)",
                "Senior_Sector": "رئاسة القطاع",
            },
        )
        # Add 1:1 reference line
        max_val = max(filtered_df["Total_Survey_Done_YTD"].max(), filtered_df["Total_Completed_YTD"].max())
        fig_bubble.add_shape(
            type="line",
            line=dict(dash="dash", color="rgba(255,255,255,0.3)"),
            x0=0,
            x1=max_val,
            y0=0,
            y1=max_val,
        )
        fig_bubble.update_layout(
            xaxis=dict(gridcolor="#f1f5f9"),
            yaxis=dict(gridcolor="#f1f5f9"),
        )
        apply_chart_style(
            fig_bubble,
            "<b>العلاقة الارتباطية: المعاينات المنجزة مقابل التنفيذ الفعلي</b> (حجم الفقاعة = المعاينات المعلقة)",
            show_legend=True,
            legend_y=-0.26,
            margin_t=120,
            margin_b=85,
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

    with col_cor2:
        # Correlation Matrix Heatmap
        corr_cols = [
            "New_Completed_YTD",
            "Mig_Completed_YTD",
            "Total_Pending_Survey",
            "Flagged_Total",
            "Total_Yesterday",
        ]
        corr_labels = [
            "جديد منفذ",
            "تحويل منفذ",
            "معاينات معلقة",
            "حالات Flagged",
            "إنجاز الأمس",
        ]
        corr_matrix = filtered_df[corr_cols].corr().values

        fig_heat = go.Figure(
            data=go.Heatmap(
                z=corr_matrix,
                x=corr_labels,
                y=corr_labels,
                colorscale="Blues",
                zmin=-1,
                zmax=1,
                text=np.round(corr_matrix, 2),
                texttemplate="%{text}",
                textfont=dict(size=12, color="#0f172a"),
                colorbar=dict(title="معامل الارتباط"),
            )
        )
        apply_chart_style(
            fig_heat,
            "<b>مصفوفة الارتباط الإحصائي (Correlation Matrix)</b>",
            show_legend=False,
            margin_t=115,
            margin_b=60,
            margin_l=40,
            margin_r=40,
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # Delta Highlights
    st.markdown("### 📈 حركة الإنجاز والتغير اليومي (Today vs Yesterday Dynamics)")
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        # Growing Regions by Daily Delta Completed (All regions if <= 15, else top 10)
        if "Delta_Total_Completed" in filtered_df.columns:
            limit_n = len(filtered_df) if len(filtered_df) <= 15 else 10
            top_growth = filtered_df.sort_values(by="Delta_Total_Completed", ascending=False).head(limit_n)
            delta_title = "<b>صافي التغير اليومي في الإنجاز لكافة مناطق المنطقة الغربية</b> (Delta Completed)" if is_western_view else f"<b>أعلى {limit_n} مناطق تحقيقاً لزيادة الإنجاز التراكمي بالأمس</b> (Delta Completed)"
            fig_delta_comp = px.bar(
                top_growth,
                x="Delta_Total_Completed",
                y="Region",
                orientation="h",
                color="Sector" if is_western_view else "Senior_Sector",
                color_discrete_map=SECTOR_COLORS,
                title=delta_title,
                labels={"Delta_Total_Completed": "صافي الإنجاز المضاف بالأمس", "Region": "المنطقة"},
            )
            fig_delta_comp.update_layout(
                yaxis=dict(autorange="reversed"),
                xaxis=dict(title="صافي الإنجاز المضاف", gridcolor="#f1f5f9"),
            )
            apply_chart_style(
                fig_delta_comp,
                delta_title,
                show_legend=True,
                legend_y=-0.30,
                margin_t=120,
                margin_b=90,
            )
            st.plotly_chart(fig_delta_comp, use_container_width=True)

    with col_d2:
        # Pending Backlog Reduction / Increase
        if "Delta_Pending_Survey" in filtered_df.columns:
            limit_n = len(filtered_df) if len(filtered_df) <= 15 else 10
            backlog_change = filtered_df.sort_values(by="Delta_Pending_Survey", ascending=True).head(limit_n)
            backlog_title = "<b>تغير رصيد المعاينات المعلقة لكافة مناطق المنطقة الغربية</b> (Backlog Reduced)" if is_western_view else f"<b>أفضل {limit_n} مناطق في تسريع وتصفية المعاينات المعلقة</b> (Backlog Reduced)"
            fig_backlog = px.bar(
                backlog_change,
                x="Delta_Pending_Survey",
                y="Region",
                orientation="h",
                color_discrete_sequence=["#059669"],
                title=backlog_title,
                labels={"Delta_Pending_Survey": "تغير رصيد المعاينات المعلقة", "Region": "المنطقة"},
            )
            fig_backlog.update_layout(
                yaxis=dict(autorange="reversed"),
                xaxis=dict(title="تغير رصيد المعاينات المعلقة", gridcolor="#f1f5f9"),
            )
            apply_chart_style(
                fig_backlog,
                backlog_title,
                show_legend=False,
                margin_t=120,
                margin_b=65,
            )
            st.plotly_chart(fig_backlog, use_container_width=True)


# =========================================================
# TAB 3: SECTOR HIERARCHY & BOTTLENECK ANALYSIS
# =========================================================
with tab3:
    st.markdown("### 🌳 الهيكل التنظيمي للإنجاز (Administrative Hierarchy)")
    # Treemap of Senior Sector -> Sector -> Region
    fig_tree = px.treemap(
        filtered_df,
        path=["Senior_Sector", "Sector", "Region"],
        values="Total_Completed_YTD",
        color="Completion_Rate",
        color_continuous_scale="Blues",
        title="<b>شجرة التوزيع الجغرافي والإداري لمشاريع FTTH</b> (المساحة = حجم الإنجاز | اللون = نسبة إنجاز المعاينات)",
        hover_data={
            "Total_Completed_YTD": ":,",
            "Total_Pending_Survey": ":,",
            "Flagged_Total": ":,",
        },
    )
    apply_chart_style(
        fig_tree,
        "<b>شجرة التوزيع الجغرافي والإداري لمشاريع FTTH</b> (المساحة = حجم الإنجاز | اللون = نسبة إنجاز المعاينات)",
        show_legend=False,
        margin_t=115,
        margin_b=35,
        margin_l=20,
        margin_r=20,
    )
    st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown("---")

    st.markdown("---")

    if is_western_view:
        st.markdown("### 🏢 بطاقات أداء قطاعات المنطقة الغربية الأربعة (Sectors Performance Scorecards)")
        sec_agg = (
            filtered_df.groupby("Sector")
            .agg(
                Total_Completed_YTD=("Total_Completed_YTD", "sum"),
                New_Completed_YTD=("New_Completed_YTD", "sum"),
                Mig_Completed_YTD=("Mig_Completed_YTD", "sum"),
                Total_Yesterday=("Total_Yesterday", "sum"),
                Delta_Total_Completed=("Delta_Total_Completed", "sum"),
                Total_Survey_Done_YTD=("Total_Survey_Done_YTD", "sum"),
                Total_Pending_Survey=("Total_Pending_Survey", "sum"),
                Flagged_Total=("Flagged_Total", "sum"),
            )
            .reset_index()
            .sort_values(by="Total_Completed_YTD", ascending=False)
        )
        sec_cols = st.columns(len(sec_agg))
        for s_idx, s_row in sec_agg.iterrows():
            with sec_cols[s_idx]:
                conv = (s_row["Total_Completed_YTD"] / s_row["Total_Survey_Done_YTD"] * 100) if s_row["Total_Survey_Done_YTD"] > 0 else 0
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-top: 4px solid #2563eb; border-radius: 14px; padding: 16px; box-shadow: 0 4px 14px rgba(15,23,42,0.04);">
                        <div style="font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">{s_row['Sector']}</div>
                        <div style="font-size: 1.6rem; font-weight: 900; color: #2563eb; margin-bottom: 4px;">{s_row['Total_Completed_YTD']:,.0f}</div>
                        <div style="font-size: 0.85rem; color: #475569; margin-bottom: 10px;">إجمالي المنفذ ({(s_row['Total_Completed_YTD']/max(total_completed,1)*100):.1f}% من الغربية)</div>
                        <hr style="margin: 8px 0; border: none; border-top: 1px solid #e2e8f0;" />
                        <div style="font-size: 0.85rem; color: #334155; display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>📈 صافي التغير اليومي:</span>
                            <b style="color: #15803d;">+{s_row['Delta_Total_Completed']:,.0f}</b>
                        </div>
                        <div style="font-size: 0.85rem; color: #334155; display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>⚡ منفذ الأمس:</span>
                            <b>{s_row['Total_Yesterday']:,.0f}</b>
                        </div>
                        <div style="font-size: 0.85rem; color: #334155; display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>⏳ المعاينات المعلقة:</span>
                            <b style="color: #b45309;">{s_row['Total_Pending_Survey']:,.0f}</b>
                        </div>
                        <div style="font-size: 0.85rem; color: #334155; display: flex; justify-content: space-between;">
                            <span>🎯 نسبة التحويل:</span>
                            <b>{conv:.1f}%</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 📋 البيان التفصيلي الشامل لكافة مناطق المنطقة الغربية (All 12 Western Regions)")
        west_summary_table = filtered_df[[
            "Sector",
            "Region",
            "Total_Completed_YTD",
            "Delta_Total_Completed",
            "Total_Yesterday",
            "Total_Last_7_Days",
            "New_Completed_YTD",
            "Mig_Completed_YTD",
            "Total_Survey_Done_YTD",
            "Total_Pending_Survey",
            "Completion_Rate",
            "Flagged_Total",
        ]].sort_values(by="Total_Completed_YTD", ascending=False).rename(
            columns={
                "Sector": "القطاع",
                "Region": "المنطقة",
                "Total_Completed_YTD": "إجمالي المنفذ (YTD)",
                "Delta_Total_Completed": "صافي التغير اليومي (Delta)",
                "Total_Yesterday": "إنجاز الأمس",
                "Total_Last_7_Days": "إنجاز آخر 7 أيام",
                "New_Completed_YTD": "جديد منفذ",
                "Mig_Completed_YTD": "تحويل منفذ",
                "Total_Survey_Done_YTD": "معاينات منجزة",
                "Total_Pending_Survey": "معاينات معلقة",
                "Completion_Rate": "نسبة الإنجاز %",
                "Flagged_Total": "حالات Flagged",
            }
        )
        st.dataframe(west_summary_table, use_container_width=True, hide_index=True)
    else:
        col_rank1, col_rank2 = st.columns(2)

        with col_rank1:
            st.markdown("#### 🏆 لوحة الشرف: أعلى 10 مناطق إنجازاً (Top 10)")
            top_10 = filtered_df.sort_values(by="Total_Completed_YTD", ascending=False).head(10)
            st.dataframe(
                top_10[["Senior_Sector", "Sector", "Region", "Total_Completed_YTD", "Total_Yesterday", "Completion_Rate"]].rename(
                    columns={
                        "Senior_Sector": "رئاسة القطاع",
                        "Sector": "القطاع",
                        "Region": "المنطقة",
                        "Total_Completed_YTD": "إجمالي المنفذ",
                        "Total_Yesterday": "إنجاز الأمس",
                        "Completion_Rate": "نسبة الإنجاز %",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        with col_rank2:
            st.markdown("#### ⚠️ مناطق الاختناق وتراكم المعاينات المعلقة (Bottlenecks)")
            bottlenecks = filtered_df.sort_values(by="Total_Pending_Survey", ascending=False).head(10)
            st.dataframe(
                bottlenecks[["Senior_Sector", "Sector", "Region", "Total_Pending_Survey", "Flagged_Total", "New_Pending_Survey", "Mig_Pending_Survey"]].rename(
                    columns={
                        "Senior_Sector": "رئاسة القطاع",
                        "Sector": "القطاع",
                        "Region": "المنطقة",
                        "Total_Pending_Survey": "إجمالي المعلق",
                        "Flagged_Total": "حالات Flagged",
                        "New_Pending_Survey": "معلق (جديد)",
                        "Mig_Pending_Survey": "معلق (تحويل)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# TAB 4: DATA EXPLORER & EXPORT
# =========================================================
with tab4:
    st.markdown("### 📑 مستكشف البيانات التفاعلي وتصدير التقارير")

    # Search Bar
    search_query = st.text_input("🔍 بحث فوري في أسماء القطاعات أو المناطق:", placeholder="اكتب اسم المنطقة أو القطاع...")
    display_df = filtered_df.copy()

    if search_query:
        display_df = display_df[
            display_df["Senior_Sector"].str.contains(search_query, case=False, na=False)
            | display_df["Sector"].str.contains(search_query, case=False, na=False)
            | display_df["Region"].str.contains(search_query, case=False, na=False)
        ]

    # Display Columns Mapping
    col_export_map = {
        "Senior_Sector": "رئاسة القطاع",
        "Sector": "القطاع",
        "Region": "المنطقة",
        "Type": "النوع",
        "Total_Completed_YTD": "إجمالي المنفذ (YTD)",
        "New_Completed_YTD": "منفذ جديد (YTD)",
        "Mig_Completed_YTD": "منفذ تحويل (YTD)",
        "Total_Yesterday": "منفذ الأمس",
        "Total_Last_7_Days": "منفذ آخر 7 أيام",
        "Total_Survey_Done_YTD": "معاينات منجزة",
        "Total_Pending_Survey": "معاينات معلقة",
        "Completion_Rate": "نسبة الإنجاز %",
        "Mig_Share": "نسبة التحويل %",
        "Flagged_Total": "حالات Flagged",
    }

    if "Delta_Total_Completed" in display_df.columns:
        col_export_map["Delta_Total_Completed"] = "تغير الإنجاز اليومي"
    if "Delta_Pending_Survey" in display_df.columns:
        col_export_map["Delta_Pending_Survey"] = "تغير المعاينات المعلقة"

    available_show_cols = [c for c in col_export_map.keys() if c in display_df.columns]
    renamed_df = display_df[available_show_cols].rename(columns=col_export_map)

    st.dataframe(
        renamed_df,
        use_container_width=True,
        hide_index=True,
    )

    # Export Buttons
    col_exp1, col_exp2, col_exp3 = st.columns([2, 2, 8])

    # Excel Export
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        renamed_df.to_excel(writer, sheet_name="FTTH_Report", index=False)
    excel_data = excel_buffer.getvalue()

    col_exp1.download_button(
        label="📥 تنزيل كملف Excel (.xlsx)",
        data=excel_data,
        file_name="FTTH_Analytics_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # CSV Export
    csv_data = renamed_df.to_csv(index=False).encode("utf-8-sig")
    col_exp2.download_button(
        label="📄 تنزيل كملف CSV",
        data=csv_data,
        file_name="FTTH_Analytics_Export.csv",
        mime="text/csv",
        use_container_width=True,
    )
