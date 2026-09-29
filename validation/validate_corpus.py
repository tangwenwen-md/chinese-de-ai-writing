#!/usr/bin/env python3
"""用人机对照语料检验 zh_ai_scan.py：各组每千字密度、文档触发率（人类组即误报率）。

用法：
    python3 validate_corpus.py --hc3 <HC3-Chinese 目录> [--extra 名称=目录 ...]

HC3-Chinese 从 https://huggingface.co/datasets/Hello-SimpleAI/HC3-Chinese 下载 medicine.jsonl、
open_qa.jsonl、psychology.jsonl 放进同一目录（CC-BY-SA，本仓库不附带）。
--extra 的目录里放 .md 文件，每个文件一篇，例如 validation/corpus/claude_qa。
只统计汉字数 ≥50 的回答。
"""
import argparse
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from zh_ai_scan import han_count, scan  # noqa: E402

SUBSETS = ["medicine", "open_qa", "psychology"]


def load(args):
    groups = collections.OrderedDict()
    if args.hc3:
        groups["human"], groups["gpt35"] = [], []
        for f in SUBSETS:
            for line in open(pathlib.Path(args.hc3) / f"{f}.jsonl", encoding="utf-8"):
                r = json.loads(line)
                groups["human"] += [a for a in r["human_answers"] if a and han_count(a) >= 50]
                groups["gpt35"] += [a for a in r["chatgpt_answers"] if a and han_count(a) >= 50]
    for e in args.extra or []:
        name, path = e.split("=", 1)
        groups[name] = [p.read_text(encoding="utf-8") for p in sorted(pathlib.Path(path).glob("*.md"))]
    return groups


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hc3")
    ap.add_argument("--extra", nargs="*")
    args = ap.parse_args()
    groups = load(args)
    stats = {}
    for g, docs in groups.items():
        dens, flags, kchar, anyflag = collections.Counter(), collections.Counter(), 0, 0
        for t in docs:
            res = scan(t)
            kchar += res["汉字数"] / 1000
            hit = False
            for r in res["实测"]:
                if r["单位"] == "每千字":
                    dens[r["特征"]] += r["命中"]
                if r["判断"] != "正常":
                    flags[r["特征"]] += 1
                    hit = True
            anyflag += hit
        stats[g] = (len(docs), kchar, dens, flags, anyflag)

    names = list(stats)
    print("| 组 | 文档数 | 千字 | 任一实测项判为偏高的文档比例 |")
    print("|---|---|---|---|")
    for g in names:
        n, k, _, _, a = stats[g]
        print(f"| {g} | {n} | {k:.1f} | {a / n * 100:.1f}% |")
    feats = sorted(set().union(*[set(stats[g][3]) | set(stats[g][2]) for g in names]))
    print("\n分项文档触发率：\n")
    print("| 特征 | " + " | ".join(names) + " |")
    print("|---|" + "---|" * len(names))
    for f in feats:
        print(f"| {f.split('（')[0]} | " + " | ".join(f"{stats[g][3][f] / stats[g][0] * 100:.1f}%" for g in names) + " |")
    print("\n每千字密度：\n")
    print("| 特征 | " + " | ".join(names) + " |")
    print("|---|" + "---|" * len(names))
    for f in feats:
        if any(stats[g][2][f] for g in names):
            print(f"| {f.split('（')[0]} | " + " | ".join(f"{stats[g][2][f] / stats[g][1]:.2f}" for g in names) + " |")


if __name__ == "__main__":
    main()
