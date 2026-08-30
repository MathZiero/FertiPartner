# FertiPartner

## Overview

FertiPartner is a comprehensive platform designed to provide deep insights into the fertilizer market, catering to producers, distributors, and traders. The system ingests complex international trade data, processes it through a multi-stage pipeline, and presents it through intuitive analytical interfaces.

## Features

- **Multi-Source Data Ingestion**: Integrates data from various international sources related to agricultural production, fertilizer trade, and economic indicators.
- **Advanced Data Processing**: Includes validation, standardization, and transformation layers to ensure data quality.
- **Historical & Real-Time Analysis**: Supports both deep historical analysis and up-to-date market insights.
- **Interactive Visualization**: Provides graphical interfaces and key indicators for market analysis.
- **Domain-Specific Intelligence**: Focuses on market dynamics, pricing trends, production capacities, and trade flows.

## Architecture

The project follows a modern, modular architecture based on **Clean Architecture** and **Domain-Driven Design (DDD)**.

### Project Structure

```text
src/
├── app/
│   ├── domain/      # Business logic and core entities
│   ├── application/ # Use cases and orchestration
│   ├── infrastructure/ # External integrations (DB, APIs)
│   └── presentation/ # Interfaces (API, CLI)
├── infrastructure/   # Infrastructure configurations
└── presentation/     # Entry points (API, CLI)
```

### Layered Dependencies

- **Domain**: Contains business rules. Cannot depend on external layers.
- **Application**: Orchestrates the domain and external abstractions.
- **Infrastructure**: Implements external interfaces (databases, APIs).
- **Presentation**: Exposes the application (Web API, CLI).

## Getting Started

### Prerequisites

- Python 3.12+
- uv (Python package manager and resolver)

### Installation

1. Clone the repository.
2. Install dependencies using `uv`:

```bash
uv sync
```

## Documentation

For detailed documentation on architecture, ADRs (Architecture Decision Records), and engineering conventions, please refer to the `docs/` directory.

- [Architecture Overview](docs/architecture/overview.md)
- [Architecture Decision Records](docs/architecture/decisions/)
- [Engineering Conventions](docs/engineering/conventions.md)
- [Testing Strategy](docs/engineering/testing.md)
- [Definition of Done](docs/engineering/definition-of-done.md)
- [Agent Guidelines](AGENTS.md)