# Changelog

All notable changes to this project will be documented in this file.

## [0.1.2] - 2026-02-02

### Fixed

- **Windows Compatibility**: Fixed `UnicodeEncodeError` in `cache.py` by enforcing UTF-8 encoding.
- **Local LLM Stability**: Added fallback to Ollama embeddings (`nomic-embed-text`) in `VectorSimilarityMatcher` when Google API key is missing.
- **Tool Support**: Fixed `AIGeneratedDetector` crash by switched agent to use tool-capable `qwen3:14b` model instead of `llama3.2:3b`.

### Changed

- Updated default configuration to use `qwen3:14b` (Optimizer) and `qwen3-vl:8b` (Reviewer).
