# ==========================================
# 足球球员评分看板 (Plotly 邮箱登录+固定顺序版)
# ==========================================
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client

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
# 2. Supabase 初始化与邮箱登录
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        st.error("⚠️ 未找到 Supabase 密钥，请检查 Streamlit Secrets 配置！")
        st.stop()
    return create_client(url, key)

supabase = init_supabase()

# 检查登录状态
if "sb_session" not in st.session_state:
    st.markdown("## 🔐 欢迎来到足球球员评分看板")
    st.info("💡 **为了让您的历史记录永久保存且不丢失，请先登录或注册。** (随便填一个常用的邮箱和密码即可)")
    
    with st.form("auth_form"):
        email = st.text_input("邮箱 (Email)")
        password = st.text_input("密码 (Password)", type="password")
        
        col1, col2 = st.columns(2)
        submit_login = col1.form_submit_button("登录", type="primary", use_container_width=True)
        submit_register = col2.form_submit_button("注册", use_container_width=True)
        
        if submit_login:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.sb_session = res.session
                st.rerun()
            except Exception as e:
                st.error(f"登录失败: {e}")
        elif submit_register:
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.success("注册成功！请点击左侧的‘登录’按钮直接登录。（注：如提示需验证邮箱，请联系管理员）")
            except Exception as e:
                st.error(f"注册失败: {e}")
    
    # 未登录时停止渲染后续看板内容
    st.stop()

# ==========================================
# 3. 默认维度 (按照 1-49 的顺序固定排列)
# ==========================================
DEFAULT_ABILITIES = [
    "短传衔接", "长传转移", "直塞", "传中", "弧线球", "外脚背", "高压出球",
    "第一脚触球", "触球精度", "控球能力", "护球", "逆足均衡度",
    "出球视野/创造力", "瞬间反应", "空间感知与预判", "比赛阅读能力",
    "常规射门", "不停球射门", "挑射", "远射", "凌空触球", "射门力量", "点球", "任意球",
    "头球攻门", "解围",
    "盘带过人", "推进突破", "变向灵活性", "跑位", "无球进攻嗅觉", "越位意识",
    "一对一盯防", "抢断", "铲球", "线路封堵", "内收补位意识", "防守选位",
    "绝对速度", "爆发速度", "加速摆脱", "回追防守", "弹跳/制空", "主动对抗", "被动对抗", "体能耐力",
    "抵抗伤病", "大场面属性", "赛场情绪"
]

# ==========================================
# 4. 各位置权重预设库
# ==========================================
POSITION_PRESETS = {
    "中后卫 (CB)": {
        "短传衔接": 1.2, "长传转移": 1.7, "直塞": 1.0, "传中": 1.0, "弧线球": 1.0, "外脚背": 1.0, "高压出球": 1.7,
        "第一脚触球": 1.2, "触球精度": 1.0, "控球能力": 1.0, "护球": 1.7, "逆足均衡度": 1.0,
        "出球视野/创造力": 1.0, "瞬间反应": 1.2, "空间感知与预判": 1.7, "比赛阅读能力": 1.7,
        "常规射门": 1.0, "不停球射门": 1.0, "挑射": 1.0, "远射": 1.0, "凌空触球": 1.0, "射门力量": 1.0, "点球": 1.0, "任意球": 1.0,
        "头球攻门": 1.4, "解围": 1.4,
        "盘带过人": 1.0, "推进突破": 1.4, "变向灵活性": 1.0, "跑位": 1.0, "无球进攻嗅觉": 1.0, "越位意识": 1.4,
        "一对一盯防": 1.4, "抢断": 1.2, "铲球": 1.2, "线路封堵": 1.4, "内收补位意识": 1.4, "防守选位": 1.4,
        "绝对速度": 1.2, "爆发速度": 1.0, "加速摆脱": 1.0, "回追防守": 1.2, "弹跳/制空": 1.4, "主动对抗": 1.4, "被动对抗": 1.4, "体能耐力": 1.2,
        "抵抗伤病": 1.0, "大场面属性": 1.0, "赛场情绪": 1.0
    },
    "边后卫 (FB)": {
        "短传衔接": 1.2, "长传转移": 1.2, "直塞": 1.0, "传中": 1.4, "弧线球": 1.2, "外脚背": 1.0, "高压出球": 1.7,
        "第一脚触球": 1.4, "触球精度": 1.0, "控球能力": 1.0, "护球": 1.4, "逆足均衡度": 1.0,
        "出球视野/创造力": 1.0, "瞬间反应": 1.2, "空间感知与预判": 1.7, "比赛阅读能力": 1.7,
        "常规射门": 1.0, "不停球射门": 1.0, "挑射": 1.0, "远射": 1.0, "凌空触球": 1.0, "射门力量": 1.0, "点球": 1.0, "任意球": 1.0,
        "头球攻门": 1.0, "解围": 1.2,
        "盘带过人": 1.2, "推进突破": 1.7, "变向灵活性": 1.2, "跑位": 1.2, "无球进攻嗅觉": 1.0, "越位意识": 1.2,
        "一对一盯防": 1.4, "抢断": 1.2, "铲球": 1.2, "线路封堵": 1.2, "内收补位意识": 1.4, "防守选位": 1.4,
        "绝对速度": 1.2, "爆发速度": 1.2, "加速摆脱": 1.2, "回追防守": 1.4, "弹跳/制空": 1.2, "主动对抗": 1.2, "被动对抗": 1.2, "体能耐力": 1.4,
        "抵抗伤病": 1.0, "大场面属性": 1.0, "赛场情绪": 1.0
    },
    "防守型中场 (DM)": {
        "短传衔接": 1.2, "长传转移": 1.2, "直塞": 1.0, "传中": 1.0, "弧线球": 1.0, "外脚背": 1.0, "高压出球": 1.7,
        "第一脚触球": 1.7, "触球精度": 1.0, "控球能力": 1.0, "护球": 1.7, "逆足均衡度": 1.0,
        "出球视野/创造力": 1.0, "瞬间反应": 1.2, "空间感知与预判": 1.7, "比赛阅读能力": 1.7,
        "常规射门": 1.0, "不停球射门": 1.0, "挑射": 1.0, "远射": 1.0, "凌空触球": 1.0, "射门力量": 1.0, "点球": 1.0, "任意球": 1.0,
        "头球攻门": 1.0, "解围": 1.4,
        "盘带过人": 1.0, "推进突破": 1.7, "变向灵活性": 1.0, "跑位": 1.0, "无球进攻嗅觉": 1.0, "越位意识": 1.2,
        "一对一盯防": 1.4, "抢断": 1.4, "铲球": 1.2, "线路封堵": 1.4, "内收补位意识": 1.4, "防守选位": 1.4,
        "绝对速度": 1.0, "爆发速度": 1.2, "加速摆脱": 1.0, "回追防守": 1.2, "弹跳/制空": 1.2, "主动对抗": 1.4, "被动对抗": 1.4, "体能耐力": 1.4,
        "抵抗伤病": 1.0, "大场面属性": 1.0, "赛场情绪": 1.0
    },
    "组织型中场 (CM)": {
        "短传衔接": 1.7, "长传转移": 1.4, "直塞": 1.4, "传中": 1.0, "弧线球": 1.0, "外脚背": 1.0, "高压出球": 1.7,
        "第一脚触球": 1.7, "触球精度": 1.2, "控球能力": 1.4, "护球": 1.7, "逆足均衡度": 1.2,
        "出球视野/创造力": 1.7, "瞬间反应": 1.0, "空间感知与预判": 1.7, "比赛阅读能力": 1.7,
        "常规射门": 1.0, "不停球射门": 1.0, "挑射": 1.0, "远射": 1.2, "凌空触球": 1.0, "射门力量": 1.0, "点球": 1.0, "任意球": 1.0,
        "头球攻门": 1.0, "解围": 1.0,
        "盘带过人": 1.2, "推进突破": 1.4, "变向灵活性": 1.0, "跑位": 1.0, "无球进攻嗅觉": 1.0, "越位意识": 1.0,
        "一对一盯防": 1.2, "抢断": 1.2, "铲球": 1.0, "线路封堵": 1.2, "内收补位意识": 1.2, "防守选位": 1.2,
        "绝对速度": 1.0, "爆发速度": 1.0, "加速摆脱": 1.0, "回追防守": 1.2, "弹跳/制空": 1.0, "主动对抗": 1.2, "被动对抗": 1.2, "体能耐力": 1.4,
        "抵抗伤病": 1.0, "大场面属性": 1.0, "赛场情绪": 1.0
    },
    "攻击型中场 (AM)": {
        "短传衔接": 1.4, "长传转移": 1.2, "直塞": 1.4, "传中": 1.0, "弧线球": 1.2, "外脚背": 1.2, "高压出球": 1.7,
        "第一脚触球": 1.7, "触球精度": 1.2, "控球能力": 1.2, "护球": 1.7, "逆足均衡度": 1.2,
        "出球视野/创造力": 1.4, "瞬间反应": 1.0, "空间感知与预判": 1.7, "比赛阅读能力": 1.7,
        "常规射门": 1.2, "不停球射门": 1.2, "挑射": 1.0, "远射": 1.2, "凌空触球": 1.0, "射门力量": 1.0, "点球": 1.0, "任意球": 1.2,
        "头球攻门": 1.0, "解围": 1.0,
        "盘带过人": 1.4, "推进突破": 1.7, "变向灵活性": 1.2, "跑位": 1.2, "无球进攻嗅觉": 1.2, "越位意识": 1.0,
        "一对一盯防": 1.0, "抢断": 1.0, "铲球": 1.0, "线路封堵": 1.0, "内收补位意识": 1.0, "防守选位": 1.0,
        "绝对速度": 1.0, "爆发速度": 1.2, "加速摆脱": 1.2, "回追防守": 1.0, "弹跳/制空": 1.0, "主动对抗": 1.0, "被动对抗": 1.2, "体能耐力": 1.2,
        "抵抗伤病": 1.0, "大场面属性": 1.0, "赛场情绪": 1.0
    },
    "边锋 (W/M)": {
        "短传衔接": 1.2, "长传转移": 1.0, "直塞": 1.4, "传中": 1.2, "弧线球": 1.4, "外脚背": 1.0, "高压出球": 1.7,
        "第一脚触球": 1.7, "触球精度": 1.2, "控球能力": 1.2, "护球": 1.4, "逆足均衡度": 1.2,
        "出球视野/创造力": 1.4, "瞬间反应": 1.0, "空间感知与预判": 1.7, "比赛阅读能力": 1.7,
        "常规射门": 1.2, "不停球射门": 1.2, "挑射": 1.0, "远射": 1.0, "凌空触球": 1.0, "射门力量": 1.0, "点球": 1.0, "任意球": 1.0,
        "头球攻门": 1.0, "解围": 1.0,
        "盘带过人": 1.7, "推进突破": 1.7, "变向灵活性": 1.4, "跑位": 1.2, "无球进攻嗅觉": 1.2, "越位意识": 1.0,
        "一对一盯防": 1.0, "抢断": 1.0, "铲球": 1.0, "线路封堵": 1.0, "内收补位意识": 1.0, "防守选位": 1.0,
        "绝对速度": 1.2, "爆发速度": 1.4, "加速摆脱": 1.2, "回追防守": 1.2, "弹跳/制空": 1.0, "主动对抗": 1.0, "被动对抗": 1.2, "体能耐力": 1.2,
        "抵抗伤病": 1.0, "大场面属性": 1.0, "赛场情绪": 1.0
    },
    "拖后前锋 (SS)": {
        "短传衔接": 1.7, "长传转移": 1.0, "直塞": 1.7, "传中": 1.0, "弧线球": 1.2, "外脚背": 1.0, "高压出球": 1.7,
        "第一脚触球": 1.7, "触球精度": 1.4, "控球能力": 1.4, "护球": 1.4, "逆足均衡度": 1.0,
        "出球视野/创造力": 1.4, "瞬间反应": 1.0, "空间感知与预判": 1.7, "比赛阅读能力": 1.7,
        "常规射门": 1.4, "不停球射门": 1.2, "挑射": 1.0, "远射": 1.0, "凌空触球": 1.0, "射门力量": 1.0, "点球": 1.0, "任意球": 1.0,
        "头球攻门": 1.0, "解围": 1.0,
        "盘带过人": 1.7, "推进突破": 1.7, "变向灵活性": 1.2, "跑位": 1.4, "无球进攻嗅觉": 1.4, "越位意识": 1.0,
        "一对一盯防": 1.0, "抢断": 1.0, "铲球": 1.0, "线路封堵": 1.0, "内收补位意识": 1.0, "防守选位": 1.0,
        "绝对速度": 1.0, "爆发速度": 1.2, "加速摆脱": 1.0, "回追防守": 1.0, "弹跳/制空": 1.0, "主动对抗": 1.0, "被动对抗": 1.2, "体能耐力": 1.0,
        "抵抗伤病": 1.0, "大场面属性": 1.0, "赛场情绪": 1.0
    },
    "中锋 (CF)": {
        "短传衔接": 1.2, "长传转移": 1.0, "直塞": 1.0, "传中": 1.0, "弧线球": 1.2, "外脚背": 1.0, "高压出球": 1.4,
        "第一脚触球": 1.7, "触球精度": 1.2, "控球能力": 1.0, "护球": 1.7, "逆足均衡度": 1.2,
        "出球视野/创造力": 1.0, "瞬间反应": 1.2, "空间感知与预判": 1.7, "比赛阅读能力": 1.7,
        "常规射门": 1.4, "不停球射门": 1.4, "挑射": 1.2, "远射": 1.2, "凌空触球": 1.2, "射门力量": 1.2, "点球": 1.0, "任意球": 1.0,
        "头球攻门": 1.4, "解围": 1.0,
        "盘带过人": 1.2, "推进突破": 1.7, "变向灵活性": 1.0, "跑位": 1.4, "无球进攻嗅觉": 1.4, "越位意识": 1.2,
        "一对一盯防": 1.0, "抢断": 1.0, "铲球": 1.0, "线路封堵": 1.0, "内收补位意识": 1.0, "防守选位": 1.0,
        "绝对速度": 1.0, "爆发速度": 1.2, "加速摆脱": 1.0, "回追防守": 1.0, "弹跳/制空": 1.4, "主动对抗": 1.4, "被动对抗": 1.2, "体能耐力": 1.0,
        "抵抗伤病": 1.0, "大场面属性": 1.0, "赛场情绪": 1.0
    }
}

# 维度详细说明文案 (去除了括号里的“天花板”等修饰，更新了名称)
ABILITY_DESC_MD = """
**一、传球类（1–7）**

1. **短传衔接**：无压迫或轻度压迫下的近距离短传、一脚出球精度与节奏。重点是连续配合、小范围传切的稳定度。
2. **长传转移**：中远距离横向、纵向长传的落点精度。用来转移进攻方向、找远端队友，含转移球与过顶球。
3. **直塞**：穿透防线的向前渗透传球。评估传球时机、线路选择、力度控制，能否给到队友单刀、半单刀。
4. **传中**：边路向禁区输送球。含低平球、高球、倒三角，衡量落点是否适配包抄队友。
5. **弧线球**：用弧线控制皮球轨迹，既用于传球绕开防守人，也用于弧线射门。评估弧线控制、轨迹与落点精度。
6. **外脚背**：用外脚背处理球，含外脚背传球与射门。评估动作熟练度、出球精度、力度控制。
7. **高压出球**：在对手贴身逼抢、狭小受限空间内的出球容错。重点看压迫下失误次数、能否合理把球摘出去。

**二、触球与持球类（8–12）**

8. **第一脚触球**：来球第一下的卸球、停球质量。能否把球停进可控范围，为后续传、射、带创造衔接条件。
9. **触球精度**：单次触球的质量，含拨、推、扣、卸球的轻重控制，以及不规则来球（反弹球、旋转球、半高球）的处理自然度。
10. **控球能力**：原地、低速状态下连续持球的稳定性，长时间把球留在脚下不丢失，低对抗、无冲刺环境下维持触球连续性。
11. **护球**：用身体隔开防守人，在贴身对抗、上抢干扰下守住球权。含背身持球场景。侧重身位卡位、对抗生存。
12. **逆足均衡度**：非惯用脚在传球、停球、射门、持球时的综合能力。逆足越强，左右脚选择越丰富。

**三、球商、视野、反应类（13–16）**

13. **出球视野/创造力**：发现隐蔽空档、想出非常规传球线路的能力。侧重 “能不能找到别人看不到的机会”，是传球思路层面。
14. **瞬间反应**：球发生变向、反弹、意外偏转时的神经反应速度，属生理反应层面，与球商无关。
15. **空间感知与预判**：预判球落点、对手跑动路线、即将出现的空当，提前占位、提前启动的能力，含把球传到空当里的意识。偏局部、动态。
16. **比赛阅读能力**：读懂场上局势、攻防节奏、对方阵型漏洞、战术意图与整体走向。偏全局、结构。

**四、射门与终结类（17–24）**

17. **常规射门**：接球调整后的常规射门。评估射正率、常规机会终结效率。
18. **不停球射门**：不做停球调整直接迎球射门，考研时机、发力、瞄准的同步性。
19. **挑射**：把球挑过出击门将的挑射，评估力度与高度控制。
20. **远射**：禁区外远距离射门，含发力、瞄准、绕开封堵的能力。
21. **凌空触球**：空中来球直接用身体部位处理，含凌空射门、凌空传球、凌空垫做、凌空卸球调整。评估时机、身体姿态、击球部位与力度。
22. **射门力量**：射门输出的球速，决定门将扑救难度。是纯物理属性，与瞄准精度分开评。
23. **点球**：点球点射门的稳定性、压力下的命中能力。
24. **任意球**：定位球直接射门，含弧线、下坠、绕墙、攻门框范围的综合能力。

**五、争顶与解围（25–26）**

25. **头球攻门**：进攻端头球抢点攻门，判断落点、控制方向与力度。
26. **解围**：危险区域把球清除到安全区域（含头顶、脚尖捅出、大脚清球）。不追求找队友，优先化解危机。

**六、进攻盘带、推进、无球（27–32）**

27. **盘带过人**：一对一面对防守人，靠技术动作完成摆脱、过人。单次动作的成败。
28. **推进突破**：持球纵向向前推进，持续带球冲击防线，含带球、选线、持续摆脱。是长距离连续扛进能力。
29. **变向灵活性**：狭小空间急停、扣球、转身、变向的灵巧度，侧重改变行进方向的敏捷。
30. **跑位**：无球时主动跑动拉扯防线、寻找接球空间的跑动选择。
31. **无球进攻嗅觉**：在进攻区域捕捉射门、补射、抢点机会的本能，对危险落点的敏感度。
32. **越位意识**：进攻端解读越位陷阱、适时启动；防守端统一防线、把控时机制造越位。双向属性，进攻球员只评反越位，防守球员只评造越位。

**七、防守技术与意识（33–38）**

33. **一对一盯防**：贴身跟防对手持球或无球人，限制接球、转身、带球。
34. **抢断**：合理时机上前争夺球权，从对手脚下把球抢下来（站立状态）。
35. **铲球**：倒地铲断的时机、控制、干净程度，兼顾断球与少吃牌。
36. **线路封堵**：预判皮球飞行路线并主动阻挡，含截传球线路、封射门线路。考时机、站位、成功率。
37. **内收补位意识**：队友离开防守位置时主动向内收拢、填补空当。
38. **防守选位**：防守时站位选择，平衡盯人、保护空间、兼顾内部空档。

**八、速度、爆发、身体（39–46）**

39. **绝对速度**：无球冲刺能达到的最高奔跑速度。
40. **爆发速度**：静止或低速瞬间启动加速，无球起步爆发力。
41. **加速摆脱**：带球状态下加速，靠启动拉开与防守人的距离。与 40 的差别在于 “带球加速”。
42. **回追防守**：落后于对手时向后、侧向冲刺追赶与干扰。不只看速度，兼顾追防选位与干扰质量。
43. **弹跳/制空**：起跳高度、空中停留时间，争夺空中球的身体基础。
44. **主动对抗**：主动发力卡位、顶靠、争抢身位，主动争夺空间。
45. **被动对抗**：被撞击、挤压时稳住重心不失去身位、不被挤开的扛冲击能力。
46. **体能耐力**：长时间高强度跑动、反复冲刺，保持动作质量直到比赛后段。

**九、特质兑现组（47–49）**

47. **抵抗伤病**：耐伤程度、受伤概率与恢复速度，影响稳定出场。
48. **大场面属性**：淘汰赛、决赛等高压关键场次保持动作质量、稳定发挥的倾向；低分代表高压下失常。
49. **赛场情绪**：情绪管理能力，减少冲动犯规、头脑发热、动作变形；也包含对队友的鼓舞、对对手的震慑。
"""

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
    st.session_state.history_data = []
if "weight_editor_version" not in st.session_state:
    st.session_state.weight_editor_version = 0
if "selected_pos_name" not in st.session_state:
    st.session_state.selected_pos_name = None

# ==========================================
# 5. 数据库交互函数
# ==========================================
def load_history_from_db():
    try:
        response = supabase.table("players").select("*").execute()
        history = []
        for row in response.data:
            record = row["data"]
            record["id"] = row["id"] 
            record["timestamp"] = row["created_at"]
            history.append(record)
        return history
    except Exception as e:
        st.error(f"读取历史记录失败：{e}")
        return []

def save_history_to_db(player_data):
    try:
        supabase.table("players").delete().eq("player_name", player_data["player_name"]).execute()
        supabase.table("players").insert({
            "player_name": player_data["player_name"],
            "data": player_data
        }).execute()
        return True
    except Exception as e:
        st.error(f"保存失败：{e}")
        return False

def delete_history_from_db(record_id):
    try:
        supabase.table("players").delete().eq("id", record_id).execute()
        return True
    except Exception as e:
        st.error(f"删除失败：{e}")
        return False

def clear_all_history_from_db():
    try:
        supabase.table("players").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        return True
    except Exception as e:
        st.error(f"清空失败：{e}")
        return False

# 页面初次加载时，从数据库拉取最新历史
if "db_loaded" not in st.session_state:
    st.session_state.history_data = load_history_from_db()
    st.session_state.db_loaded = True

# ==========================================
# 6. 绘图与渲染
# ==========================================
def player_radar_plotly(player_name, abilities, rank_list, score_list, weighted_score_sum, weighted_max_sum, weighted_avg_score, fill_color="#87CEEB", edge_color="#000000"):
    
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

    dynamic_font_size = 13

    title_text = (
        f"<b>{player_name}</b><br>"
        f"加权总分: {weighted_score_sum:.1f} / {weighted_max_sum:.1f}<br>"
        f"综合评级: {score_to_rank(weighted_avg_score)}"
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 11.5]),
            angularaxis=dict(
                tickmode='array', tickvals=angles, ticktext=tick_texts,       
                tickfont=dict(size=dynamic_font_size, family="SimHei"), 
                gridcolor="rgba(0,0,0,0)", 
                linecolor="rgba(0,0,0,0)", 
                ticks="",        
                ticklen=0,       
                rotation=90, 
                direction="clockwise"
            ),
            bgcolor="white"
        ),
        title=dict(
            text=title_text,
            font=dict(size=18, family="SimHei", color="#333333"),
            x=0.02, y=0.98, xanchor="left", yanchor="top"
        ),
        showlegend=False, 
        margin=dict(l=220, r=220, t=100, b=100), 
        height=1100, paper_bgcolor="white"
    )
    return fig

def render_result(data):
    fig = player_radar_plotly(
        data["player_name"], data["abilities"], data["rank_list"], data["score_list"], 
        data["weighted_score_sum"], data["weighted_max_sum"], data["weighted_avg_score"],
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
    
    df_to_show = data['df_display']
    if isinstance(df_to_show, list):
        df_to_show = pd.DataFrame(df_to_show)
        
    st.dataframe(df_to_show, width="stretch", hide_index=True)
    return df_to_show

# ==========================================
# 7. 网页 UI 界面与交互
# ==========================================
st.set_page_config(page_title="足球球员评分看板", layout="wide")
st.title("⚽ 足球球员评分看板")

with st.expander("📖 点击查看：看板使用总说明", expanded=False):
    st.markdown("""
    1. 这是一个**评价非门将足球运动员**的看板。为使防守球员在某些维度分值过低，进而导致能力衡量不够直观，作者对部分进攻与防守维度做了整合，例如盘带过人/盯防。
    2. 评级的说明详见左侧边栏的 **“评级说明对照表”**。
    3. **分值与评级**：分值范围为0-11，评级范围为H-X，其中雷达图的白色基准线为 10 分，若某维度达到 10.5 (S+) 或 11 (X)，图形将会**超出边缘**。
    4. **位置权重预设**：左侧边栏新增了一键载入不同位置权重预设的功能，可大幅节省您的调参时间。
    5. **云端记录**：数据已接入云端数据库并开启**账号隔离**。注册登录后，历史记录将永久保存且不同账号互相独立。
    6. **维度排版**：雷达图外围维度严格按照“传球-触球-球商-射门-争顶-进攻-防守-身体-特质”的顺序从正上方顺时针排布。
    """)

with st.sidebar:
    # 显示当前登录的邮箱及退出按钮
    st.success(f"👤 已登录：\n{st.session_state.sb_session.user.email}")
    if st.button("🚪 退出登录", use_container_width=True):
        supabase.auth.sign_out()
        del st.session_state.sb_session
        st.rerun()
    st.markdown("---")

    st.header("⚙️ 看板配置")
    
    if st.button("🔄 一键重置打分", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ["history_data", "db_loaded", "sb_session", "weight_editor_version"]:
                del st.session_state[key]
        st.session_state.ability_text = "\n".join(DEFAULT_ABILITIES)
        st.session_state.selected_pos_name = None
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
        st.caption("点击下方位置，一键载入标准权重：")
        pos_names = list(POSITION_PRESETS.keys())
        col_btns = st.columns(2) 
        for i, pos in enumerate(pos_names):
            with col_btns[i % 2]:
                if st.button(pos, key=f"btn_{pos}", use_container_width=True):
                    st.session_state.selected_pos_name = pos
                    st.session_state.weight_editor_version += 1
                    st.rerun()
                    
        default_weights = [1.0] * len(current_abilities)
        if st.session_state.selected_pos_name:
            preset = POSITION_PRESETS[st.session_state.selected_pos_name]
            for i, dim in enumerate(current_abilities):
                default_weights[i] = preset.get(dim, 1.0)

        df_weights = pd.DataFrame({"维度": current_abilities, "权重": default_weights})
        editor_key_w = f"weight_editor_{hash(tuple(current_abilities))}_v{st.session_state.weight_editor_version}"
        
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

    with st.expander("5. 维度详细说明", expanded=False):
        st.markdown(ABILITY_DESC_MD)
        
    with st.expander("📁 历史记录管理", expanded=True):
        if not st.session_state.history_data:
            st.info("暂无历史记录。")
        else:
            if st.button("🗑️ 清空所有历史记录", use_container_width=True):
                if clear_all_history_from_db():
                    st.session_state.history_data = []
                    st.session_state.has_generated = False
                    st.session_state.view_record = None
                    st.rerun()
                
            for idx, record in enumerate(reversed(st.session_state.history_data)):
                real_idx = len(st.session_state.history_data) - 1 - idx
                col_load, col_del = st.columns([5, 1])
                
                with col_load:
                    if st.button(f"👤 {record['player_name']}", key=f"load_{idx}", use_container_width=True):
                        st.session_state.view_record = record
                        st.session_state.has_generated = True
                        st.rerun()
                with col_del:
                    if st.button("❌", key=f"del_{idx}", help="删除此记录"):
                        if delete_history_from_db(record["id"]):
                            st.session_state.history_data.pop(real_idx)
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

if st.session_state.get("has_generated", False):
    st.markdown("---")
    
    if "save_msg" in st.session_state:
        st.success(st.session_state.save_msg)
        del st.session_state.save_msg

    if st.session_state.get("view_record"):
        data_to_show = st.session_state.view_record
        df_display = render_result(data_to_show)
        st.info(f"📂 正在查看历史记录：{data_to_show['player_name']} (保存于 {data_to_show['timestamp']})")
    else:
        data_to_show = st.session_state.current_data
        df_display = render_result(data_to_show)
        
        col_a, col_b = st.columns([1, 4])
        with col_a:
            if st.button("💾 保存当前球员", type="primary"):
                record_to_save = {
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
                
                if save_history_to_db(record_to_save):
                    st.session_state.history_data = load_history_from_db()
                    st.session_state.save_msg = "✅ 已保存到云端数据库！"
                    st.rerun() 
    
    st.markdown("### 📥 导出数据表")
    csv_bytes = df_display.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label="📊 下载评分数据 (CSV)",
        data=csv_bytes,
        file_name=f"{data_to_show['player_name']}_评分数据.csv",
        mime="text/csv",
        use_container_width=False
    )
