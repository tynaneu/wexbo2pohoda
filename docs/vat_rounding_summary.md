## Technical Guide: Preserving Tax and Rounding in Pohoda XML Import

To ensure that Pohoda (Stormware) does not recalculate taxes or rounding and instead accepts the exact totals from your e-shop, follow these implementation rules.

### 1. Control the Tax Recalculation
By default, Pohoda attempts to validate and recalculate tax amounts based on the items provided. To prevent discrepancies caused by different rounding algorithms, you must **explicitly define the totals** in the summary section rather than letting the system derive them.

### 2. Mandatory Element: `<invoiceSummary>`
The key is to populate the `<homeCurrency>` (or `<foreignCurrency>`) element within the `<invoiceSummary>` block. Providing values here forces Pohoda to prioritize your data over its internal calculations.

* **Tax Base:** Use `<typ:priceLow>` (reduced rate) or `<typ:priceHigh>` (standard rate).
* **VAT Amount:** Use `<typ:priceLowVAT>` or `<typ:priceHighVAT>`.
* **Total with VAT:** Use `<typ:priceLowSum>` or `<typ:priceHighSum>`.

### 3. Handling Rounding Differences
E-shops often encounter "penny differences" (rounding errors). To ensure the final invoice total matches the e-shop payment exactly:
* Use the **`<typ:round>`** element within `<homeCurrency>`.
* Map any discrepancy between the sum of items and the final paid amount to the **`<typ:priceRound>`** tag. This creates a "rounding adjustment" entry in Pohoda.

### 4. Item Level Configuration
In the `<invoiceItem>` section, use the following attributes to maintain consistency:
* **`payVAT`**: Set to `false` if you are providing the unit price and want Pohoda to respect your pre-calculated tax.
* **`roundingVAT`**: Set to `none` if you want to avoid per-item rounding and handle rounding only at the document level.

### Implementation Snippet (Example)
```xml
<inv:invoiceSummary>
    <inv:homeCurrency>
        <typ:priceHigh>1000.00</typ:priceHigh>
        <typ:priceHighVAT>210.00</typ:priceHighVAT>
        <typ:priceHighSum>1210.00</typ:priceHighSum>
        <typ:round>
            <typ:priceRound>0.40</typ:priceRound>
        </typ:round>
    </inv:homeCurrency>
</inv:invoiceSummary>
```
