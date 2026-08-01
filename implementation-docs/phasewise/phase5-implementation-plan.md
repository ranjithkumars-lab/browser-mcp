# Phase 5: Web Scraping Plugin Implementation Plan

## 1. Phase Goal
Develop a production-grade **Web Scraping Plugin** leveraging the Phase 4 Plugin Framework and Phase 3 Element Engine. This plugin provides structured, robust data extraction tools allowing the AI assistant to fetch information reliably from web pages without hallucination.

## 2. Architectural Context
Phase 5 introduces the `scraper` package within the `plugins/` directory.

### Proposed Architecture & Pipeline
We will implement a clean data processing pipeline:
`Tool → Collector → Normalizer → Formatter → Response`

```text
src/browser_mcp/
├── plugins/
│   └── scraper/              # The Web Scraping Plugin
│       ├── __init__.py
│       ├── plugin.yaml       # Plugin manifest
│       ├── models.py         # Typed models (TextResult, TableResult, ProductResult, etc.)
│       ├── collectors/       # Gathers raw data from DOM elements
│       │   ├── text.py
│       │   ├── table.py
│       │   ├── images.py
│       │   ├── metadata.py
│       │   ├── jsonld.py
│       │   └── links.py
│       ├── normalizers/      # Cleans and sanitizes collected data
│       ├── formatters/       # Output converters
│       │   ├── json.py
│       │   ├── csv.py
│       │   ├── markdown.py
│       │   ├── html.py
│       │   ├── xml.py        # (Reserved)
│       │   └── yaml.py       # (Reserved)
│       └── tools.py          # MCP tool registrations
```

## 3. Scope of Tools

The plugin exposes the following tools under the `browser.scrape` namespace:
- `browser.scrape.text`: Extracts visible text.
- `browser.scrape.tables`: Extracts structured `<table/>` data.
- `browser.scrape.images`: Extracts `<img>` tags (src, resolved URL, alt, dimensions, loading attr).
- `browser.scrape.metadata`: Extracts `<meta>`, `<title>`, OpenGraph, and Twitter card data.
- `browser.scrape.jsonld`: Extracts embedded `application/ld+json` schemas.
- `browser.scrape.links`: Extracts `<a>` tags with strict URL normalization (relative to absolute, duplicates removed).
- `browser.scrape.products`: *Composite tool* that aggregates data sequentially from JSON-LD → Open Graph → Microdata → Visible DOM → Meta tags.

### Output Formatting & Large Payloads
Formatters consume the typed models. Output configuration:
- Small artifacts: Returned inline in the MCP response as structured text (JSON, CSV, Markdown, HTML).
- Large artifacts: Saved to the configured scratch/artifact storage, returning metadata and the filepath identifier.

## 4. Advanced Features
- **Deterministic Scope**: We will focus purely on general-purpose structured extraction from the *current page*. Distributed scraping, recursive traversal, and infinite scrolling are out of scope.
- **Error Handling**: 
  ```text
  BrowserError
  └── ScraperError
      ├── ExtractionError
      ├── FormattingError
      ├── PaginationError
      └── ProductExtractionError
  ```
- **Event Bus Integration**: 
  - `scrape.started`
  - `scrape.collect.completed`
  - `scrape.format.completed`
  - `scrape.completed`
  - `scrape.failed`

## 5. Definition of Done
- `plugin.yaml` manifest defined.
- Scrape Pipeline (`Collector → Normalizer → Formatter`) fully implemented.
- Typed `models.py` strictly mapping collected results.
- Product composite collector uses multi-signal priority extraction.
- HTML fixtures added (`table.html`, `metadata.html`, `jsonld.html`, `microdata.html`, `links.html`, `images.html`, `ecommerce.html`).
- Unit and Integration tests achieving >90% coverage.
- Documentation created at `docs/plugins/scraper/` including `output-models.md`.
