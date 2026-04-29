# GAIA-v2-LILT

[**GAIA-v2-LILT** dataset](https://huggingface.co/datasets/Fujitsu-FRE/MAPS/viewer/GAIA-v2-LILT) is a re-audited version of the MAPS [1] translation of GAIA [2], using a custom review workflow that includes functional alignment, cultural alignment, and difficulty calibration for agentic tasks.
This repository is a fork of [huggingface/smolagents](https://github.com/huggingface/smolagents) and contains code for experiments in the [GAIA-v2-LILT tech report](https://arxiv.org/pdf/2604.24929).

All experiments were run using [Open Deep Research](examples/open_deep_research/), a multi-agent system that answers complex research questions by browsing the web, inspecting files, and synthesizing answers.

## Notable changes from upstream

**Search agent**
- Added Exa as a web search provider (`ApiWebSearchTool`) alongside Serper/SerpAPI
- Fixed `tool_choice=auto` handling for Anthropic models with extended thinking

**Agent core (`agents.py`)**
- Fixed tool-call parse retry to happen in-place, avoiding quadratic context growth
- Strengthened search agent prompt to always produce tool calls under `tool_choice=auto`

**Experiment runner (`run_gaia.py`)**
- CLI flags for `--reasoning-effort` and `--search-reasoning-effort` (independent control of manager vs. search agent)
- Support for loading a local dataset file (JSON) instead of only HuggingFace Hub
- Run questions that have no attached files
- Fixed token usage counting
- Fatal API error detection (insufficient credits, rate limits) with early experiment stopping
- Skipped-task tracking with warnings instead of misleading completion messages

**Scoring**
- Made `gaia_scorer.py` a standalone runnable script with exact-match scoring

## Quick start

```bash
cd examples/open_deep_research
pip install -r requirements.txt
pip install -e ../../.[dev]
```

Required environment variables:
- LLM API key (e.g., `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
- Search API key (e.g., `EXA_API_KEY` or `SERPER_API_KEY`)
- HuggingFace Hub access (`HF_TOKEN`)

```bash
# Run with a local dataset file
python run_gaia.py \
  --concurrency 8 \
  --model-id gpt-5.4 \
  --run-name gaia-v2-lilt \
  --local-dataset-file DATA_FILE_PATH

# Score results
python scripts/gaia_scorer.py RESULT_FILE_PATH
```

## Citation

If you use this dataset or code, please cite our tech report:

```bibtex
@article{gaia-v2-lilt2026,
  title =   {GAIA-v2-LILT: Multilingual Adaptation of Agent Benchmark beyond Translation},
  author =  {Yunsu Kim and Kaden Uhlig and Joern Wuebker},
  journal = {arXiv preprint arXiv:2604.24929},
  year =    {2026}
}
```
