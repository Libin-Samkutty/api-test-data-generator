**Project Name:** `api-test-data-generator`
**Language:** Python 3.11+
**Project Type:** CLI-based tool + importable package
**Purpose:** Generate structured, customizable test data for API functional, integration, and load testing.

---

## 1. Objectives

* Generate realistic and deterministic test data.
* Support JSON payload generation for REST APIs.
* Allow schema-driven data generation.
* Enable bulk dataset creation.
* Provide seeding for reproducibility.
* Export data in JSON / CSV.
* Integrate easily with pytest or other API test frameworks.

---

## 2. Functional Requirements

### 2.1 Core Capabilities

1. Generate data based on:

   * Predefined templates
   * JSON Schema
   * YAML config
   * Inline CLI definitions

2. Support field types:

   * string
   * integer
   * float
   * boolean
   * enum
   * array
   * nested object
   * date / datetime
   * UUID
   * email
   * phone
   * address
   * custom regex

3. Deterministic output:

   * Seed-based randomization

4. Bulk generation:

   * Generate N records via CLI or config

5. Export formats:

   * JSON (default)
   * CSV

6. Validation:

   * JSON Schema validation before export

---

## 3. Non-Functional Requirements

* Modular architecture
* 90%+ unit test coverage
* CLI execution < 2 seconds for 10k records
* Type hints everywhere
* PEP8 compliance
* Logging support
* Extensible via plugins

---

## 4. System Architecture

```
api_test_data_generator/
│
├── generator/
│   ├── core.py
│   ├── schema_loader.py
│   ├── field_types.py
│   ├── validators.py
│
├── exporters/
│   ├── json_exporter.py
│   ├── csv_exporter.py
│
├── cli/
│   ├── main.py
│
├── utils/
│   ├── randomizer.py
│   ├── seed_manager.py
│
├── tests/
│
├── pyproject.toml
└── README.md
```

---

## 5. Dependencies

Mandatory:

* faker
* pydantic
* jsonschema
* typer (CLI)
* pytest

Optional:

* pandas (CSV optimization)
* rich (CLI output formatting)

---

## 6. CLI Specification

### Base Command

```
api-gen generate
```

### Arguments

| Flag     | Description              | Required           |
| -------- | ------------------------ | ------------------ |
| --schema | Path to JSON/YAML schema | Yes                |
| --count  | Number of records        | No (default: 1)    |
| --output | Output file path         | Yes                |
| --format | json / csv               | No (default: json) |
| --seed   | Integer seed             | No                 |

### Example

```
api-gen generate --schema user_schema.json --count 1000 --output users.json --seed 42
```

---

## 7. Schema Definition Example

### JSON Schema Example

```json
{
  "type": "object",
  "properties": {
    "user_id": { "type": "string", "format": "uuid" },
    "name": { "type": "string", "faker": "name" },
    "email": { "type": "string", "faker": "email" },
    "age": { "type": "integer", "minimum": 18, "maximum": 60 },
    "is_active": { "type": "boolean" }
  },
  "required": ["user_id", "email"]
}
```

---

## 8. Core Module Design

### 8.1 Generator Engine

Class: `DataGenerator`

Responsibilities:

* Load schema
* Resolve field types
* Generate record
* Apply constraints
* Return dict object

Public Methods:

```python
generate_record() -> dict
generate_bulk(count: int) -> list[dict]
```

---

### 8.2 Field Type Handlers

Strategy Pattern:

```python
class BaseFieldGenerator:
    def generate(self, config: dict) -> Any:
        pass
```

Concrete Implementations:

* StringGenerator
* IntegerGenerator
* BooleanGenerator
* UUIDGenerator
* FakerFieldGenerator
* EnumGenerator
* ArrayGenerator
* ObjectGenerator

---

### 8.3 Seed Management

* Single global seed
* Faker seed synchronization
* Random module seed

---

## 9. Error Handling

Custom Exceptions:

* SchemaLoadError
* UnsupportedFieldTypeError
* ValidationError
* ExportError

---

## 10. Logging

* DEBUG: field-level generation
* INFO: file export success
* ERROR: schema validation failures

---

## 11. Testing Strategy

### Unit Tests

* Field generators
* Schema parsing
* Deterministic behavior
* Exporters

### Integration Tests

* End-to-end CLI generation
* JSON schema validation

### Edge Cases

* Empty schema
* Invalid constraints
* Deeply nested objects
* Large dataset performance

---

## 12. CI/CD

* GitHub Actions:

  * Lint (flake8)
  * Test (pytest)
  * Coverage threshold check
  * Build package
  * Publish to PyPI (tag-based)

---

## 13. Packaging

* PEP 517 compliant
* Build via:

```
python -m build
```

* CLI entry point in `pyproject.toml`:

```toml
[project.scripts]
api-gen = "cli.main:app"
```

---

## 14. Future Enhancements

* Database seeding mode
* GraphQL schema support
* OpenAPI spec auto-import
* Mock server mode
* Web UI for schema builder

---

## 15. Definition of Done

* CLI generates valid schema-compliant payloads
* Deterministic output with seed
* Test coverage >= 90%
* Packaged and installable via pip
* Documented with usage examples
* Works cross-platform (Linux, Mac, Windows)
