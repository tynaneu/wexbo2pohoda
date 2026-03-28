# Wexbo to Pohoda

A Python tool that converts e-shop XML exports to Pohoda accounting software format.

## Requirements

- Python >= 3.9

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the main script:

```bash
python src/wexbo2pohoda/wexbo2pohoda.py
```

A file dialog will appear to select the XML export file from your e-shop.

## Testing

Run integration tests:

```bash
pytest tests/
```

## Project Structure

```
wexbo2pohoda/
├── src/
│   └── wexbo2pohoda/
│       └── wexbo2pohoda.py
├── tests/
│   ├── fixtures/
│   │   └── sample_export.xml
│   └── test_integration.py
├── requirements.txt
├── .gitignore
└── README.md
```
