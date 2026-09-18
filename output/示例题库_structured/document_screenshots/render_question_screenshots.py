from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).parent
FONT = "C:/Windows/Fonts/msyh.ttc"
BOLD_FONT = "C:/Windows/Fonts/msyhbd.ttc"
PAGE_WIDTH = 1800


EXAMPLES = [
    {
        "file": "01-basic-derivatives.png",
        "title": "知识点 1：导数与微分 - 求导运算 - 基本函数求导",
        "subtitle": "从基本导数到隐函数求导；每题均附关键步骤。",
        "items": [
            ("难度 1", "设 f(x)=x^3-2x，求 f'(1)。", "答案：1。f'(x)=3x^2-2，所以 f'(1)=3-2=1。"),
            ("难度 2", "设 f(x)=sin x+x^2，求 f'(0)。", "答案：1。f'(x)=cos x+2x，代入 x=0 得 1。"),
            ("难度 3", "设 f(x)=x^2e^x，求 f'(1)。", "答案：3e。用乘积求导：f'(x)=2xe^x+x^2e^x=e^x(x^2+2x)。"),
            ("难度 4", "求 f(x)=ln x / x（x>0）的单调区间。", "f'(x)=(1-ln x)/x^2。x^2>0；0<x<e 时导数为正，x>e 时为负。因此在 (0,e) 递增、在 (e,+infinity) 递减。"),
            ("难度 5", "曲线 x^2+xy+y^2=7 与直线 x=1 相交于两点，求两点处的切线斜率。", "交点为 (1,2)、(1,-3)。隐函数求导得 2x+y+(x+2y)y'=0。代入两点，斜率分别为 -4/5、-1/5。"),
        ],
    },
    {
        "file": "02-tangent-lines.png",
        "title": "知识点 2：导数与微分 - 切线方程 - 求切线",
        "subtitle": "由切点斜率到外点切线与参数定位。",
        "items": [
            ("难度 1", "求曲线 y=x^2 在点 (1,1) 处的切线方程。", "y'=2x，切点处斜率为 2。故 y-1=2(x-1)，即 y=2x-1。"),
            ("难度 2", "求 y=x^3-3x 在 x=1 处的切线方程。", "y'=3x^2-3；x=1 时斜率为 0，且 y(1)=-2。因此切线为 y=-2。"),
            ("难度 3", "求 y=ln x 在 x=e 处的切线方程。", "切点为 (e,1)，斜率 y'(e)=1/e。故 y-1=(x-e)/e，化简为 y=x/e。"),
            ("难度 4", "从点 (0,-1) 向抛物线 y=x^2 作切线，求所有切线方程。", "设切点横坐标为 t，切线为 y=2tx-t^2。代入 (0,-1) 得 t^2=1，t=+/-1。因此切线为 y=2x-1 或 y=-2x-1。"),
            ("难度 5", "曲线 y=x^3-3x^2+2 的哪一条切线经过点 (1,0)？求该切线。", "设切点为 t，则 f(t)+f'(t)(1-t)=-2(t-1)^3=0，故 t=1。f(1)=0，f'(1)=-3，所以切线为 y=-3(x-1)。"),
        ],
    },
    {
        "file": "03-monotonicity.png",
        "title": "知识点 3：导数应用 - 单调性 - 判断单调区间",
        "subtitle": "由导数符号表判断函数变化，并处理参数。",
        "items": [
            ("难度 1", "判断 f(x)=3x-1 的单调性。", "f'(x)=3>0，所以 f(x) 在 R 上单调递增。"),
            ("难度 2", "求 f(x)=x^2-4x 的单调区间。", "f'(x)=2x-4。x<2 时导数小于 0，x>2 时导数大于 0；故在 (-infinity,2) 递减、在 (2,+infinity) 递增。"),
            ("难度 3", "求 f(x)=x^3-3x 的单调区间。", "f'(x)=3(x-1)(x+1)。符号表给出：在 (-infinity,-1) 与 (1,+infinity) 递增，在 (-1,1) 递减。"),
            ("难度 4", "求 f(x)=ln x-x/2 的单调区间及最大值。", "定义域 x>0，f'(x)=1/x-1/2=(2-x)/(2x)。故 (0,2) 递增、(2,+infinity) 递减，最大值为 f(2)=ln 2-1。"),
            ("难度 5", "已知 f_a(x)=ln x+a/x（x>0），讨论其单调性。", "f'_a(x)=(x-a)/x^2。a<=0 时 x-a>0，函数在 (0,+infinity) 递增；a>0 时在 (0,a) 递减、在 (a,+infinity) 递增。"),
        ],
    },
    {
        "file": "04-extrema.png",
        "title": "知识点 4：导数应用 - 极值与最值 - 求最值",
        "subtitle": "覆盖驻点、端点与含参数最值反推。",
        "items": [
            ("难度 1", "求 f(x)=x^2-4x+5 的最小值。", "f(x)=(x-2)^2+1，因此最小值为 1，取到时 x=2。"),
            ("难度 2", "求 f(x)=x^3-3x+2 的极大值和极小值。", "f'(x)=3(x-1)(x+1)。x=-1 处由正变负，极大值 f(-1)=4；x=1 处由负变正，极小值 f(1)=0。"),
            ("难度 3", "求 f(x)=x^2+4/x（x>0）的最小值。", "f'(x)=2x-4/x^2。令 f'=0 得 x^3=2。导数先负后正，最小值为 3*2^(2/3)。"),
            ("难度 4", "求 f(x)=x^3-3x^2+1 在 [0,4] 上的最大值与最小值。", "f'(x)=3x(x-2)。比较端点和驻点：f(0)=1，f(2)=-3，f(4)=17。因此最大值 17，最小值 -3。"),
            ("难度 5", "a>0，f(x)=x^2+a/x（x>0）的最小值为 12，求 a 及取最小值时的 x。", "f'=2x-a/x^2=0，得 x=(a/2)^(1/3)。最小值为 3(a/2)^(2/3)=12，故 a=16，取到时 x=2。"),
        ],
    },
    {
        "file": "05-total-probability.png",
        "title": "知识点 5：概率统计 - 概率模型 - 全概率公式",
        "subtitle": "从分支加权到贝叶斯反推的概率建模。",
        "items": [
            ("难度 1", "甲盒被选中的概率为 0.4，抽到红球概率为 0.5；乙盒相应概率为 0.6、0.2。随机选择一盒后抽球，求抽到红球的概率。", "P(红)=0.4*0.5+0.6*0.2=0.32。"),
            ("难度 2", "生产线 A、B 的产量占比为 0.6、0.4；次品率为 0.02、0.05。随机抽取一件，求次品概率。", "按来源分解：P(次品)=0.6*0.02+0.4*0.05=0.032。"),
            ("难度 3", "A 班占 0.3，及格率 0.8；B 班占 0.7，及格率 0.5。随机抽到一名及格学生，求其来自 A 班的概率。", "P(及格)=0.3*0.8+0.7*0.5=0.59。P(A|及格)=0.3*0.8/0.59=24/59。"),
            ("难度 4", "某病患病率为 0.02；检测灵敏度 P(+|病)=0.90，假阳性率 P(+|非病)=0.05。检测阳性者实际患病的概率是多少？", "P(+)=0.02*0.90+0.98*0.05=0.067。由贝叶斯公式 P(病|+)=0.018/0.067=18/67，约 26.87%。"),
            ("难度 5", "供应商 A、B、C 的供货占比为 0.2、0.3、0.5，次品率为 0.01、0.03、0.06。已知产品为次品，求其来自 C 的概率。", "P(次品)=0.2*0.01+0.3*0.03+0.5*0.06=0.041。P(C|次品)=0.5*0.06/0.041=30/41。"),
        ],
    },
]


def load_font(size, bold=False):
    return ImageFont.truetype(BOLD_FONT if bold else FONT, size)


def wrap(draw, text, font, max_width):
    lines = []
    current = ""
    for char in text:
        candidate = current + char
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_multiline(draw, xy, text, font, fill, max_width, spacing):
    x, y = xy
    lines = wrap(draw, text, font, max_width)
    line_height = font.size + spacing
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y, len(lines)


def render(example):
    title_font = load_font(44, bold=True)
    subtitle_font = load_font(25)
    level_font = load_font(23, bold=True)
    question_font = load_font(27, bold=True)
    solution_font = load_font(25)
    small_font = load_font(22)
    page_height = 2500
    image = Image.new("RGB", (PAGE_WIDTH, page_height), "#f3f6fb")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, PAGE_WIDTH, 26), fill="#1f5fa8")
    draw.text((88, 72), "推题生题 · 难度分层示例", font=small_font, fill="#52708e")
    draw.text((88, 116), example["title"], font=title_font, fill="#15243a")
    draw.text((88, 180), example["subtitle"], font=subtitle_font, fill="#5f7185")
    draw.line((88, 232, PAGE_WIDTH - 88, 232), fill="#d7e0ec", width=2)

    y = 278
    accent_colors = ["#3c82c5", "#378e87", "#8b6db7", "#b86f3d", "#b64c58"]
    for index, (level, question, solution) in enumerate(example["items"]):
        card_x = 88
        card_width = PAGE_WIDTH - 176
        question_lines = wrap(draw, question, question_font, card_width - 205)
        solution_lines = wrap(draw, solution, solution_font, card_width - 205)
        content_height = 94 + len(question_lines) * 39 + 18 + len(solution_lines) * 37 + 42
        card_height = max(280, content_height)

        draw.rounded_rectangle((card_x, y, card_x + card_width, y + card_height), radius=16, fill="#ffffff", outline="#dbe4ef", width=2)
        draw.rounded_rectangle((card_x, y, card_x + 18, y + card_height), radius=9, fill=accent_colors[index])
        label_x = card_x + 54
        draw.rounded_rectangle((label_x, y + 34, label_x + 122, y + 76), radius=12, fill="#edf3fa")
        draw.text((label_x + 16, y + 43), level, font=level_font, fill=accent_colors[index])
        text_x = card_x + 212
        q_y = y + 32
        draw.text((text_x, q_y), "题目", font=small_font, fill="#6b7e94")
        next_y, _ = draw_multiline(draw, (text_x + 62, q_y - 4), question, question_font, "#172842", card_width - 285, 12)
        solution_y = max(q_y + 46 + len(question_lines) * 39, next_y) + 18
        draw.text((text_x, solution_y), "解析", font=small_font, fill="#6b7e94")
        draw_multiline(draw, (text_x + 62, solution_y - 3), solution, solution_font, "#40546d", card_width - 285, 12)
        y += card_height + 30

    footer_y = y + 12
    draw.text((88, footer_y), "题目设计原则：同知识点递增，不以单纯增大数值或拉长题干代替难度提升。", font=small_font, fill="#62758b")
    image.crop((0, 0, PAGE_WIDTH, footer_y + 72)).save(OUT / example["file"], optimize=True)


for example in EXAMPLES:
    render(example)
    print(OUT / example["file"])
