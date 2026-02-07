# HR-Breaker

Resume optimization tool that transforms any resume into a job-specific, ATS-friendly PDF.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)

## Features

- **Any format in** - LaTeX, plain text, markdown, HTML, PDF
- **Optimized PDF out** - Single-page, professionally formatted
- **LLM-powered optimization** - Tailors content to job requirements
- **Minimal changes** - Preserves your content, only restructures for fit
- **No fabrication** - Hallucination detection prevents made-up claims
- **Opinionated formatting** - Follows proven resume guidelines (one page, no fluff, etc.)
- **Multi-filter validation** - ATS simulation, keyword matching, structure checks
- **Web UI + CLI** - Streamlit dashboard or command-line
- **Debug mode** - Inspect optimization iterations

## How It Works

1. Upload resume in any supported format (PDF, LaTeX, markdown, txt)
2. Provide job posting URL or text description
3. LLM extracts content and generates optimized HTML resume
4. System runs internal filters (ATS simulation, keyword matching, hallucination detection)
5. If filters reject, regenerates using feedback
6. When all checks pass, renders HTML→PDF via WeasyPrint

## Quick Start

```bash
# Install
uv sync

# Configure (non-secret settings)
cp .env.example .env

# Configure (secrets: OpenAI keys; this file is gitignored)
cp .env.openai_keys.example .env.openai_keys
# Edit .env.openai_keys and set one of:
# - OPENAI_API_KEYS=sk-...,sk-...
# - OPENAI_API_KEY=sk-...
# - OPENAI_API_KEY_1=sk-... (+ OPENAI_API_KEY_2, ...)

# Run Web UI
uv run streamlit run src/hr_breaker/main.py
```

### PDF Rendering Prereqs (WeasyPrint)

HR-Breaker renders HTML to PDF via WeasyPrint.

- macOS (Homebrew):
  - `brew install pango gdk-pixbuf libffi`
  - Then run with: `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib uv run streamlit run src/hr_breaker/main.py`
- Windows:
  - Install GTK3 runtime from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
  - Ensure "Set up PATH environment variable" is checked during install.

## Docker

### Web UI (recommended)

```bash
# 1) Configure
cp .env.example .env
cp .env.openai_keys.example .env.openai_keys
# Edit .env.openai_keys and set your OpenAI key(s)

# 2) Build
docker compose build

# 3) Run
docker compose up
```

Open http://localhost:8501

### One-off run (no compose)

```bash
docker build -t hr-breaker .
docker run --rm -p 8501:8501 --env-file .env --env-file .env.openai_keys \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/.cache:/app/.cache" \
  hr-breaker
```

## Usage

### Web UI

Launch with `uv run streamlit run src/hr_breaker/main.py`

1. Paste or upload resume
2. Enter job URL or description
3. Click optimize
4. Download PDF

### CLI

```bash
# From URL
uv run hr-breaker optimize resume.pdf https://example.com/job

# From job description file
uv run hr-breaker optimize resume.txt job.txt

# Debug mode (saves iterations)
uv run hr-breaker optimize resume.txt job.txt -d

# Lenient mode - relaxes content constraints but still prevents fabricating experience. Use with caution!
uv run hr-breaker optimize resume.txt job.txt --no-shame

# List generated PDFs
uv run hr-breaker list
```

## Output

- Final PDFs: `output/<name>_<company>_<role>.pdf`
- Debug iterations: `output/debug_<company>_<role>/`
- Records: `output/index.json`

## Configuration

This branch uses OpenAI (or OpenAI-compatible) models.

- Non-secret config: copy `.env.example` to `.env` and override what you need (models, base URL, etc.).
- Secrets: copy `.env.openai_keys.example` to `.env.openai_keys` and set your OpenAI key(s).

Supported key formats:

- `OPENAI_API_KEYS="k1,k2,k3"` (comma/space/newline separated)
- `OPENAI_API_KEY="k1"` (single key fallback)
- `OPENAI_API_KEY_1`, `OPENAI_API_KEY_2`, ... (ordered)

Optional UI auth (useful for deployments):

- `HR_BREAKER_AUTH_ENABLED=true`
- `HR_BREAKER_AUTH_USERNAME=...`
- `HR_BREAKER_AUTH_PASSWORD=...`

---

## Architecture

```
src/hr_breaker/
├── agents/          # Pydantic-AI agents (optimizer, reviewer, etc.)
├── filters/         # Validation plugins (ATS, keywords, hallucination)
├── services/        # Rendering, scraping, caching
│   └── scrapers/    # Job scraper implementations
├── models/          # Pydantic data models
├── orchestration.py # Core optimization loop
├── main.py          # Streamlit UI
└── cli.py           # Click CLI
```

**Filters** (run by priority):

- 0: ContentLengthChecker - Size check
- 1: DataValidator - HTML structure validation
- 3: HallucinationChecker - Detect fabricated claims not supported by original resume
- 4: KeywordMatcher - TF-IDF matching
- 5: LLMChecker - Visual formatting check and LLM-based ATS simulation
- 6: VectorSimilarityMatcher - Semantic similarity
- 7: AIGeneratedChecker - Detect AI-sounding text

## Development

```bash
# Run tests
uv run pytest tests/

# Install dev dependencies
uv sync --group dev
```
