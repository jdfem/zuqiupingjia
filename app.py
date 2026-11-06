# ==========================================
# 足球球员评分看板 (Plotly 历史记录管理版)
# ==========================================
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json
import os
from datetime import datetime

# ==========================================
# 1. 核心逻辑：评级函数
# ==========================================
def score_to_rank(score):
    score = float(score)
    if score >= 11: return "X"
    elif score >= 10.5: return "S+"
    elif score >= 10.0: return "S"
    elif score >= 9.5: return "S-"
    elif score >= 9.0: return "A+"
    elif score >= 8.5: return "A"
    elif score >= 8.0: return "A-"
    elif score >= 7.5: return "B+"
    elif score >= 7.0: return "B"
    elif score >= 6.5: return "B-"
    elif score >= 6.0: return "C+"
    elif score >= 5.5: return "C"
    elif score >= 5.0: return "C-"
    elif score >= 4.5: return "D+"
    elif score >= 4.0: return "D"
    elif score >= 3.5: return "D-"
    elif score >= 3.0: return "E+"
    elif score >= 2.5: return "E"
    elif score >= 2.0: return "E-"
    elif score >= 1.5: return "F"
    elif score >= 1.0: return "G"
    else: return "H"

# ==========================================
# 2. 默认维度与数据持久化
# ==========================================
DEFAULT_ABILITIES = [
    "边路传中", "直塞", "弧线传球", "短传衔接", "长传转移", "外脚背",
    "出球视野/创造力", "第一脚触球", "触球精度", "控球能力", "球感", "瞬间反应",
    "常规射门", "挑射", "远射", "点球", "任意球", "不停球射门",
    "凌空触球", "射门力量", "头球", "盘带过人/一对一盯防",
    "推进突破/回追防守", "爆发速度", "绝对速度", "加速摆脱",
    "反越位意识/造越位意识", "无球嗅觉/内收补位",
    "空间感知与预判/防守选位", "比赛阅读能力", "逆足均衡度",
    "护球", "跑位", "战术作用", "抢断", "铲球", "拦截/封堵射门",
    "弹跳能力/制空", "对抗", "体能", "铁人/抵抗伤病",
    "赛场情绪/体育精神", "大场面属性"
]

HISTORY_FILE = "player_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# 初始化状态
if 'ability_text' not in st.session_state:
    st.session_state.ability_text = "\n".join(DEFAULT_ABILITIES)
if "has_generated" not in st.session_state:
    st.session_state.has_generated = False
if "player_name_input" not in st.session_state:
    st.session_state.player_name_input = ""
if "edge_color_pick" not in st.session_state:
    st.session_state.edge_color_pick = "#000000"
if "fill_color_pick" not in st.session_state:
    st.session_state.fill_color_pick = "#87CEEB"
if "history_data" not in st.session_state:
    st.session_state.history_data = load_history()

# ==========================================
# 3. 绘图函数
# ==========================================
def player_radar_plotly(player_name, abilities, rank_list, score_list, fill_color="#87CEEB", edge_color="#000000"):
    total_score = sum(score_list) 
    n = len(abilities)
    angles = np.linspace(0, 360, n, endpoint=False).tolist()
    r_values = score_list + [score_list[0]]
    theta_values = angles + [angles[0]]
    rank_values = rank_list + [rank_list[0]]
    
    fixed_color_map = {
        "X": "#e033ff", "S+": "#ff0000", "S": "#ff333b", "S-": "#ff646a", 
        "A+": "#ff6200", "A": "#ff8529", "A-": "#ffa85c", "B+": "#40b8b8", 
        "B": "#3098c8", "B-": "#2078c0", "C+": "#d4d020", "C": "#b0d840", 
        "C-": "#80cc60", "D+": "#00a829", "D": "#28c24f", "D-": "#52d874", 
        "E+": "#ffaa00", "E": "#ffc033", "E-": "#ffd770", "F": "#4058a8", 
        "G": "#604898", "H": "#703878"
    }

    tick_texts = []
    for ab, rk in zip(abilities, rank_list):
        color = fixed_color_map.get(rk, "#333333")
        text = f"{ab}<br><span style='color:{color}; font-weight:bold;'>({rk})</span>"
        tick_texts.append(text)

    hover_texts = [f"<b>{ab}</b><br>分值: {sc:.1f}<br>评级: {rk}" for ab, sc, rk in zip(abilities, score_list, rank_list)]
    hover_texts.append(hover_texts[0])

    def hex_to_rgba(hex_color, alpha=0.7): 
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"

    fill_rgba = hex_to_rgba(fill_color, alpha=0.7)
    fig = go.Figure()
    
    theta_circle = np.linspace(0, 360, 360).tolist()
    bg_colors = ["#f5f5f5", "#ffffff", "#f5f5f5", "#ffffff", "#f5f5f5"] 
    bg_radii = [10, 8, 6, 4, 2]
    
    for radius, color in zip(bg_radii, bg_colors):
        fig.add_trace(go.Scatterpolar(
            r=[radius] * 360, theta=theta_circle, fill='toself', fillcolor=color, 
            mode='lines', line=dict(width=0, color=color), hoverinfo='none', showlegend=False
        ))
        
    fig.add_trace(go.Scatterpolar(
        r=r_values, theta=theta_values, fill='toself', fillcolor=fill_rgba,
        line=dict(color=edge_color, width=2.5), text=hover_texts, 
        hovertemplate="%{text}<extra></extra>", name=player_name
    ))

    for a in angles:
        fig.add_trace(go.Scatterpolar(
            r=[0, 10], theta=[a, a], mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.45)', width=0.8), hoverinfo='none', showlegend=False
        ))
    for r_circle in [2, 4, 6, 8]:
        fig.add_trace(go.Scatterpolar(
            r=[r_circle] * 360, theta=theta_circle, mode='lines', 
            line=dict(color='rgba(255, 255, 255, 0.45)', width=0.8), hoverinfo='none', showlegend=False
        ))
    fig.add_trace(go.Scatterpolar(
        r=[10] * 360, theta=theta_circle, mode='lines', 
        line=dict(color='rgba(255, 255, 255, 0.8)', width=1.2), hoverinfo='none', showlegend=False
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 11.5]),
            angularaxis=dict(
                tickmode='array', tickvals=angles, ticktext=tick_texts,       
                tickfont=dict(size=11, family="SimHei"), 
                gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)", 
                rotation=90, direction="clockwise"
            ),
            bgcolor="white"
        ),
        title=dict(
            text=f"<b>{player_name}</b><br>绝对能力总和: {total_score:.1f}",
            font=dict(size=22, family="SimHei", color="#333333"),
            x=0.02, y=0.98, xanchor="left", yanchor="top"
        ),
        showlegend=False, margin=dict(l=120, r=120, t=80, b=80), 
        height=850, paper_bgcolor="white"
    )
    return fig

# 统一的渲染结果函数
def render_result(data):
    fig = player_radar_plotly(
        data["player_name"], data["abilities"], data["rank_list"], data["score_list"], 
        data["fill_color"], data["edge_color"]
    )
    
    chart_config = {
        'displayModeBar': True,
        'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
        'displaylogo': False
    }
    
    st.plotly_chart(fig, use_container_width=True, config=chart_config)
    
    st.markdown(f"""
    <div style='text-align: center; font-size: 18px; margin-top: -20px; margin-bottom: 20px;'>
        <span style='color: #666;'>加权综合总分：</span><b>{data['weighted_score_sum']:.1f}</b> <span style='color: #999;'>/ {data['weighted_max_sum']:.1f}</span>
        &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
        <span style='color: #666;'>加权平均分：</span><b>{data['weighted_avg_score']:.2f}</b> <span style='color: #999;'>/ 11.0</span>
        &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
        <span style='color: #666;'>综合评级：</span><b style='font-size: 20px;'>{score_to_rank(data['weighted_avg_score'])}</b>
    </div>
    """, unsafe_allow_html=True)
    
    # 兼容处理：历史记录读出来是 list，需要转成 DataFrame
    df_to_show = data['df_display']
    if isinstance(df_to_show, list):
        df_to_show = pd.DataFrame(df_to_show)
        
    st.dataframe(df_to_show, width="stretch", hide_index=True)
    return df_to_show

# ==========================================
# 4. 网页 UI 界面与交互
# ==========================================
st.set_page_config(page_title="足球球员评分看板", layout="wide")
st.title("⚽ 足球球员评分看板")

with st.expander("📖 点击查看：看板使用总说明", expanded=False):
    st.markdown("""
    1. 这是一个**评价非门将足球运动员**的看板。为使防守球员在某些维度分值过低，进而导致能力衡量不够直观，作者对部分进攻与防守维度做了整合，例如盘带过人/盯防。强烈建议将您认为可以重合的进攻与防守维度重合，这样可以达到不低估防守球员能力，且防守球员画出的雷达图也会美观一些。
    2. 评级的说明详见左侧边栏的 **“评级说明对照表”**。
    3. **分值与评级**：分值范围为0-11，评级范围为H-X，其中雷达图的白色基准线为 10 分，即10分已经是极高水平能够填满雷达图。若某维度达到 10.5 (S+) 或 11 (X)，图形将会**超出边缘**，这是为了直观表现某些球员能力极其突出故意设置的，应谨慎设置10.5 (S+) 和 11 (X)分值及评级，其中X评级建议只选1-2人代表该维度足球历史球员的最高水平。
    4. **总分权重机制**：左侧可设置维度权重，球员的“综合总评”将基于权重加权计算。以此区分某些维度的重要性。
    5. **雷达图**：如果您发现维度文字有重叠，可以用鼠标旋转雷达图以解决重叠现象；保存雷达图的方式是将鼠标移到雷达图右上角的**相机图标**，点击即可直接保存高清图。
    """)

with st.sidebar:
    st.header("⚙️ 看板配置")
    
    if st.button("🔄 一键重置打分", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ["history_data", "ability_text"]: # 重置时不清空维度和历史记录
                del st.session_state[key]
        st.rerun()

    st.markdown("---")
    
    with st.expander("1. 管理评价维度", expanded=False):
        new_ability_text = st.text_area("维度列表 (一行一个)", value=st.session_state.get('ability_text', "\n".join(DEFAULT_ABILITIES)), height=250)
        if new_ability_text != st.session_state.get('ability_text', ""):
            st.session_state.ability_text = new_ability_text
            st.rerun()
            
    current_abilities = [line.strip() for line in st.session_state.get('ability_text', "\n".join(DEFAULT_ABILITIES)).split('\n') if line.strip()]
    
    if len(current_abilities) < 3:
        st.error("⚠️ 评价维度不能少于 3 项！")
        st.stop()
    
    with st.expander("2. 维度权重设置", expanded=True):
        df_weights = pd.DataFrame({"维度": current_abilities, "权重": [1.0] * len(current_abilities)})
        editor_key_w = f"weight_editor_{hash(tuple(current_abilities))}"
        edited_weights = st.data_editor(
            df_weights, hide_index=True, width="stretch", key=editor_key_w,
            column_config={"权重": st.column_config.NumberColumn("权重", min_value=0.0, max_value=10.0, step=0.1, format="%.1f")}
        )
        weight_dict = dict(zip(edited_weights["维度"], edited_weights["权重"]))

    with st.expander("3. X评级参考对象", expanded=False):
        df_ref = pd.DataFrame({"维度": current_abilities, "参考球员": [""] * len(current_abilities)})
        editor_key = f"ref_editor_{hash(tuple(current_abilities))}"
        edited_ref = st.data_editor(df_ref, hide_index=True, width="stretch", key=editor_key)
        ref_dict = dict(zip(edited_ref["维度"], edited_ref["参考球员"]))

    with st.expander("4. 评级说明对照表", expanded=False):
        st.markdown("""
        | 分值 | 评级 | 释义 |
        |---|---|---|
        | 11.0 | **X** | 历史极境  |
        | 10.5 | **S+** | 超殿堂  |
        | 10.0 | **S** | 殿堂级  |
        | 9.5 | **S-** | 历史级 |
        | 9.0 | **A+** | 超世界级 |
        | 8.5 | **A** | 世界级 |
        | 8.0 | **A-** | 次世界级 |
        | 7.5 | **B+** | 超洲际级 |
        | 7.0 | **B** | 洲际级 |
        | 6.5 | **B-** | 次洲际 |
        | 6.0 | **C+** | 超国家级 |
        | 5.5 | **C** | 国家级 |
        | 5.0 | **C-** | 次国家级 |
        | 4.5 | **D+** | 超平均 |
        | 4.0 | **D** | 平均 |
        | 3.5 | **D-** | 弱于平均 |
        | 3.0 | **E+** | 尚可 |
        | 2.5 | **E** | 稍弱 |
        | 2.0 | **E-** | 弱 |
        | 1.5 | **F** | 差 |
        | 1.0 | **G** | 很差 |
        | < 1.0 | **H** | 极差 |
        """)
        
    # 【更新】历史记录管理区
    with st.expander("📁 历史记录管理", expanded=True):
        if not st.session_state.history_data:
            st.info("暂无历史记录。")
        else:
            # 清空按钮
            if st.button("🗑️ 清空所有历史记录", use_container_width=True):
                st.session_state.history_data = []
                save_history([])
                st.session_state.has_generated = False
                st.session_state.view_record = None
                st.rerun()
                
            # 列出记录并添加删除按钮
            for idx, record in enumerate(reversed(st.session_state.history_data)):
                # 用倒序索引找到原数据中的真实位置
                real_idx = len(st.session_state.history_data) - 1 - idx
                col_load, col_del = st.columns([5, 1])
                
                with col_load:
                    if st.button(f"👤 {record['player_name']}", key=f"load_{idx}", use_container_width=True):
                        st.session_state.view_record = record
                        st.session_state.has_generated = True
                        st.rerun()
                with col_del:
                    if st.button("❌", key=f"del_{idx}", help="删除此记录"):
                        st.session_state.history_data.pop(real_idx)
                        save_history(st.session_state.history_data)
                        # 如果当前正在查看的就是被删掉的，清空视图
                        if st.session_state.get("view_record") == record:
                            st.session_state.has_generated = False
                            st.session_state.view_record = None
                        st.rerun()

col1, col2, col3 = st.columns(3)
with col1:
    player_name = st.text_input("被评价球员姓名", key="player_name_input").strip() or "未命名球员"
with col2:
    edge_color = st.color_picker("雷达图外线颜色", key="edge_color_pick")
with col3:
    fill_color = st.color_picker("雷达图填充颜色", key="fill_color_pick")

with st.form("rating_form"):
    st.subheader("能力打分")
    scores = {}
    
    for dim in current_abilities:
        if f"slider_{dim}" not in st.session_state:
            st.session_state[f"slider_{dim}"] = 7.0

    cols = st.columns(3) 
    for i, dim in enumerate(current_abilities):
        with cols[i % 3]:
            ref_name = ref_dict.get(dim, "").strip()
            display_label = f"{dim} (参考: {ref_name})" if ref_name else dim
            scores[dim] = st.slider(display_label, 0.0, 11.0, key=f"slider_{dim}")

    submitted = st.form_submit_button("生成雷达图与评级", type="primary", width="stretch")

# 处理表单提交
if submitted:
    score_list = [scores[dim] for dim in current_abilities]
    rank_list = [score_to_rank(s) for s in score_list]
    
    total_weight = sum(weight_dict.values())
    if total_weight == 0: total_weight = 1 
        
    weighted_score_sum = sum(sc * weight_dict.get(dim, 1.0) for dim, sc in zip(current_abilities, score_list))
    weighted_max_sum = sum(11.0 * weight_dict.get(dim, 1.0) for dim in current_abilities)
    weighted_avg_score = weighted_score_sum / total_weight
    
    display_data = []
    for dim, score, rank in zip(current_abilities, score_list, rank_list):
        ref_player = ref_dict.get(dim, "")
        ref_text = f"👉 {ref_player}" if ref_player.strip() else ""
        display_data.append({"维度": dim, "分值": score, "评级": rank, "权重": weight_dict.get(dim, 1.0), "参考对象": ref_text})
    
    current_data = {
        "player_name": player_name,
        "abilities": current_abilities,
        "rank_list": rank_list,
        "score_list": score_list,
        "fill_color": fill_color,
        "edge_color": edge_color,
        "weighted_score_sum": weighted_score_sum,
        "weighted_max_sum": weighted_max_sum,
        "weighted_avg_score": weighted_avg_score,
        "df_display": pd.DataFrame(display_data)
    }
    
    st.session_state.current_data = current_data
    st.session_state.has_generated = True
    st.session_state.view_record = None
    st.rerun()

# 渲染展示区
if st.session_state.get("has_generated", False):
    st.markdown("---")
    
    if st.session_state.get("view_record"):
        data_to_show = st.session_state.view_record
        df_display = render_result(data_to_show)
        st.info(f"📂 正在查看历史记录：{data_to_show['player_name']} (保存于 {data_to_show['timestamp']})")
    else:
        data_to_show = st.session_state.current_data
        df_display = render_result(data_to_show)
        
        # 保存按钮
        col_a, col_b = st.columns([1, 4])
        with col_a:
            if st.button("💾 保存当前球员", type="primary"):
                # 判断是否重名覆盖
                record_to_save = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "player_name": data_to_show["player_name"],
                    "abilities": data_to_show["abilities"],
                    "rank_list": data_to_show["rank_list"],
                    "score_list": data_to_show["score_list"],
                    "fill_color": data_to_show["fill_color"],
                    "edge_color": data_to_show["edge_color"],
                    "weighted_score_sum": data_to_show["weighted_score_sum"],
                    "weighted_max_sum": data_to_show["weighted_max_sum"],
                    "weighted_avg_score": data_to_show["weighted_avg_score"],
                    "df_display": data_to_show["df_display"].to_dict(orient="records")
                }
                
                # 如果历史记录里已经有这个名字，先删掉旧的（实现覆盖）
                st.session_state.history_data = [
                    r for r in st.session_state.history_data 
                    if r['player_name'] != record_to_save['player_name']
                ]
                
                st.session_state.history_data.append(record_to_save)
                save_history(st.session_state.history_data)
                st.success("✅ 已保存到历史记录！(同名球员将自动覆盖)")
    
    st.markdown("### 📥 导出数据表")
    csv_bytes = df_display.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label="📊 下载评分数据 (CSV)",
        data=csv_bytes,
        file_name=f"{data_to_show['player_name']}_评分数据.csv",
        mime="text/csv",
        use_container_width=False
    )