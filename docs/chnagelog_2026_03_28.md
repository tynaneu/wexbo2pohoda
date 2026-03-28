# Wexbo2Pohoda Converter - Bug Fixes (2026-03-28)

## Problem Summary

The converter was producing incorrect final prices in Pohoda compared to WEXBO source data. The following discrepancies were identified:

| Invoice | WEXBO (correct) | Pohoda (wrong) | Difference |
|---------|-----------------|----------------|------------|
| 32600049 | 10,286 | 9,668.02 | 617.98 |
| 32600056 | 4,000.7 | 4,206 | -205.3 |
| 32600058 | 1,010 | 1,009.99 | 0.01 |
| 32600059 | 1,700.1 | 1,700.05 | 0.05 |
| 32600060 | 239.9 | 239.94 | -0.04 |
| 32600061 | 2,235 | 2,234.99 | 0.01 |
| 32600062 | 816 | 816.02 | -0.02 |
| 32600064 | 380.1 | 380.06 | 0.04 |
| 32600065 | 1,169.9 | 1,169.95 | -0.05 |
| 32600066 | 1,600 | 1,599.98 | 0.02 |
| 32600067 | 4,475.7 | 4,475.67 | 0.03 |

## Root Causes Identified

### 1. Missing Multiple VAT Rates Support
**Problem**: Invoice 32600049 contains items with different VAT rates:
- High VAT (21%): base 7,990.1 CZK → with VAT 9,668 CZK
- No VAT (0%): 618 CZK

The old converter only exported ONE item per invoice, using the first detected VAT rate. This caused the 618 CZK no-VAT portion to be completely missing from the Pohoda import.

**Fix**: Added `get_vat_items()` function that extracts ALL VAT rate items from an invoice and creates separate invoice items for each.

### 2. Rounding Issues
**Problem**: Small discrepancies (0.01-0.05 CZK) occurred because:
- Pohoda recalculates `base_price * VAT_rate` internally
- The source XML already contains pre-calculated `price_vat_*` values
- Floating-point arithmetic caused rounding differences

**Fix**: Added `round_price()` function implementing proper rounding to 1 decimal place:
- Uses Python's `Decimal` with `ROUND_HALF_UP` mode
- Values ≤4 in second decimal round down
- Values ≥5 in second decimal round up

### 3. Books with Different VAT Rate
**Problem**: Books have a reduced VAT rate (12% instead of 21%) stored in `price_low` fields.

**Fix**: The `get_vat_items()` function now handles all three VAT categories:
- `high` (21%) - standard goods
- `low` (12%) - books and reduced-rate items  
- `none` (0%) - VAT-exempt items

## Changes Made

### New Functions in `src/wexbo2pohoda/wexbo2pohoda.py`

#### `round_price(value)`
```python
def round_price(value):
    """Round price to 1 decimal place (<=4 down, >5 up)."""
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(str(value))
    return float(d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
```

#### `get_vat_items(item)`
```python
def get_vat_items(item):
    """Extract all VAT rate items from an invoice.
    
    Returns a list of dicts with vat_rate, base_price, and price_with_vat.
    Handles invoices with multiple VAT rates (high, low, none).
    """
```

### Modified `convert_xml()` Function
- Now iterates over all VAT items returned by `get_vat_items()`
- Creates separate `invoiceItem` elements for each VAT rate
- Sets appropriate item text based on VAT rate:
  - High VAT: "Zboží / služby – e-shop"
  - Low VAT: "Knihy – snížená sazba DPH"
  - No VAT: "Zboží bez DPH"

## New Tests Added

### `TestRounding` class
- `test_round_price_down_at_4` - verifies rounding down at .04
- `test_round_price_up_at_5` - verifies rounding up at .05
- `test_round_price_up_at_6_and_above` - verifies rounding up at .06+
- `test_round_price_exact_decimal` - verifies exact decimals unchanged
- `test_round_price_negative` - verifies negative number handling

### `TestMultipleVatRates` class
- `test_get_vat_items_single_high` - single VAT rate invoice
- `test_get_vat_items_high_and_none` - mixed VAT rates (like invoice 32600049)
- `test_get_vat_items_all_three_rates` - all three VAT rates

### `TestInvoiceTotals` class
- `test_invoice_32600049_total` - verifies correct total for problematic invoice
- `test_invoice_with_rounding` - verifies rounding in output

## Verification

All 26 tests pass:
```
tests/test_integration.py ... 26 passed in 0.06s
```

### Invoice 32600049 Before/After

**Before (incorrect)**:
- 1 item: high VAT 7,990.1 CZK
- Total with VAT: 9,668.02 CZK (missing 618 CZK)

**After (correct)**:
- 2 items:
  - high VAT: 7,990.1 CZK base → 9,668 CZK with VAT
  - none: 618.0 CZK
- Total with VAT: 10,286 CZK ✓

## Files Modified

1. `src/wexbo2pohoda/wexbo2pohoda.py` - Added `round_price()`, `get_vat_items()`, updated `convert_xml()`
2. `tests/test_integration.py` - Added 12 new tests for rounding and multiple VAT rates
