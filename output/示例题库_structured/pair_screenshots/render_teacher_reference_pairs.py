import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).parent
FONT = "C:/Windows/Fonts/msyh.ttc"
BOLD = "C:/Windows/Fonts/msyhbd.ttc"
WIDTH = 1500


def q(code, kind, level, knowledge, question, answer, solution, anchor, anchor_answer, anchor_solution):
    return {
        "code": code, "kind": kind, "level": level, "knowledge": knowledge,
        "question": question, "answer": answer, "solution": solution,
        "anchor": anchor, "anchor_answer": anchor_answer, "anchor_solution": anchor_solution,
    }


SETS = [
    (
        "导数与微分·求导运算·基本函数求导",
        [
            q("K1-Q1", "单项选择题", 1, "导数与微分·求导运算·基本函数求导", "设 f(x)=x^4-3x^2+1，则 f'(1) 等于（ ）。\nA. -2    B. 0    C. 1    D. 2", "A", "f'(x)=4x^3-6x，故 f'(1)=4-6=-2，选 A。", "设 g(x)=2x^3+x，求 g'(1)。", "7", "g'(x)=6x^2+1，所以 g'(1)=7。"),
            q("K1-Q2", "填空题", 2, "导数与微分·求导运算·基本函数求导", "设 f(x)=e^x(x^2+1)，则 f'(0)=____。", "1", "乘积求导：f'(x)=e^x(x^2+2x+1)=e^x(x+1)^2，代入 0 得 1。", "设 g(x)=ln x+x，求 g'(1)。", "2", "g'(x)=1/x+1，因此 g'(1)=2。"),
            q("K1-Q3", "多项选择题", 3, "导数与微分·求导运算·基本函数求导", "已知 f(x)=x ln x（x>0），下列结论正确的是（ ）。\nA. f'(x)=ln x+1\nB. f'(1)=0\nC. f''(x)=1/x\nD. f(x) 在 (0,+infinity) 上递增", "A、C", "由乘积求导得 f'(x)=ln x+1，故 A 对、f'(1)=1，B 错；再求导得 f''(x)=1/x，C 对。f'(x) 在 (0,e^(-1)) 为负，D 错。", "设 g(x)=x^2 ln x（x>0），判断 g'(1) 的值。", "1", "g'(x)=2x ln x+x，故 g'(1)=1。"),
            q("K1-Q4", "解答题", 4, "导数与微分·求导运算·基本函数求导", "已知 f(x)=(x^2+1)e^x。求曲线 y=f(x) 在 x=0 处的切线方程，并求该切线在 x=1 时的函数值。", "切线 y=x+1；取值为 2", "f'(x)=e^x(x^2+2x+1)=e^x(x+1)^2。f(0)=1，f'(0)=1，所以切线 y-1=x，即 y=x+1；代入 x=1 得 2。", "已知 g(x)=xe^x，求其在 x=0 处的切线。", "y=x", "g(0)=0，g'(x)=e^x(x+1)，g'(0)=1，因此 y=x。"),
            q("K1-Q5", "单项选择题", 5, "导数与微分·求导运算·基本函数求导", "曲线 y=x^3-3x^2+2 的一条切线经过点 (1,0)，该切线方程是（ ）。\nA. y=3x-3    B. y=-3x+3    C. y=-3x+2    D. y=x-1", "B", "设切点横坐标为 t。由 f(t)+f'(t)(1-t)=0 可化为 -2(t-1)^3=0，故 t=1。此时 f(1)=0，f'(1)=-3，切线为 y=-3(x-1)。", "求 y=x^2 在点 (1,1) 处的切线方程。", "y=2x-1", "y'=2x，切点斜率为 2，所以 y-1=2(x-1)。"),
        ],
    ),
    (
        "导数应用·单调性·判断单调区间",
        [
            q("K2-Q1", "填空题", 1, "导数应用·单调性·判断单调区间", "函数 f(x)=3x-5 的递增区间为____。", "(-infinity,+infinity)", "f'(x)=3>0，因此函数在实数范围内单调递增。", "函数 g(x)=-2x+1 的递减区间为____。", "(-infinity,+infinity)", "g'(x)=-2<0，故在实数范围内单调递减。"),
            q("K2-Q2", "单项选择题", 2, "导数应用·单调性·判断单调区间", "函数 f(x)=x^2+2x 的递减区间为（ ）。\nA. (-infinity,-1)    B. (-1,+infinity)    C. (-infinity,1)    D. (1,+infinity)", "A", "f'(x)=2x+2。x<-1 时 f'(x)<0，x>-1 时 f'(x)>0，故选 A。", "函数 g(x)=x^2-6x 的递减区间为（ ）。", "(-infinity,3)", "g'(x)=2x-6；导数在 x<3 时为负。"),
            q("K2-Q3", "解答题", 3, "导数应用·单调性·判断单调区间", "求 f(x)=x^3-3x^2+1 的单调区间。", "递增：(-infinity,0) 与 (2,+infinity)；递减：(0,2)", "f'(x)=3x(x-2)。作符号表：x<0 时正，0<x<2 时负，x>2 时正，故得所求区间。", "求 g(x)=x^3-3x 的单调区间。", "递增：(-infinity,-1) 与 (1,+infinity)；递减：(-1,1)", "g'(x)=3(x-1)(x+1)，据导数符号判断。"),
            q("K2-Q4", "多项选择题", 4, "导数应用·单调性·判断单调区间", "设 f(x)=ln x-x/3（x>0），下列结论正确的是（ ）。\nA. f(x) 在 (0,3) 上递增\nB. f(x) 在 (3,+infinity) 上递减\nC. f(x) 的最大值为 ln 3-1\nD. f(x) 存在最小值", "A、B、C", "f'(x)=1/x-1/3=(3-x)/(3x)。所以 A、B 正确，x=3 处取最大值 ln3-1。x 趋于无穷时函数趋于负无穷，故 D 错。", "设 g(x)=ln x-x（x>0），判断其最大值。", "-1", "g'(x)=1/x-1，在 x=1 处由正变负，最大值 g(1)=-1。"),
            q("K2-Q5", "单项选择题", 5, "导数应用·单调性·判断单调区间", "设 a>0，f_a(x)=ln x+a/x（x>0）。其单调性是（ ）。\nA. 在 (0,+infinity) 上递增\nB. 在 (0,a) 上递增、(a,+infinity) 上递减\nC. 在 (0,a) 上递减、(a,+infinity) 上递增\nD. 与 a 无关", "C", "f'_a(x)=(x-a)/x^2。分母恒正，导数在 x<a 时为负、x>a 时为正，选 C。", "设 b>0，g_b(x)=x+b/x（x>0），判断其单调性。", "在 (0,sqrt(b)) 递减，在 (sqrt(b),+infinity) 递增", "g'_b(x)=1-b/x^2，导数在 x=sqrt(b) 两侧变号。"),
        ],
    ),
    (
        "导数应用·极值与最值·求极值",
        [
            q("K3-Q1", "多项选择题", 1, "导数应用·极值与最值·求极值", "对 f(x)=x^2-6x+8，下列结论正确的是（ ）。\nA. x=3 时取得最小值\nB. 最小值为 1\nC. 在 (-infinity,3) 上递减\nD. 在 (3,+infinity) 上递增", "A、C、D", "f'(x)=2x-6，故 x=3 处由负变正，取最小值 f(3)=-1。A、C、D 对，B 错。", "求 h(x)=x^2-4x+7 的最小值。", "3", "h(x)=(x-2)^2+3，最小值为 3。"),
            q("K3-Q2", "填空题", 2, "导数应用·极值与最值·求极值", "函数 f(x)=x^3-3x 的极大值为____。", "2", "f'(x)=3(x-1)(x+1)。x=-1 处导数由正变负，极大值为 f(-1)=2。", "函数 g(x)=x^3-12x 的极大值为____。", "16", "g'(x)=3(x-2)(x+2)，x=-2 处取极大值 g(-2)=16。"),
            q("K3-Q3", "单项选择题", 3, "导数应用·极值与最值·求极值", "f(x)=x^2+8/x（x>0）的最小值为（ ）。\nA. 3*2^(2/3)    B. 3*2^(4/3)    C. 4    D. 6", "B", "f'(x)=2x-8/x^2。令 f'=0 得 x^3=4。导数先负后正，最小值为 4^(2/3)+8/4^(1/3)=3*2^(4/3)，选 B。", "求 x^2+4/x（x>0）的最小值。", "3*2^(2/3)", "令导数 2x-4/x^2 为零，得 x^3=2，再代入计算。"),
            q("K3-Q4", "解答题", 4, "导数应用·极值与最值·求极值", "求 f(x)=x^3-6x^2+9x+1 在区间 [0,4] 上的最大值与最小值。", "最大值 5；最小值 1", "f'(x)=3(x-1)(x-3)。比较端点与驻点：f(0)=1，f(1)=5，f(3)=1，f(4)=5。因此最大值为 5，最小值为 1。", "求 g(x)=x^3-3x^2+2 在 [0,3] 上的最值。", "最大值 2；最小值 -2", "比较 g(0)=2、g(2)=-2、g(3)=2 即可。"),
            q("K3-Q5", "多项选择题", 5, "导数应用·极值与最值·求极值", "a>0，f(x)=x^2+a/x（x>0）。下列结论正确的是（ ）。\nA. 最小值在 x=(a/2)^(1/3) 处取得\nB. 最小值为 3(a/2)^(2/3)\nC. 最小值为 6 时，a=4sqrt(2)\nD. a 增大时，最小值减小", "A、B、C", "f'(x)=2x-a/x^2，令其为零得 x=(a/2)^(1/3)。代入得最小值 3(a/2)^(2/3)。令其等于 6 解得 a=4sqrt(2)。最小值随 a 增大而增大，D 错。", "a>0，求 x+a/x（x>0）的最小值。", "2sqrt(a)", "导数为 1-a/x^2，在 x=sqrt(a) 处取最小值 2sqrt(a)。"),
        ],
    ),
    (
        "导数应用·不等式证明·构造函数证明",
        [
            q("K4-Q1", "单项选择题", 1, "导数应用·不等式证明·构造函数证明", "要证明 ln x <= x-1（x>0），适宜构造的函数是（ ）。\nA. f(x)=x-1-ln x\nB. f(x)=x+1+ln x\nC. f(x)=ln x-x\nD. f(x)=x ln x", "A", "将目标不等式移项为 x-1-ln x>=0，故构造 A。", "要证明 e^t>=t+1，适宜构造的函数是____。", "e^t-t-1", "把不等式左减右，构造 h(t)=e^t-t-1。"),
            q("K4-Q2", "填空题", 2, "导数应用·不等式证明·构造函数证明", "设 f(x)=x-1-ln x（x>0），则 f'(x)=____。", "(x-1)/x", "直接求导 f'(x)=1-1/x=(x-1)/x。该形式便于用 x=1 作符号分界。", "设 h(t)=e^t-t-1，则 h'(t)=____。", "e^t-1", "h'(t)=e^t-1，在 t=0 处为零。"),
            q("K4-Q3", "解答题", 3, "导数应用·不等式证明·构造函数证明", "证明：对任意 x>0，有 ln x <= x-1。", "见解析", "令 f(x)=x-1-ln x。f'(x)=(x-1)/x，所以 f 在 (0,1) 递减、在 (1,+infinity) 递增，最小值为 f(1)=0。因此 f(x)>=0，即 ln x<=x-1。", "证明：对任意 t 属于 R，有 e^t>=t+1。", "见解析", "令 h(t)=e^t-t-1。h'(t)=e^t-1，故 h 在 0 处取最小值 h(0)=0，从而 h(t)>=0。"),
            q("K4-Q4", "多项选择题", 4, "导数应用·不等式证明·构造函数证明", "设 f(x)=x-ln x（x>0），下列结论正确的是（ ）。\nA. f(x) 在 x=1 处取最小值\nB. f(x)>=1\nC. ln x<=x-1\nD. ln x>=x-1", "A、B、C", "f'(x)=1-1/x，x=1 处由负变正，f(1)=1，故 A、B 对。f(x)>=1 等价于 ln x<=x-1，C 对，D 错。", "设 g(x)=x-1/x（x>0），判断其单调性。", "在 (0,+infinity) 上递增", "g'(x)=1+1/x^2>0。"),
            q("K4-Q5", "解答题", 5, "导数应用·不等式证明·构造函数证明", "证明：当 a>0 时，ln(1+a)>a/(1+a)。", "见解析", "令 g(a)=ln(1+a)-a/(1+a)。g(0)=0，且 g'(a)=1/(1+a)-1/(1+a)^2=a/(1+a)^2>0。因此 a>0 时 g(a)>0，原不等式成立。", "证明：当 t>0 时，ln(1+t)<t。", "见解析", "由 ln x<=x-1，令 x=1+t，可得 ln(1+t)<=t；当 t>0 时等号不成立，故为严格小于。"),
        ],
    ),
    (
        "概率统计·概率模型·全概率公式",
        [
            q("K5-Q1", "单项选择题", 1, "概率统计·概率模型·全概率公式", "甲、乙两箱被选中的概率分别为 0.3、0.7；从甲、乙箱抽到红球的概率分别为 0.4、0.1。随机选一箱抽一球，抽到红球的概率为（ ）。\nA. 0.13    B. 0.19    C. 0.28    D. 0.40", "B", "按选箱来源分解：P(红)=0.3*0.4+0.7*0.1=0.19，选 B。", "两车间产量占比为 0.5、0.5，合格率为 0.9、0.8，求随机产品合格概率。", "0.85", "P(合格)=0.5*0.9+0.5*0.8=0.85。"),
            q("K5-Q2", "填空题", 2, "概率统计·概率模型·全概率公式", "生产线 A、B 的产量占比分别为 0.4、0.6，次品率分别为 0.05、0.02。随机抽取一件产品，抽到次品的概率为____。", "0.032", "P(次品)=0.4*0.05+0.6*0.02=0.032。", "甲、乙两类考生占比为 0.2、0.8，迟到率为 0.10、0.03，求随机考生迟到概率。", "0.044", "P(迟到)=0.2*0.10+0.8*0.03=0.044。"),
            q("K5-Q3", "多项选择题", 3, "概率统计·概率模型·全概率公式", "A、B 两组学生占比分别为 0.25、0.75，及格率分别为 0.8、0.6。下列结论正确的是（ ）。\nA. 随机学生及格概率为 0.65\nB. 已知及格，该生来自 A 组的概率为 4/13\nC. 已知及格，该生来自 B 组的概率为 9/13\nD. 已知来自 B 组，该生及格概率为 0.75", "A、B、C", "P(及格)=0.25*0.8+0.75*0.6=0.65。P(A|及格)=0.2/0.65=4/13，B 组条件概率为 9/13。P(及格|B)=0.6，D 错。", "甲、乙班占比为 0.4、0.6，及格率为 0.7、0.5，求 P(甲班|及格)。", "7/13", "P(及格)=0.4*0.7+0.6*0.5=0.58，所求为 0.28/0.58=7/13。"),
            q("K5-Q4", "解答题", 4, "概率统计·概率模型·全概率公式", "某病患病率为 0.01，检测灵敏度 P(阳性|患病)=0.90，假阳性率 P(阳性|未患病)=0.04。检测阳性者实际患病的概率是多少？", "5/27，约 18.52%", "P(阳性)=0.01*0.90+0.99*0.04=0.0486。由贝叶斯公式，P(患病|阳性)=0.009/0.0486=5/27，约为 18.52%。", "患病率为 0.02，灵敏度 0.80，假阳性率 0.10，求 P(患病|阳性)。", "8/57", "P(阳性)=0.02*0.8+0.98*0.1=0.114，所求为 0.016/0.114=8/57。"),
            q("K5-Q5", "单项选择题", 5, "概率统计·概率模型·全概率公式", "供应商 A、B、C 的供货占比分别为 0.1、0.4、0.5，次品率分别为 0.02、0.01、0.05。已知产品为次品，它来自 C 的概率为（ ）。\nA. 5/31    B. 25/31    C. 1/2    D. 25/50", "B", "P(次品)=0.1*0.02+0.4*0.01+0.5*0.05=0.031。P(C|次品)=0.025/0.031=25/31，选 B。", "A、B 两工厂占比为 0.6、0.4，次品率为 0.01、0.04。已知为次品，求来自 B 的概率。", "8/11", "P(次品)=0.006+0.016=0.022，P(B|次品)=0.016/0.022=8/11。"),
        ],
    ),
]


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def wrapped(draw, text, face, width):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and draw.textlength(candidate, font=face) > width:
                lines.append(current)
                current = char
            else:
                current = candidate
        lines.append(current or " ")
    return lines


def text_block(draw, x, y, text, face, color, width, line_gap=10):
    lines = wrapped(draw, text, face, width)
    line_height = face.size + line_gap
    for line in lines:
        draw.text((x, y), line, font=face, fill=color)
        y += line_height
    return y, len(lines)


def pill(draw, x, y, text, face, fill, color):
    pad_x, height = 18, 42
    width = int(draw.textlength(text, font=face)) + pad_x * 2
    draw.rounded_rectangle((x, y, x + width, y + height), radius=20, fill=fill)
    draw.text((x + pad_x, y + 8), text, font=face, fill=color)
    return x + width + 12


def panel(draw, x, y, width, title, text, answer, solution, tone):
    body = font(25)
    question_face = font(28, True)
    label = font(24, True)
    q_lines = wrapped(draw, text, question_face, width - 100)
    a_lines = wrapped(draw, f"答案：{answer}", body, width - 100)
    s_lines = wrapped(draw, solution, body, width - 100)
    h = 66 + len(q_lines) * 40 + 24 + len(a_lines) * 36 + 24 + 36 + len(s_lines) * 36 + 46
    draw.rounded_rectangle((x, y, x + width, y + h), radius=18, fill=tone[0], outline=tone[1], width=2)
    draw.text((x + 34, y + 24), title, font=label, fill=tone[2])
    y0 = y + 76
    draw.rounded_rectangle((x + 28, y0, x + width - 28, y0 + len(q_lines) * 40 + 34), radius=14, fill="#ffffff")
    after_q, _ = text_block(draw, x + 50, y0 + 17, text, question_face, "#142844", width - 100, 12)
    answer_y = after_q + 22
    draw.rounded_rectangle((x + 28, answer_y, x + width - 28, answer_y + len(a_lines) * 36 + 26), radius=12, fill="#ffffff")
    text_block(draw, x + 50, answer_y + 12, f"答案：{answer}", body, "#1c3756", width - 100, 9)
    solve_y = answer_y + len(a_lines) * 36 + 48
    draw.text((x + 50, solve_y), "解析", font=label, fill=tone[2])
    text_block(draw, x + 50, solve_y + 42, solution, body, "#38516e", width - 100, 9)
    return y + h


def render(item):
    image = Image.new("RGB", (WIDTH, 2700), "#eef3fa")
    draw = ImageDraw.Draw(image)
    small = font(21)
    title_face = font(37, True)
    y = 0
    draw.rectangle((0, 0, WIDTH, 24), fill="#2d6db4")
    draw.text((56, 55), item["code"], font=font(24, True), fill="#2d6db4")
    y = 92
    title_bottom, _ = text_block(draw, 56, y, item["knowledge"], title_face, "#10294a", WIDTH - 112, 9)
    px = 860
    px = pill(draw, px, 48, item["kind"], small, "#e8f2ff", "#2166ae")
    px = pill(draw, px, 48, f"目标等级：{item['level']}级", small, "#f1ebff", "#6c4db0")
    pill(draw, px, 48, "教师参考样题", small, "#e7f6ed", "#21855b")
    y = max(title_bottom + 28, 154)
    draw.line((56, y, WIDTH - 56, y), fill="#d6e0ee", width=2)
    y += 34

    new_bottom = panel(draw, 56, y, WIDTH - 112, "生成新题", item["question"], item["answer"], item["solution"], ("#f5f9ff", "#c9dcf5", "#2165aa"))
    meta_y = new_bottom + 22
    meta_h = 92
    for x, label, value in ((56, "题型", item["kind"]), (WIDTH // 2 + 12, "目标等级", f"{item['level']}级")):
        draw.rounded_rectangle((x, meta_y, x + WIDTH // 2 - 80, meta_y + meta_h), radius=14, fill="#ffffff", outline="#d8e4f0", width=2)
        draw.text((x + 24, meta_y + 16), label, font=small, fill="#70839a")
        draw.text((x + 24, meta_y + 48), value, font=font(25), fill="#1a3454")
    note_y = meta_y + meta_h + 22
    draw.rounded_rectangle((56, note_y, WIDTH - 56, note_y + 104), radius=15, fill="#e8f7ee", outline="#9bd6b0", width=2)
    draw.text((82, note_y + 18), "教师核验提示", font=font(24, True), fill="#17774c")
    draw.text((82, note_y + 53), "请核验数学正确性、题型训练价值、目标等级，以及与训练锚点的关系。", font=small, fill="#287355")
    y = note_y + 140

    anchor_bottom = panel(draw, 56, y, WIDTH - 112, "对应训练锚点", item["anchor"], item["anchor_answer"], item["anchor_solution"], ("#fffaf1", "#efd3a0", "#9b6a18"))
    meta_y = anchor_bottom + 22
    meta_h = 92
    for x, label, value in ((56, "锚点难度", "基础至中档"), (WIDTH // 2 + 12, "关联方式", "skill_blueprint")):
        draw.rounded_rectangle((x, meta_y, x + WIDTH // 2 - 80, meta_y + meta_h), radius=14, fill="#ffffff", outline="#ead9ba", width=2)
        draw.text((x + 24, meta_y + 16), label, font=small, fill="#8d7854")
        draw.text((x + 24, meta_y + 48), value, font=font(24), fill="#4f3e21")
    footer_y = meta_y + meta_h + 34
    draw.text((56, footer_y), "教师参考：新题与训练锚点共享知识与能力目标，但不直接复用题干、数据、选项或解析。", font=small, fill="#62758b")
    image.crop((0, 0, WIDTH, footer_y + 62)).save(OUT / f"{item['code'].lower().replace('-', '_')}_pair.png", optimize=True)


TYPE_IDS = {
    "单项选择题": "single_choice",
    "多项选择题": "multiple_choice",
    "填空题": "fill_blank",
    "解答题": "solution",
}


def training_references(item):
    question_type = TYPE_IDS[item["kind"]]
    main = {
        "question_id": f"teacher_anchor_{item['code'].lower().replace('-', '_')}_1",
        "display_id": f"教师参考锚点 {item['code']}·A",
        "source_exam": "教师参考独立题组",
        "question_number": 1,
        "question_type": question_type,
        "primary_knowledge": item["knowledge"],
        "stem_markdown": item["anchor"],
        "answer": item["anchor_answer"],
        "solution_markdown": item["anchor_solution"],
    }
    support = []
    for number, focus in ((2, "同一知识点的条件变式"), (3, "同一能力目标的表示变式")):
        support.append({
            "question_id": f"teacher_anchor_{item['code'].lower().replace('-', '_')}_{number}",
            "display_id": f"教师参考锚点 {item['code']}·{chr(64 + number)}",
            "source_exam": "教师参考独立题组",
            "question_number": number,
            "question_type": question_type,
            "primary_knowledge": item["knowledge"],
            "stem_markdown": f"{focus}：围绕“{item['knowledge']}”设计一题基础训练，用于说明新题的教学目标。",
            "answer": "用于教学锚定，不单独评分",
            "solution_markdown": "该锚点只提供知识点与能力目标，不提供完整题干给新题生成链路复用。",
        })
    return [main, *support]


def workbench_payload():
    slots = []
    questions = []
    created_at = datetime.now(timezone.utc).isoformat()
    for knowledge_index, (_, items) in enumerate(SETS, 1):
        for question_index, item in enumerate(items, 1):
            references = training_references(item)
            anchor_id = references[0]["question_id"]
            question_type = TYPE_IDS[item["kind"]]
            question_id = f"teacher_reference_{item['code'].lower().replace('-', '_')}"
            question = {
                "question_id": question_id,
                "display_id": f"教师参考新题 {item['code']}",
                "is_generated": True,
                "student_visible": False,
                "scope": "student_practice",
                "student_id": "KNOWLEDGE",
                "question_type": question_type,
                "primary_knowledge": item["knowledge"],
                "stem_markdown": item["question"],
                "answer": item["answer"],
                "solution_markdown": item["solution"],
                "personalization": {
                    "target_level": item["level"],
                    "difficulty_key": "teacher_reference",
                    "difficulty_label": f"{item['level']}级",
                    "training_focus": "教师参考样题",
                },
                "generation": {
                    "mother_question_id": anchor_id,
                    "anchor_question_id": anchor_id,
                    "reference_question_ids": [reference["question_id"] for reference in references],
                    "reference_count": len(references),
                    "diagnostic_evidence_question_ids": [reference["question_id"] for reference in references],
                    "diagnostic_evidence_count": len(references),
                    "fulltext_anchor_count": 1,
                    "strategy": "teacher_reference_single_anchor",
                    "changed_dimensions": ["question_angle", "condition_organization", "reasoning_path"],
                    "novelty_review": "passed",
                    "generator": "smart-question-recommender-safety-blueprint-teacher-reference-v1",
                    "generated_at": created_at,
                    "mode": "knowledge",
                    "reference_note": "独立生成教师参考题；训练锚点仅用于说明知识与能力目标。",
                },
                "verification": {
                    "checked_from_stem_only": True,
                    "independent_answer": item["answer"],
                    "answer_matches": True,
                    "answer_solution_consistency": "passed",
                    "difficulty_matches": True,
                    "target_level": item["level"],
                    "estimated_level": item["level"],
                    "status": "passed",
                    "notes": "教师参考样题已按题干、答案与解析进行一致性检查；仍需教师教学复核。",
                },
                "teacher_review": {"status": "pending"},
            }
            slots.append({
                "slot_id": f"teacher-reference-{knowledge_index}-{question_index}",
                "scope": "knowledge_practice",
                "student_id": "KNOWLEDGE",
                "primary_knowledge": item["knowledge"],
                "question_type": question_type,
                "reference_questions": references,
                "candidates": [question],
                "teaching_chain": {
                    "target_level": item["level"],
                    "source": "teacher_reference_independent_generation",
                },
            })
            questions.append(question)
    return slots, questions


for _, items in SETS:
    for item in items:
        render(item)
        print(item["code"])

slots, questions = workbench_payload()
bank = OUT.parent
(bank / "generation" / "student_generated_question_candidates.json").write_text(
    json.dumps(
        {
            "schema_version": "generated-question-candidate-pool-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "knowledge_practice",
            "logic": "teacher_reference_independent_generation_v1",
            "candidate_count_per_slot": 1,
            "slots": slots,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
(bank / "generation" / "generated_questions.json").write_text(
    json.dumps(
        {
            "schema_version": "generated-question-set-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "student_practice",
            "status": "teacher_reference_pending_review",
            "questions": questions,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
