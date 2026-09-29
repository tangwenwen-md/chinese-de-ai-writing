# Third-party notices

This project adapts ideas, rule definitions, regular-expression approaches and
human/AI baseline figures from the MIT-licensed projects below. Rules were
rewritten in our own words; where a pattern or number is taken from a project,
the source is named next to it in `references/evidence.md` or in code comments.

| Project | What was adapted | License |
|---|---|---|
| [larashero3-dotcom/lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone) | Measured feature list (rules A1–A11), human/AI per-1,000-character baselines, regex approach in `scripts/zh_ai_scan.py` (paragraph-comment and adjacent-sentence signature checks, translationese markers, prompt-colon pattern) | MIT, Copyright (c) 2026 shiujan |
| [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) | Constraint priority (information and certainty first), "keep" boundaries per rule, dropping self-scoring, some Chinese-specific pattern ideas | MIT, Copyright (c) 2026 歸藏 |
| [MrGeDiao/shuorenhua](https://github.com/MrGeDiao/shuorenhua) | Keeping vague attributions and flagging instead of deleting; reasons for not shipping a word blacklist | MIT, Copyright (c) 2026 MrGeDiao |
| [LifelongLazyLearner/qu-ai-wei](https://github.com/LifelongLazyLearner/qu-ai-wei) | Evidence-level labelling of rules; "re-skinned pattern" idea | MIT |
| [KKKKhazix/human-writing](https://github.com/KKKKhazix/human-writing) | Material check before writing | MIT |
| [Hyacehila/humanizer-zh-next](https://github.com/Hyacehila/humanizer-zh-next) | Academic-mode keep list and claim–evidence matching | MIT |
| [Raymondhou0917/speak-human-tw](https://github.com/Raymondhou0917/speak-human-tw) | "Stance vacuum" pattern and its medical exception | MIT |

The MIT license text of each project applies to the portions adapted from it:

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

Other sources (Wikipedia "Signs of AI writing" pages, CC BY-SA; academic papers)
are cited, not copied. The HC3-Chinese dataset (CC BY-SA) used for validation is
not redistributed; `validation/validate_corpus.py` explains how to download it.
Questions in `validation/corpus/claude_qa_questions.json` are taken from HC3-Chinese
(CC BY-SA 4.0) and remain under that license.
