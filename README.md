# api-test-data-generator

A tool that automatically creates realistic fake data for testing your APIs — no more writing test data by hand.

You describe what your data should look like (using a simple schema file), and this tool generates as macny records as you need, ready to use in your tests.

---

## Table of Contents

- [What does it do?](#what-does-it-do)
- [How it works — the big picture](#how-it-works--the-big-picture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Step 1 — Create a schema file](#step-1--create-a-schema-file)
- [Step 2 — Generate data from the terminal](#step-2--generate-data-from-the-terminal)
- [Step 3 — Use it inside Python or pytest](#step-3--use-it-inside-python-or-pytest)
- [All CLI options explained](#all-cli-options-explained)
- [Schema field types — full reference](#schema-field-types--full-reference)
- [Real-world schema examples](#real-world-schema-examples)
- [Common recipes](#common-recipes)
- [Using with pytest](#using-with-pytest)
- [Exporting to CSV](#exporting-to-csv)
- [Reproducible data with seeds](#reproducible-data-with-seeds)
- [Error messages and what they mean](#error-messages-and-what-they-mean)
- [Development setup](#development-setup)
- [Project structure](#project-structure)
- [Platform quick reference](#platform-quick-reference)
- [FAQ](#faq)

---

## What does it do?

Imagine you are building a user registration API and want to test it with 1000 different users. Writing those users by hand would take hours. With this tool you just:

1. Describe what a user looks like (name, email, age, etc.) in a schema file
2. Run one command
3. Get a ready-to-use JSON or CSV file with 1000 realistic users

---

## How it works — the big picture

```
Your schema file          This tool              Output file
(what data looks like) → (generates records) → (users.json / users.csv)

user_schema.json   →   api-gen generate   →   users.json
```

A **schema file** is just a description of your data. For example:

> "I want records that each have a user ID (UUID format), a name, an email address, and an age between 18 and 60."

The tool reads that description and creates as many records as you ask for.

---

## Requirements

- Python 3.11 or higher
- pip (comes with Python)

Check your Python version by running:

```bash
python --version
```

---

## Installation

**Linux / macOS**
```bash
# Basic install
pip install api-test-data-generator

# Full install — includes pandas (faster CSV) and rich (prettier terminal output)
pip install "api-test-data-generator[all]"
```

**Windows (PowerShell)**
```powershell
# Basic install
pip install api-test-data-generator

# Full install — use cmd /c to avoid a PowerShell bracket issue
cmd /c "pip install api-test-data-generator[all]"
```

**Windows (Command Prompt)**
```cmd
pip install api-test-data-generator[all]
```

After installing, verify it worked:

```bash
api-gen --help
```

You should see a help message listing the available commands.

---

## Step 1 — Create a schema file

A schema file tells the tool what your data should look like. You can write it in **JSON** or **YAML** — use whichever you prefer.

Create a file called `user_schema.json`:

```json
{
  "type": "object",
  "properties": {
    "user_id":   { "type": "string", "format": "uuid" },
    "name":      { "type": "string", "faker": "name" },
    "email":     { "type": "string", "format": "email" },
    "age":       { "type": "integer", "minimum": 18, "maximum": 60 },
    "is_active": { "type": "boolean" }
  },
  "required": ["user_id", "email"]
}
```

What each line means:
- `"format": "uuid"` — generate a unique ID like `550e8400-e29b-41d4-a716-446655440000`
- `"faker": "name"` — generate a realistic full name like `"Sarah Johnson"`
- `"format": "email"` — generate a valid email like `"sarah.johnson@example.com"`
- `"minimum": 18, "maximum": 60` — age will always be between 18 and 60
- `"required": [...]` — these fields will always be present in every record

---

## Step 2 — Generate data from the terminal

Once you have a schema file, run this command to generate data.

**Linux / macOS**
```bash
api-gen generate \
  --schema user_schema.json \
  --count 100 \
  --output users.json
```

**Windows (PowerShell)**
```powershell
api-gen generate `
  --schema user_schema.json `
  --count 100 `
  --output users.json
```

**Windows (Command Prompt)**
```cmd
api-gen generate --schema user_schema.json --count 100 --output users.json
```

This creates a `users.json` file with 100 user records. Open it and you will see something like:

```json
[
  {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Sarah Johnson",
    "email": "sarah.johnson@example.com",
    "age": 34,
    "is_active": true
  },
  {
    "user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "name": "Michael Torres",
    "email": "m.torres@example.org",
    "age": 27,
    "is_active": false
  }
]
```

---

## Step 3 — Use it inside Python or pytest

You can also use the tool directly in your Python code without going to the terminal.

### Generate a single record

```python
from api_test_data_generator.generator import DataGenerator

# Load your schema and create a generator
gen = DataGenerator.from_file("user_schema.json")

# Generate one record
user = gen.generate_record()
print(user)
# {'user_id': '550e8400-...', 'name': 'Sarah Johnson', 'email': 'sarah@example.com', 'age': 34}
```

### Generate many records at once

```python
from api_test_data_generator.generator import DataGenerator

gen = DataGenerator.from_file("user_schema.json")

# Generate 500 records
users = gen.generate_bulk(500)
print(f"Generated {len(users)} users")
print(users[0])  # print the first one
```

### Define the schema directly in Python (no file needed)

```python
from api_test_data_generator.generator import DataGenerator

schema = {
    "type": "object",
    "properties": {
        "order_id": {"type": "string", "format": "uuid"},
        "amount":   {"type": "number", "minimum": 1.0, "maximum": 999.99},
        "status":   {"enum": ["pending", "paid", "cancelled"]}
    },
    "required": ["order_id", "amount", "status"]
}

gen = DataGenerator.from_dict(schema)
order = gen.generate_record()
print(order)
# {'order_id': '...', 'amount': 47.83, 'status': 'paid'}
```

### Export to a file from Python

```python
from api_test_data_generator.generator import DataGenerator
from api_test_data_generator.exporters import export_json, export_csv

gen = DataGenerator.from_file("user_schema.json", seed=42)
users = gen.generate_bulk(1000)

# Save as JSON
export_json(users, "output/users.json")

# Save as CSV
export_csv(users, "output/users.csv")
```

---

## All CLI options explained

```
api-gen generate [OPTIONS]
```

| Option | What it does | Required? | Default |
|--------|-------------|-----------|---------|
| `--schema PATH` | Path to your schema file (.json or .yaml) | Yes | — |
| `--count INT` | How many records to generate | No | 1 |
| `--output PATH` | Where to save the output file | Yes | — |
| `--format TEXT` | File format: `json` or `csv` | No | `json` |
| `--seed INT` | A number to make output repeatable (same seed = same data every time) | No | Random |
| `--no-validate` | Skip checking the output against the schema | No | Validates by default |
| `--verbose` | Show detailed logs while generating | No | Off |

### Examples

Generate 1 record (useful for a quick check):
```bash
# Linux / macOS
api-gen generate --schema user_schema.json --output one_user.json

# Windows PowerShell
api-gen generate --schema user_schema.json --output one_user.json
```

Generate 10 000 records in CSV format:
```bash
# Linux / macOS
api-gen generate \
  --schema user_schema.json \
  --count 10000 \
  --output users.csv \
  --format csv

# Windows PowerShell
api-gen generate `
  --schema user_schema.json `
  --count 10000 `
  --output users.csv `
  --format csv

# Windows Command Prompt
api-gen generate --schema user_schema.json --count 10000 --output users.csv --format csv
```

Generate the same data every time (useful for repeatable tests):
```bash
# Linux / macOS
api-gen generate --schema user_schema.json --count 50 --output users.json --seed 42

# Windows PowerShell
api-gen generate --schema user_schema.json --count 50 --output users.json --seed 42

# Windows Command Prompt
api-gen generate --schema user_schema.json --count 50 --output users.json --seed 42
```

Show verbose logs (useful for debugging):
```bash
# Linux / macOS
api-gen generate --schema user_schema.json --output users.json --verbose

# Windows PowerShell / Command Prompt
api-gen generate --schema user_schema.json --output users.json --verbose
```

---

## Schema field types — full reference

### Basic types

```json
{ "type": "string" }
```
Generates a random text string like `"XkLmpQrsT"`.

```json
{ "type": "string", "minLength": 5, "maxLength": 20 }
```
Generates a string between 5 and 20 characters long.

```json
{ "type": "integer", "minimum": 1, "maximum": 100 }
```
Generates a whole number between 1 and 100, e.g. `47`.

```json
{ "type": "number", "minimum": 0.0, "maximum": 99.99, "precision": 2 }
```
Generates a decimal number like `34.72`. `precision` controls decimal places.

```json
{ "type": "boolean" }
```
Generates `true` or `false` randomly.

---

### Formatted strings

```json
{ "type": "string", "format": "uuid" }
```
Generates a UUID like `"550e8400-e29b-41d4-a716-446655440000"`.

```json
{ "type": "string", "format": "email" }
```
Generates a valid email like `"john.smith@example.com"`.

```json
{ "type": "string", "format": "date" }
```
Generates a date like `"2023-07-15"`.

```json
{ "type": "string", "format": "date-time" }
```
Generates a datetime like `"2023-07-15T14:32:10"`.

```json
{ "type": "string", "format": "phone" }
```
Generates a phone number like `"+1-555-867-5309"`.

```json
{ "type": "object", "format": "address" }
```
Generates a full address as a nested object:
```json
{
  "street": "123 Main St",
  "city": "Springfield",
  "state": "Illinois",
  "country": "United States",
  "postal_code": "62701"
}
```

---

### Faker fields — use any realistic data type

The `"faker"` key lets you use any method from the [Faker library](https://faker.readthedocs.io/en/master/providers.html) to generate realistic data.

```json
{ "type": "string", "faker": "name" }
```
→ `"Sarah Johnson"`

```json
{ "type": "string", "faker": "first_name" }
```
→ `"Sarah"`

```json
{ "type": "string", "faker": "company" }
```
→ `"Acme Corp Ltd"`

```json
{ "type": "string", "faker": "job" }
```
→ `"Software Engineer"`

```json
{ "type": "string", "faker": "city" }
```
→ `"Nairobi"`

```json
{ "type": "string", "faker": "country" }
```
→ `"Kenya"`

```json
{ "type": "string", "faker": "url" }
```
→ `"https://www.example.com/page"`

```json
{ "type": "string", "faker": "sentence" }
```
→ `"The quick brown fox jumps over the lazy dog."`

```json
{ "type": "string", "faker": "word" }
```
→ `"discovery"`

> Tip: Browse all available faker providers at https://faker.readthedocs.io/en/master/providers.html

---

### Enum — choose from a fixed list

```json
{ "enum": ["active", "inactive", "pending"] }
```
Randomly picks one value from the list every time.

```json
{ "enum": ["admin", "user", "guest"] }
```
→ `"user"`

---

### Pattern — match a specific format using regex

```json
{ "type": "string", "pattern": "[A-Z]{2}\\d{4}" }
```
Generates strings matching the pattern, e.g. `"AB1234"` (2 uppercase letters followed by 4 digits).

```json
{ "type": "string", "pattern": "\\d{3}-\\d{2}-\\d{4}" }
```
→ `"123-45-6789"` (SSN-style format)

---

### Arrays — lists of items

```json
{
  "type": "array",
  "items": { "type": "string", "faker": "word" },
  "minItems": 1,
  "maxItems": 5
}
```
Generates a list of 1 to 5 random words, e.g. `["apple", "river", "quantum"]`.

```json
{
  "type": "array",
  "items": { "type": "integer", "minimum": 1, "maximum": 100 },
  "minItems": 3,
  "maxItems": 3
}
```
Generates exactly 3 random integers, e.g. `[42, 7, 88]`.

---

### Nested objects — data inside data

```json
{
  "type": "object",
  "properties": {
    "street": { "type": "string", "faker": "street_address" },
    "city":   { "type": "string", "faker": "city" },
    "zip":    { "type": "string", "faker": "postcode" }
  },
  "required": ["street", "city", "zip"]
}
```
Generates:
```json
{
  "street": "742 Evergreen Terrace",
  "city":   "Springfield",
  "zip":    "62701"
}
```

---

## Real-world schema examples

### E-commerce order

Save as `order_schema.json`:

```json
{
  "type": "object",
  "properties": {
    "order_id":       { "type": "string", "format": "uuid" },
    "customer_name":  { "type": "string", "faker": "name" },
    "customer_email": { "type": "string", "format": "email" },
    "status":         { "enum": ["pending", "confirmed", "shipped", "delivered", "cancelled"] },
    "total_amount":   { "type": "number", "minimum": 5.0, "maximum": 2000.0, "precision": 2 },
    "item_count":     { "type": "integer", "minimum": 1, "maximum": 20 },
    "created_at":     { "type": "string", "format": "date-time" },
    "shipping_address": {
      "type": "object",
      "properties": {
        "street":  { "type": "string", "faker": "street_address" },
        "city":    { "type": "string", "faker": "city" },
        "country": { "type": "string", "faker": "country" },
        "zip":     { "type": "string", "faker": "postcode" }
      },
      "required": ["street", "city", "country", "zip"]
    }
  },
  "required": ["order_id", "customer_email", "status", "total_amount"]
}
```

Generate 200 orders:
```bash
# Linux / macOS
api-gen generate --schema order_schema.json --count 200 --output orders.json

# Windows PowerShell
api-gen generate --schema order_schema.json --count 200 --output orders.json

# Windows Command Prompt
api-gen generate --schema order_schema.json --count 200 --output orders.json
```

---

### Healthcare patient record

Save as `patient_schema.yaml`:

```yaml
type: object
properties:
  patient_id:
    type: string
    format: uuid
  full_name:
    type: string
    faker: name
  date_of_birth:
    type: string
    format: date
  gender:
    enum:
      - male
      - female
      - other
      - prefer_not_to_say
  blood_type:
    enum:
      - A+
      - A-
      - B+
      - B-
      - AB+
      - AB-
      - O+
      - O-
  phone:
    type: string
    format: phone
  email:
    type: string
    format: email
  registered_at:
    type: string
    format: date-time
required:
  - patient_id
  - full_name
  - date_of_birth
  - blood_type
```

Generate 500 patient records:
```bash
# Linux / macOS
api-gen generate \
  --schema patient_schema.yaml \
  --count 500 \
  --output patients.json \
  --seed 42

# Windows PowerShell
api-gen generate `
  --schema patient_schema.yaml `
  --count 500 `
  --output patients.json `
  --seed 42

# Windows Command Prompt
api-gen generate --schema patient_schema.yaml --count 500 --output patients.json --seed 42
```

---

### Product catalogue

Save as `product_schema.json`:

```json
{
  "type": "object",
  "properties": {
    "product_id":   { "type": "string", "format": "uuid" },
    "name":         { "type": "string", "faker": "catch_phrase" },
    "sku":          { "type": "string", "pattern": "[A-Z]{3}-\\d{5}" },
    "category":     { "enum": ["electronics", "clothing", "food", "books", "home", "sports"] },
    "price":        { "type": "number", "minimum": 0.99, "maximum": 4999.99, "precision": 2 },
    "stock_count":  { "type": "integer", "minimum": 0, "maximum": 500 },
    "is_available": { "type": "boolean" },
    "tags": {
      "type": "array",
      "items": { "type": "string", "faker": "word" },
      "minItems": 1,
      "maxItems": 6
    },
    "created_at": { "type": "string", "format": "date-time" }
  },
  "required": ["product_id", "name", "sku", "category", "price"]
}
```

---

## Common recipes

### Generate a single record to check your schema is correct

```bash
# Linux / macOS
api-gen generate --schema user_schema.json --count 1 --output test.json && cat test.json

# Windows PowerShell
api-gen generate --schema user_schema.json --count 1 --output test.json; Get-Content test.json

# Windows Command Prompt
api-gen generate --schema user_schema.json --count 1 --output test.json && type test.json
```

### Generate data without validating (faster for large datasets)

Validation checks that every generated record matches your schema. Skipping it is safe when you trust your schema and need speed.

```bash
# Linux / macOS
api-gen generate --schema user_schema.json --count 50000 --output big_dataset.json --no-validate

# Windows PowerShell
api-gen generate --schema user_schema.json --count 50000 --output big_dataset.json --no-validate

# Windows Command Prompt
api-gen generate --schema user_schema.json --count 50000 --output big_dataset.json --no-validate
```

### Debug why a schema is not working

```bash
# Linux / macOS
api-gen generate --schema user_schema.json --count 1 --output debug.json --verbose

# Windows PowerShell / Command Prompt
api-gen generate --schema user_schema.json --count 1 --output debug.json --verbose
```

---

## Using with pytest

This is one of the most powerful ways to use the package — generate fresh test data automatically inside your tests.

### Basic example

```python
# tests/test_user_api.py
import pytest
import requests
from api_test_data_generator.generator import DataGenerator


@pytest.fixture
def user_generator():
    """Create a generator once, reuse it across tests."""
    return DataGenerator.from_file("schemas/user_schema.json", seed=42)


def test_create_user(user_generator):
    """Test that the API accepts a valid user."""
    user = user_generator.generate_record()

    response = requests.post("http://localhost:8000/users", json=user)

    assert response.status_code == 201
    assert response.json()["email"] == user["email"]


def test_create_100_users(user_generator):
    """Load test: create 100 users and verify all succeed."""
    users = user_generator.generate_bulk(100)

    for user in users:
        response = requests.post("http://localhost:8000/users", json=user)
        assert response.status_code == 201
```

### Parametrize tests with generated data

```python
import pytest
from api_test_data_generator.generator import DataGenerator


def get_test_users(count=5):
    gen = DataGenerator.from_file("schemas/user_schema.json", seed=99)
    return gen.generate_bulk(count)


@pytest.mark.parametrize("user", get_test_users(5))
def test_user_validation(user):
    """Run the same test for 5 different users."""
    assert "@" in user["email"]
    assert len(user["user_id"]) == 36  # UUID length
```

### Use inline schema — no file needed

```python
from api_test_data_generator.generator import DataGenerator


def test_order_processing():
    schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "format": "uuid"},
            "amount":   {"type": "number", "minimum": 1.0, "maximum": 500.0},
            "currency": {"enum": ["USD", "EUR", "GBP", "KES", "NGN"]}
        },
        "required": ["order_id", "amount", "currency"]
    }

    gen = DataGenerator.from_dict(schema, seed=1)
    orders = gen.generate_bulk(10)

    for order in orders:
        assert order["amount"] >= 1.0
        assert order["currency"] in ["USD", "EUR", "GBP", "KES", "NGN"]
```

---

## Exporting to CSV

CSV is useful when you want to load test data into Excel, a database, or a data pipeline.

### From the terminal

**Linux / macOS**
```bash
api-gen generate \
  --schema user_schema.json \
  --count 1000 \
  --output users.csv \
  --format csv \
  --seed 42
```

**Windows (PowerShell)**
```powershell
api-gen generate `
  --schema user_schema.json `
  --count 1000 `
  --output users.csv `
  --format csv `
  --seed 42
```

**Windows (Command Prompt)**
```cmd
api-gen generate --schema user_schema.json --count 1000 --output users.csv --format csv --seed 42
```

### From Python

```python
from api_test_data_generator.generator import DataGenerator
from api_test_data_generator.exporters import export_csv

gen = DataGenerator.from_file("user_schema.json", seed=42)
users = gen.generate_bulk(1000)

export_csv(users, "output/users.csv")
print("Saved 1000 users to output/users.csv")
```

**Note on nested fields in CSV:** If your schema has nested objects (like an address inside a user), the CSV will flatten them using dot notation. For example, `address.city` and `address.country` will each become their own column.

---

## Reproducible data with seeds

By default, every run generates different random data. If you need the **same data every time** — for example, to compare test results across runs or share data with a colleague — use the `--seed` option.

```bash
# These two commands produce identical output
# Linux / macOS
api-gen generate --schema user_schema.json --count 10 --output users.json --seed 42
api-gen generate --schema user_schema.json --count 10 --output users.json --seed 42

# Windows PowerShell / Command Prompt
api-gen generate --schema user_schema.json --count 10 --output users.json --seed 42
```

In Python:

```python
from api_test_data_generator.generator import DataGenerator

# Both generators produce the same records
gen1 = DataGenerator.from_file("user_schema.json", seed=42)
gen2 = DataGenerator.from_file("user_schema.json", seed=42)

records1 = gen1.generate_bulk(10)
records2 = gen2.generate_bulk(10)

assert records1 == records2  # Always True
```

Use a **different seed number** to get different (but still repeatable) data:

```bash
# Linux / macOS
api-gen generate --schema user_schema.json --count 10 --output dataset_a.json --seed 1
api-gen generate --schema user_schema.json --count 10 --output dataset_b.json --seed 2

# Windows PowerShell / Command Prompt
api-gen generate --schema user_schema.json --count 10 --output dataset_a.json --seed 1
api-gen generate --schema user_schema.json --count 10 --output dataset_b.json --seed 2
```

---

## Error messages and what they mean

| Error message | What it means | How to fix it |
|---|---|---|
| `Schema file not found` | The path to your schema file is wrong | Check the file path and make sure the file exists |
| `Failed to parse schema` | Your JSON or YAML file has a syntax error | Validate your JSON at [jsonlint.com](https://jsonlint.com) or your YAML at [yamllint.com](http://www.yamllint.com) |
| `Unsupported schema format` | You used a file extension other than `.json`, `.yaml`, or `.yml` | Rename your file to use one of those extensions |
| `Record failed schema validation` | A generated record does not match your schema | Check your schema for conflicting rules (e.g. minimum > maximum) |
| `Cannot export an empty record list to CSV` | You tried to export 0 records | Make sure `--count` is at least 1 |
| `No generator registered for type '...'` | You used an unsupported field type | See the [field types reference](#schema-field-types--full-reference) for valid options |

---

## Development setup

Follow these steps if you want to modify the code or contribute.

### 1. Clone or extract the project

```bash
# Linux / macOS
cd path/to/api_test_data_generator

# Windows PowerShell / Command Prompt
cd path\to\api_test_data_generator
```

### 2. Install in editable mode with all dependencies

**Linux / macOS**
```bash
pip install -e ".[dev,all]"
```

**Windows (PowerShell)**
```powershell
cmd /c "pip install -e .[dev,all]"
```

**Windows (Command Prompt)**
```cmd
pip install -e .[dev,all]
```

### 3. Run the tests

```bash
# All platforms
pytest
```

Run with more detail:
```bash
pytest -v
```

Run a specific test file:
```bash
pytest tests/test_field_types.py -v
```

Run without the coverage requirement:
```bash
pytest --no-cov
```

### 4. Check code style

```bash
# All platforms
flake8 api_test_data_generator/ --max-line-length=100
```

### 5. Build the package

```bash
# All platforms
pip install build
python -m build
```

The built files appear in `dist/`:
- `.whl` — installable wheel (use this for `pip install`)
- `.tar.gz` — source distribution

---

## Project structure

```
api_test_data_generator/
│
├── api_test_data_generator/     ← the actual package code
│   ├── generator/
│   │   ├── core.py              ← DataGenerator class (main entry point)
│   │   ├── schema_loader.py     ← reads .json and .yaml schema files
│   │   ├── field_types.py       ← one class per field type (string, integer, etc.)
│   │   ├── validators.py        ← checks generated data matches the schema
│   │   └── exceptions.py        ← custom error classes
│   │
│   ├── exporters/
│   │   ├── json_exporter.py     ← saves records as JSON
│   │   └── csv_exporter.py      ← saves records as CSV (flattens nested data)
│   │
│   ├── cli/
│   │   └── main.py              ← the "api-gen generate" command
│   │
│   └── utils/
│       ├── seed_manager.py      ← manages the random seed globally
│       └── randomizer.py        ← helper functions for random data
│
├── tests/                       ← 139 tests, 96% coverage
├── examples/
│   ├── user_schema.json         ← example user schema
│   └── order_schema.yaml        ← example order schema
├── pyproject.toml               ← package configuration
└── README.md
```

---

## Platform quick reference

| Task | Linux / macOS | Windows PowerShell | Windows CMD |
|---|---|---|---|
| Line continuation | `\` | `` ` `` (backtick) | `^` |
| Install with extras | `".[dev,all]"` | `cmd /c "pip install -e .[dev,all]"` | `.[dev,all]` |
| Path separator | `/` | `\` or `/` (both work) | `\` |
| Run pytest | `pytest` | `pytest` | `pytest` |
| Run flake8 | `flake8 pkg/` | `flake8 pkg/` | `flake8 pkg/` |
| Build package | `python -m build` | `python -m build` | `python -m build` |

---

## FAQ

**Q: How is this different from just writing test data by hand?**
Writing data by hand is fine for 5–10 records. This tool is useful when you need hundreds or thousands of records, need them to be realistic (real-looking names, emails, UUIDs), or need the same data to be reproducible across test runs.

**Q: Do I need to know JSON Schema to use this?**
Not deeply. The examples in this README cover the most common cases. You can copy and adapt them without knowing the full JSON Schema specification.

**Q: Will the same seed always produce the same data?**
Yes, as long as your schema does not change and you use the same version of the tool. If you update your schema, the same seed may produce different records.

**Q: My schema has a `"faker"` key but I am getting generic strings instead of names. Why?**
The faker method name might be misspelled. Check the full list of available methods at https://faker.readthedocs.io/en/master/providers.html. The tool falls back to a plain string silently if the method is not found.

**Q: Can I use this with any testing framework?**
Yes. It returns plain Python dicts and lists, so it works with pytest, unittest, or any other framework. You can also use it to pre-generate data files and load them separately.

**Q: How fast is it?**
Generating 10 000 records takes under 2 seconds on a standard laptop.

---

## License

MIT — free to use, modify, and distribute.