# Contributing

This project accepts three kinds of contributions.

## 1. Evidence

The most valuable contribution is data. A rule moves into the enforced group (A) only when it holds up in a human/AI comparison. Useful submissions:

- A public, reproducible Chinese human/AI corpus comparison for any feature in `references/patterns.md`, especially for current models (DeepSeek, Qwen, Kimi, Doubao, GPT, Claude).
- Results of running `validation/validate_corpus.py` on a new human corpus (long-form articles, news, academic abstracts). The current false-positive estimate comes from HC3-Chinese Q&A answers only.
- Peer-reviewed papers that confirm or refute a rule.

Please include the corpus source, size, model versions, and how "human" texts were verified as human (for example, published before November 2022).

## 2. False positives and misses

Open an issue with:

- the text (or a shortened excerpt you have the right to share),
- the register (社媒 / 口播 / 科普 / 文书 / 学术 / 通用),
- what the scanner or the skill flagged, and why you think it is wrong (or what it missed).

Regex changes must be checked against the validation set before merging: the human false-positive rate must not go up.

## 3. Register rules

New register-specific rules (for example, a new platform or document type) should cite where the convention comes from (an official style guide, a platform announcement, practitioner sources). Rules that only reflect personal taste will not be merged.

## What will not be accepted

- Techniques whose purpose is evading AI detectors (typos, back-translation, synonym spinning, invisible characters).
- Rewrite examples that add facts, experiences or numbers not present in the original.
- Word blacklists presented as rules without frequency evidence.
- Direct copying from projects without a compatible license.
