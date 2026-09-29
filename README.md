# chinese-de-ai-writing · 中文去 AI 味

> An evidence-graded skill (Claude Code / Agent Skills format) for auditing and editing AI-sounding patterns in Simplified Chinese. Only features that hold up in human/AI corpus comparisons are enforced; popular rules that were refuted by data are listed as things not to do. The top constraint is information conservation: no invented facts, cases, numbers or quotes, and no change to claim strength.

[简体中文](README.zh-CN.md) · [License (MIT)](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md) · [Contributing](CONTRIBUTING.md)

---

## Why another one

There are already many Chinese "de-AI" skills on GitHub. Reviewing 13 of them turned up two problems:

1. **Many popular rules are wrong.** [lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone) tested 26 widely shared tells against a 2.83-million-character human/AI corpus; only 11 held. "Vary sentence length", "remove rhetorical questions", "use fewer metaphors" and "add colloquial fillers" all failed: humans use rhetorical questions 17× and metaphors 2.4× as often as the models tested.
2. **Many rewrite examples fabricate.** They add numbers, experiences, or "a child I saw in clinic last week" that the author never wrote. For medical, academic and official writing this is more dangerous than the AI tone itself.

This project combines those findings, labels every rule with its evidence level, and ships a reproducible validation.

## What is inside

```
SKILL.md                    hard constraints, four modes, rule table (in Chinese)
references/patterns.md      each rule with before/after examples and keep-boundaries
references/registers.md     register rules: social media, spoken scripts & dialogue, popular science, grant/official documents, academic Chinese
references/evidence.md      sources, how conflicts between projects were resolved, folk methods checked, known gaps
scripts/zh_ai_scan.py       regex scanner: 10 measured features, density per 1,000 characters vs human/AI baselines, line numbers
validation/                 validation script, Claude-generated comparison corpus, results
tests/                      regression samples
```

Modes: **audit** (diagnose only), **edit** (minimal changes, with a change log and "needs author input" list), **write** (inventory real material before drafting), and **pipeline review** (fixed JSON output for multi-agent pipelines).

## Evidence levels

| Level | Meaning | Examples |
|---|---|---|
| A measured | Holds in human/AI comparison; enforced | "not X but Y" reversal, paragraph-initial comment without anaphora, prompt colons, idle sentence + colon + list, ordinal headings, dense enumeration with 、, idealised-role metaphors |
| B consensus | Named by several projects or practitioner sources, no Chinese frequency data; **edited only when empty** | significance inflation, "in today's era" openers, upbeat closers, business jargon, assistant-style pleasantries |
| C do not | Refuted or contradicted by data | adjusting sentence length, deleting rhetorical questions or metaphors, blanket nominalisation fixes, word-list substitution, typos, back-translation, synonym spinning |

## Validation

The scanner was run on HC3-Chinese (human vs GPT-3.5 answers; open_qa, medicine, psychology) and on Claude-generated text. "Flagged" means at least one measured feature exceeds twice the human baseline.

| Group | Docs | Flagged |
|---|---|---|
| Human answers (HC3) | 12,078 | 3.4% (false-positive rate) |
| GPT-3.5 answers (HC3) | 5,803 | 18.9% |
| Claude answers to the same questions | 60 | 85.0% |
| Claude popular-science drafts | 12 | 83.3% |

Edit-mode results, per-feature numbers and limitations are in [validation/RESULTS.md](validation/RESULTS.md). In short:

- Current Claude models almost never use stock phrases like 综上所述 or 此外. Their AI tone is structural: idle lead-in + list, ordinal headings, long 、 enumerations. GPT-3.5 is the opposite.
- Em-dash frequency changes a lot across model versions, even within one vendor.
- The human control set is Q&A text. False-positive rates on long-form human articles with headings have not been measured yet.

## Install

Claude Code:

```bash
git clone https://github.com/tangwenwen-md/chinese-de-ai-writing ~/.claude/skills/chinese-de-ai-writing
```

Then ask in Chinese, for example 帮我去一下 AI 味 or 这段有没有 AI 味. The scanner uses only the Python 3 standard library and works on its own:

```bash
python3 scripts/zh_ai_scan.py draft.md --register 科普
```

`--register`: 通用, 社媒, 口播, 台词, 科普, 文书, 学术.

## What it does not do

- It does not aim at lowering scores from AIGC detectors (CNKI, Zhuque, GPTZero) and provides no evasion techniques. Label AI-assisted content as your platform or institution requires.
- It does not judge whether medical or legal content is correct; it only guarantees edits do not change facts or claim strength.
- It does not handle English text.

## Citation

See [CITATION.cff](CITATION.cff).

## Acknowledgements

Rules and baselines draw heavily on lieflat-less-ai-tone, op7418/Humanizer-zh, shuorenhua, qu-ai-wei, human-writing, humanizer-zh-next and speak-human-tw (all MIT), the English and Chinese Wikipedia pages on signs of AI writing, Zhu et al. (CCL 2023) and the HC3 dataset. Details in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [references/evidence.md](references/evidence.md).
