# CAPTCHA-Solving Agent

A research-grade agent that uses a locally-hosted vision language model (vLLM) to solve image-based CAPTCHAs. The agent automates browser interaction via Selenium, extracts CAPTCHA image grids, splits them into tiles, and classifies each tile using [LLaVA](https://llava-vl.github.io/) served through [Ollama](https://ollama.com/).

> **Disclaimer — Academic & Responsible Use Only**
>
> This project is built **purely for academic and research purposes**. It is intended as a proof-of-concept exploring how vision language models can interpret image-based challenges. It is **not** intended for bypassing security measures on production systems. CAPTCHAs exist to protect services from abuse — please respect website terms of service and applicable laws.

## How It Works

1. **Browser Automation** — Selenium drives a Firefox browser, fills in a search form, and detects when a reCAPTCHA challenge appears.
2. **CAPTCHA Extraction** — The agent locates the CAPTCHA iframe, reads the text prompt (e.g. *"Select all squares with traffic lights"*), and downloads the composite image grid.
3. **Image Splitting** — The grid image (3×3 or 4×4) is split into individual tiles, each base64-encoded.
4. **vLLM Classification** — Each tile is sent to a local Ollama instance running LLaVA. The model returns `1` (match) or `0` (no match) for each tile.
5. **Form Completion** — Matching tiles are clicked and the CAPTCHA is submitted.

## Prerequisites

| Requirement | Notes |
|---|---|
| **macOS** (Apple Silicon or Intel) | Tested on 16 GB RAM — works for research/demo loads |
| **Python 3.10+** | |
| **Firefox** | Selenium drives Firefox via GeckoDriver |
| **Ollama** | Local LLM runtime |

## Setup

### 1. Install Ollama & Pull the Model

```bash
# Install Ollama (macOS)
brew install ollama

# Start the Ollama server (runs on http://localhost:11434 by default)
ollama serve

# In another terminal, pull the LLaVA model (~4.7 GB)
ollama pull llava
```

> **Memory Note:** LLaVA (7B) fits comfortably within 16 GB RAM on Mac. Ollama handles quantisation automatically. For tighter memory, you can also try `ollama pull llava:7b-v1.6-mistral-q4_0` for a smaller quantised variant.

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install GeckoDriver

```bash
brew install geckodriver
```

## Usage

Make sure Ollama is running (`ollama serve`) with the LLaVA model pulled, then:

```bash
cd src/
python main.py ../config.json
```

The agent will open Firefox, navigate to the configured URL, fill in search queries, and attempt to solve any CAPTCHA challenges that appear.

### Configuration

`config.json` contains the target URL and CSS/XPath selectors:

```json
{
    "URL": "https://iam.uiowa.edu/whitepages/search",
    "SELECTORS": { ... },
    "NAMES": ["THOMAS S GRUCA", ...]
}
```

The Ollama endpoint and model are configured in `src/decaptcha.py`:

```python
config = {
    "model": "llava",
    "prompt": "Respond with 1 if image has a {target}, else 0.",
    "server_url": "http://localhost:11434/api/generate",
    "api_timeout": 200
}
```

## Project Structure

```
├── README.md
├── config.json          # Target URL, selectors, and search names
├── requirements.txt     # Python dependencies
├── test_log.ini         # Logging configuration
└── src/
    ├── main.py          # Entry point — orchestrates the scraping workflow
    ├── agent.py         # CAPTCHA detection & solving workflow (Selenium)
    ├── decaptcha.py     # Image splitting, encoding, and vLLM classification
    ├── state.py         # State file management for batch processing
    └── utils.py         # Browser helpers, form filling, image download
```

## Known Limitations & Future Directions

- **3×3 and 4×4 grids** are supported; dynamic/animated CAPTCHAs are not.
- **Single-pass classification** — no retry logic if the model is uncertain. A confidence-threshold or retry mechanism would improve accuracy.
- **Sequential tile classification** — tiles are classified one at a time. Batching or a single multi-image prompt could improve throughput.
- **Model accuracy** — LLaVA 7B is sufficient for demo purposes but is not optimised for this task. Fine-tuning or using a larger model would improve results.

## License

This project is provided as-is for educational purposes. No warranty is expressed or implied.
