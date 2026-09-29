#!/usr/bin/env python3
"""中文 AI 痕迹量化扫描：只数能用正则定位的形式特征，给出每千字密度和人机基线对照。

用法：
    python3 zh_ai_scan.py <文件> [--register 社媒|口播|科普|文书|学术|通用] [--json] [--all]
    cat 稿子.md | python3 zh_ai_scan.py -

输出三块：
  1. 实测特征（有人机对照基线，来自 lieflat-less-ai-tone 283 万字语料，MIT 许可）
  2. 共识特征（多个项目或社区提到，但没有中文频率数据，只作提示）
  3. 每条命中的行号和原句片段，默认每项最多列 8 条（--all 全列）

这个脚本不打分、不判定"是不是 AI 写的"。它只告诉你哪几类形式特征明显高于人类写作的常见水平，
以及它们在哪。改不改、怎么改，按 SKILL.md 的规则和文体例外来判断。
基线是公开文章语料的平均值，不同作者之间差异可以很大（破折号人类组间相差百倍），
所以作者本人一贯的写法优先于基线。
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HAN = re.compile(r"[一-鿿]")

# ---------------------------------------------------------------------------
# 实测特征：human / ai 为每千汉字（段落类指标另注单位），来源 lieflat RESEARCH.md
# ---------------------------------------------------------------------------
FANAN = re.compile(
    r"(?<![是还])(?:不是|并非|并不是)[^。！？\n]{1,24}?[，,]?\s*(?:而是|是)(?=[^。！？\n])"
    r"|不在于[^。！？\n]{1,24}?而在于"
    r"|与其说[^。！？\n]{1,24}?不如说"
    r"|(?:看似|表面上?)[^。！？\n]{1,20}?(?:实则|实际上|其实)"
    r"|你以为[^。！？\n]{1,20}?其实"
    r"|(?:这|它)?不仅(?:仅)?是[^。！？\n]{1,24}?(?:更是|也是|而是)"
    r"|答案恰恰相反|说到底|回头才发现"
)
# "不是 A 是 B" 的宽匹配误报多，要求前半有逗号分隔或出现"而是"
FANAN_STRICT_FILTER = re.compile(r"而是|更是|也是|实则|其实|不如说|而在于|恰恰相反|说到底|回头才发现|[，,]\s*是")

DASH = re.compile(r"(?<!—)(?:——|—)(?![—》>→])")  # 连续 3 个以上的分隔线、"——》"箭头不算
# 依据 HC3 验证：裸标签"问题：/建议：/原因："在人类医疗问答里同样常见（医生回复的固定格式），不收
PROMPT_COLON = re.compile(
    r"(?<!第)(?<!这)(?:一句话(?:总结|说|概括)?|简单(?:来)?说|说白了|总结(?:一下)?|小结|结论|核心(?:是|在于|观点)?"
    r"|关键(?:是|在于)|重点(?:是)|原因(?:如下|在于)|问题(?:是|在于)|答案(?:是)?"
    r"|本质(?:是|上)?|具体(?:来说|如下)|换句话说|也就是说|我的(?:观点|判断|结论))[：:](?!\s*[「“\"『])"  # 后面紧跟引号的是引出原话，不算
)
# 引导句本身带行动指令（出现下面任一条就去医院：），不是空转
ACTION_LEADER = re.compile(r"(?:立即|立刻|马上|尽快|直接|及时)[^：:]{0,12}(?:就医|就诊|去医院|挂号|挂[^：:]{0,6}门诊|走[^：:]{0,8}门诊|复诊|急诊|拨打|打120)")
OPENER = re.compile(r"(?:^|[。！？\n])\s*(?:说白了|说穿了|先说结论)")
PERSONA_METAPHOR = re.compile(
    r"(?:像|如同|好比|相当于|宛如|犹如)(?:一位|一个|一名|位)[^，。！？\n]{0,10}?"
    r"(?:导师|秘书|助手|顾问|管家|审查员|向导|守护者|引路人|伙伴|老师|医生|朋友)"
)
DUNHAO_CLAUSE = re.compile(r"[^，。！？；：\n]*、[^，。！？；：\n]*、[^，。！？；：\n]*")

# 翻译腔五种（lieflat 18 种候选筛剩 5 种）
TRANSLATIONESE = {
    "长前置定语": re.compile(r"(?:一个|一种|一套|这种|这个)[^，。、；：！？\n]{15,}的[一-鿿]{2,5}"),
    "当…时前置": re.compile(r"当[^，。！？\n]{2,20}(?:的时候|时)，"),
    "前置话题壳": re.compile(r"(?:对于[^，。！？\n]{2,15}(?:来说|而言)|对[^，。！？\n]{2,15}而言|就[^，。！？\n]{2,15}而言|在[^，。！？\n]{2,12}方面)"),
    "句首连接词当路标": re.compile(r"(?:^|[。！？\n])\s*(?:然而|因此|此外|与此同时|换言之|总而言之)[，、]"),
    "这意味着复述": re.compile(r"这(?:意味着|表明|说明)"),
}

COMMENT_START = re.compile(
    r"^(?:听起来|看起来|看上去|听上去|说白了|说到底|换句话说|意味着|值得注意|不难看出|细看|再看|"
    r"回过头看|问题在于|原因在于|结果是|有意思的是|更重要的是|关键在于|真正的)"
)
ANAPHOR = re.compile(
    r"^(?:这|那|其|此|上面|前面|刚才|以上|该|它|他|她|同样|类似|相比|反过来|但|不过|所以|因此|于是|而|另|除此|与此)"
)
ORDINAL_HEAD = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:[一二三四五六七八九十]+、|第[一二三四五六七八九十]+[，、：:部章节点步]|[（(][一二三四五六七八九十]+[)）]|\d+[.、．]\s*\S)"
)
ORDINAL_HEAD_CN = re.compile(r"^\s*(?:[一二三四五六七八九十]+、|第[一二三四五六七八九十]+[部章节步]|[（(][一二三四五六七八九十]+[)）])")
LIST_LINE = re.compile(r"^\s*(?:[-*•·]\s|\d+[.、．)]\s*|[（(]?\d+[)）]|[一二三四五六七八九十]+、)")

# ---------------------------------------------------------------------------
# 共识特征：没有中文频率基线，只提示位置
# ---------------------------------------------------------------------------
CONSENSUS = {
    "聊天残留/客服腔": r"希望(?:这|以上)?(?:些)?(?:内容)?(?:能)?对(?:你|您)有(?:所)?帮助|好问题|当然可以|你说得(?:很|非常)?对|如果你愿意|要不要我|需要的话我可以|以下是|作为一个?(?:AI|人工智能|语言模型)",
    "时代帽子开场": r"随着[^，。！？\n]{1,20}的(?:不断|快速|飞速|日益)?(?:发展|进步|普及)|在当今[^，。！？\n]{0,10}(?:时代|社会)|在[^，。！？\n]{1,12}(?:的)?(?:背景|浪潮|时代)下|近年来[，,]",
    "意义拔高": r"标志着|里程碑|具有(?:十分|非常)?重要(?:的)?意义|意义(?:重大|非凡|深远)|至关重要|举足轻重|不可或缺|开启了?[^，。！？\n]{0,8}新篇章|谱写|注入(?:新的)?活力|彰显|见证了",
    "展望/正能量收尾": r"未来可期|让我们(?:一起)?拭目以待|前景广阔|任重而道远|尽管[^。！？\n]{2,30}(?:但|仍)[^。！？\n]{0,20}(?:值得期待|充满希望|前景)|让我们(?:一起|携手)",
    "总结标签": r"综上所述|总而言之|总的来说|简而言之|一言以蔽之|由此可见",
    "官样路标": r"值得(?:一提|注意)的是|需要指出的是|不可否认|毋庸置疑|不难发现|众所周知|显而易见",
    "模糊归因": r"(?:有|相关)?研究(?:表明|显示|发现)|数据显示|(?:有)?专家(?:认为|指出|表示)|业内人士|普遍认为|大量(?:实践|研究)(?:证明|表明)",
    "黑话大词": r"赋能|抓手|闭环|底层逻辑|顶层设计|颗粒度|拉通|打通|沉淀|全链路|深度融合|降本增效|心智|赛道|范式|跃迁|打造|助力",
    "接住腔/心理咨询腔": r"稳稳(?:地)?接住|接住(?:你|您|情绪)|我(?:就)?在这里|不躲、?不藏|你不是[^，。！？\n]{0,6}(?:敏感|想太多|矫情)|这次我(?:真的)?懂了",
    "回避是/有": r"扮演着?[^，。！？\n]{0,10}角色|作为[^，。！？\n]{1,12}的(?:重要)?(?:载体|组成部分|代表)|起到了?[^，。！？\n]{0,8}作用|发挥着?[^，。！？\n]{0,8}作用",
    "并列列举(包括…等)": r"包括[^。！？\n]{4,50}等",
    "限定词堆叠": r"(?:也许|可能|或许)[^，。！？\n]{0,4}(?:可能|或许|也许)|在一定程度上[^，。！？\n]{0,6}(?:可能|或许)",
    "戏剧碎句": r"(?:^|[。！？\n])[^，。！？\n]{1,5}。[^，。！？\n]{1,5}。[^，。！？\n]{1,5}。",
}
CONSENSUS = {k: re.compile(v) for k, v in CONSENSUS.items()}

BOLD = re.compile(r"\*\*[^*\n]+\*\*")
MODAL_PARTICLE = re.compile(r"[吧呢嘛啊呀哈呗啦咯]")


def is_emoji(ch):
    cp = ord(ch)
    return 0x1F300 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or cp in (0x2B50, 0x2B55)


def han_count(text):
    return len(HAN.findall(text))


def body_paragraphs(lines):
    """正文段落：去掉标题、表格、代码、引用、列表、图片行"""
    out = []
    in_code = False
    for no, raw in lines:
        s = raw.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or len(s) < 8:
            continue
        if s.startswith(("#", "|", ">", "!", "[")) or LIST_LINE.match(s):
            continue
        out.append((no, s))
    return out


def sentences(par):
    return [s.strip() for s in re.split(r"[。！？!?]", par) if s.strip()]


def signature(sent):
    return (sent.count("，"), "：" in sent, ("（" in sent or "(" in sent), len(sent) // 15)


def locate(pattern, lines, filt=None):
    hits = []
    for no, line in lines:
        for m in pattern.finditer(line):
            frag = m.group(0).strip()
            if filt and not filt.search(frag):
                continue
            start = max(0, m.start() - 8)
            hits.append((no, line[start:m.end() + 12].strip()))
    return hits


def scan(text, register="通用"):
    lines = list(enumerate(text.splitlines(), 1))
    kchar = han_count(text) / 1000 or 0.001
    paras = body_paragraphs(lines)
    body_lines = paras  # 句子层特征只在正文里数，避免把标题、列表算进去
    result = {"汉字数": int(kchar * 1000), "正文段数": len(paras), "实测": [], "共识": [], "格式": {}}

    def add_measured(name, hits, human, ai, unit="每千字", denom=None, note=""):
        n = len(hits)
        if unit == "每千字":
            rate = n / kchar
        else:
            rate = n / denom * 100 if denom else 0
        # 人类基线低于 0.1/千字（或 0.2%）的特征，人类基本不写，出现一次就值得看；
        # 其余特征要求至少 2 处，避免短文本里一处命中把密度撑得很高
        rare = human < 0.1 if unit == "每千字" else human < 0.2
        min_n = 1 if rare else (3 if unit == "每百段" else 2)  # 相邻句同构区分力弱（HC3 人类 3.1% 文档触发），门槛提高
        level = "正常"
        if n >= min_n and rate >= human * 2:
            level = "偏高"
        if n >= min_n and rate >= ai:
            level = "高（达到 AI 平均水平）"
        result["实测"].append({
            "特征": name, "命中": n, "密度": round(rate, 2), "单位": unit,
            "人类基线": human, "AI基线": ai, "判断": level, "说明": note, "位置": hits,
        })

    add_measured("翻案腔（不是…而是 / 不仅是…更是 / 看似…实则）",
                 locate(FANAN, body_lines, FANAN_STRICT_FILTER), 0.22, 0.73,
                 note="纠正真实误解的用法保留，只改制造反转感的")
    add_measured("破折号", locate(DASH, body_lines), 0.80, 2.38,
                 note="模型差异大：DeepSeek 5.16、Claude 4.25、GPT 0.11；作者本人习惯优先")
    add_measured("提示性冒号（核心是：/ 原因如下：）", locate(PROMPT_COLON, lines), 0.08, 0.29)

    # 空转句引列表：以冒号结尾的正文行，下一非空行是列表
    idle = []
    for i, (no, raw) in enumerate(lines):
        s = raw.strip()
        if s.endswith(("：", ":")) and not s.startswith("#") and 4 <= len(s) <= 40 and not ACTION_LEADER.search(s):
            nxt = next((l for _, l in lines[i + 1:] if l.strip()), "")
            if LIST_LINE.match(nxt.strip()):
                idle.append((no, s))
    add_measured("空转句引出列表（几种情况：+ 列表）", idle, 0.03, 0.29)

    add_measured("起手式（说白了 / 说穿了 / 先说结论）", locate(OPENER, body_lines), 0.008, 0.025)

    # 序数词小标题：标题行（# 开头，或 ≤30 字、以"一、/第一"起头的独立短行）里连续 ≥3 个序数开头算一组；
    # 正文段落不打断计数，非序数标题才打断
    runs, cur = [], []
    for no, raw in lines:
        s = raw.strip()
        is_md_head = s.startswith("#")
        is_cn_head = (not is_md_head) and len(s) <= 30 and ORDINAL_HEAD_CN.match(s)
        if not (is_md_head or is_cn_head):
            continue
        if ORDINAL_HEAD.match(s):
            cur.append((no, s))
        else:
            if len(cur) >= 3:
                runs.append(cur)
            cur = []
    if len(cur) >= 3:
        runs.append(cur)
    ord_hits = [h for r in runs for h in r]
    add_measured("序数词当小标题（一、二、三 连续 ≥3）", ord_hits, 0.06, 0.19,
                 note="正文里的'首先、其次'不算；学术论文、标书的章节编号是文体要求，不改")

    add_measured("拟人化职业喻体（像一位智慧的导师）", locate(PERSONA_METAPHOR, body_lines), 0.002, 0.018,
                 note="具体的人做喻体（像个老师傅）不改；比喻本身人类用得更多，不要删比喻")

    # 顿号罗列：一个分句里 ≥2 个顿号
    dun = []
    for no, s in body_lines:
        for m in DUNHAO_CLAUSE.finditer(s):
            dun.append((no, m.group(0).strip()[:40]))
    add_measured("顿号罗列（一个分句串 ≥3 项）", dun, 1.78, 3.21, note="条件纳入（倍率 1.8），同段其他特征也高时才处理；症状、检查、鉴别诊断这类必要清单不压缩。列表行不计入，所以把列表并成段落后这一项会升高，属正常")

    # 段落级：段首零回指评论、相邻句同构
    zero, nonfirst, iso = [], 0, []
    for idx, (no, p) in enumerate(paras):
        sents = [x for x in sentences(p) if len(x) > 10]
        for i in range(len(sents) - 1):
            a, b = signature(sents[i]), signature(sents[i + 1])
            if a == b and a[0] >= 1:
                iso.append((no, sents[i][:20] + " / " + sents[i + 1][:20]))
        if idx == 0:
            continue
        nonfirst += 1
        if COMMENT_START.match(p) and not ANAPHOR.match(p):
            zero.append((no, p[:30]))
    add_measured("段首零回指评论（非首段以'看起来/关键在于'开头且无'这/那'）", zero, 0.14, 0.61,
                 unit="占非首段%", denom=nonfirst, note="区分力最强的一条；多数只需补一个'这'")
    add_measured("相邻句结构同款（逗号数、长度档相同）", iso, 4.81, 9.41,
                 unit="每百段", denom=len(paras), note="句内排比人类更多，不改；只看相邻整句套同一骨架")

    # 翻译腔五种：只有 AI 侧频率，人类侧除句首连接词外未公开，统一按提示处理
    for name, pat in TRANSLATIONESE.items():
        hits = locate(pat, body_lines)
        result["共识"].append({"特征": "翻译腔·" + name, "命中": len(hits),
                             "密度": round(len(hits) / kchar, 2), "位置": hits,
                             "说明": "实测 AI 多 2.6–5.3 倍，但单处不构成问题，同段堆叠才改"})

    for name, pat in CONSENSUS.items():
        hits = locate(pat, body_lines)
        result["共识"].append({"特征": name, "命中": len(hits), "密度": round(len(hits) / kchar, 2),
                             "位置": hits, "说明": "命中且空泛才改；有具体内容跟着的保留"})

    # 格式
    bold = len(BOLD.findall(text))
    emoji = sum(1 for ch in text if is_emoji(ch))
    list_lines = sum(1 for _, l in lines if LIST_LINE.match(l.strip()))
    nonempty = sum(1 for _, l in lines if l.strip())
    result["格式"] = {
        "加粗处数": bold,
        "emoji 个数": emoji,
        "列表行占比": f"{list_lines}/{nonempty}",
        "语气词每千字": round(len(MODAL_PARTICLE.findall(text)) / kchar, 1),
    }
    notes = []
    if bold >= 5:
        notes.append("加粗 ≥5 处：正文加粗通常只留真正需要读者停下的一两处")
    if register == "台词":
        ell = len(re.findall(r"……|\.\.\.", text))
        lines_n = sum(1 for _, l in lines if l.strip())
        if lines_n and ell >= 4 and ell / lines_n > 0.4:
            notes.append(f"省略号 {ell} 处：多数台词都用'……'停顿，角色容易变成一个腔调")
    if register not in ("社媒",) and emoji >= 3:
        notes.append("非社媒文体出现 emoji")
    if register in ("口播", "社媒"):  # 台词不提示语气词：紧张戏的短句本来就可以没有
        mp = result["格式"]["语气词每千字"]
        if mp < 3:
            notes.append(f"口语文体语气词偏少（{mp}/千字）。CCL 2023 估算人类问答约 9/千字、GPT-3.5 约 2/千字（按词密度换算，粗略）。"
                         "只在原文口吻允许时恢复，不要硬塞")
    if nonempty and list_lines / nonempty > 0.4 and register != "文书":
        notes.append("列表行超过四成：检查是不是把连贯的论述切成了要点")
    if kchar < 0.5:
        notes.append("正文不足 500 汉字，密度数字波动大，只看具体命中位置，不看倍率")
    result["提示"] = notes
    return result


def render(res, show_all=False):
    out = []
    out.append(f"汉字 {res['汉字数']}，正文段落 {res['正文段数']}\n")
    out.append("【实测特征】有人机对照基线（lieflat 语料：5 个模型 300 篇 vs 人类 329 篇）")
    out.append(f"{'特征':<44}{'命中':>4}{'密度':>8}  {'人类':>6}{'AI':>6}  判断")
    for r in res["实测"]:
        unit = "" if r["单位"] == "每千字" else f"({r['单位']})"
        name = (r["特征"] + unit)[:40]
        pad = 44 - sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in name)
        out.append(f"{name}{' ' * max(pad, 1)}{r['命中']:>4}{r['密度']:>8}  {r['人类基线']:>6}{r['AI基线']:>6}  {r['判断']}")
    out.append("")
    flagged = [r for r in res["共识"] if r["命中"]]
    out.append("【共识特征】无中文频率基线，只提示位置")
    if not flagged:
        out.append("  （无命中）")
    for r in flagged:
        out.append(f"  {r['特征']}：{r['命中']} 处")
    out.append("")
    out.append("【格式】" + "，".join(f"{k} {v}" for k, v in res["格式"].items()))
    for n in res.get("提示", []):
        out.append("  · " + n)
    out.append("")
    out.append("【命中位置】")
    limit = None if show_all else 8
    for r in res["实测"] + flagged:
        if not r["命中"]:
            continue
        out.append(f"- {r['特征']}（{r.get('说明', '')}）")
        for no, frag in r["位置"][:limit]:
            out.append(f"    L{no}: {frag}")
        if limit and len(r["位置"]) > limit:
            out.append(f"    …另有 {len(r['位置']) - limit} 处（--all 全列）")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="文件路径，- 表示标准输入")
    ap.add_argument("--register", default="通用", choices=["通用", "社媒", "口播", "台词", "科普", "文书", "学术"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true", help="列出全部命中，包括判断为正常的项")
    a = ap.parse_args()
    text = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    res = scan(text, a.register)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(render(res, a.all))


if __name__ == "__main__":
    main()
