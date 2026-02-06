# Changelog

All notable changes to this project will be documented in this file.

## [0.1.3] - 2026-02-06

### Added

- **Model Configuration UI**: Added sidebar controls to configure LLM provider (Google/OpenAI), base URL, and API keys directly in the interface.
- **Config Persistence**: Settings are now saved to `.user_config.json` and persist across sessions.
- **Git Ignore**: Added `CV.pdf`, `job.txt`, and `.user_config.json` to `.gitignore`.

### Changed

- **Async Handling**: Improved event loop management in `main.py` for Streamlit compatibility.
- **Cleanup**: Removed unused `lru_cache` decorators and unused imports across multiple files (`combined_reviewer.py`, `job_parser.py`, tests).
- **CLI**: Fixed f-string formatting in `cli.py`.

## [0.1.2] - 2026-02-02

### Fixed

- **Windows Compatibility**: Fixed `UnicodeEncodeError` in `cache.py` by enforcing UTF-8 encoding.
- **Local LLM Stability**: Added fallback to Ollama embeddings (`nomic-embed-text`) in `VectorSimilarityMatcher` when Google API key is missing.
- **Tool Support**: Fixed `AIGeneratedDetector` crash by switched agent to use tool-capable `qwen3:14b` model instead of `llama3.2:3b`.

### Changed

- Updated default configuration to use `qwen3:14b` (Optimizer) and `qwen3-vl:8b` (Reviewer).
