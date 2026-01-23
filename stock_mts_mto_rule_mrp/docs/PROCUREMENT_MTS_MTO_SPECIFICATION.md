# MTS+MTO Rule MRP - Procurement Specification

## Overview

This module extends the OCA `stock_mts_mto_rule` module to support MTS+MTO (Make-to-Stock + Make-to-Order) procurement rules for manufacturing (MRP) operations.

## Configuration

### Warehouse Settings

Navigate to: **Inventory > Configuration > Warehouses**

Select a warehouse and find the following settings under the warehouse form:

| Field | Description | Default |
|-------|-------------|---------|
| **Use MTO+MTS rules** | Enable MTS+MTO route for this warehouse | False |
| **MTS use actual available instead virtual** | When enabled, uses actual available quantity instead of forecasted | True |

### Setting Location

The parameter **"MTS use actual available instead virtual"** is located:
- Menu: Inventory > Configuration > Warehouses
- Select warehouse (e.g., "VLA")
- Field appears after "Use MTO+MTS rules" checkbox

## Quantity Calculation Methods

### Virtual Available (Forecasted)

Formula: `virtual_available = on_hand + incoming - outgoing`

- **on_hand**: Physical quantity in stock
- **incoming**: Expected receipts (PO, MO outputs)
- **outgoing**: Expected deliveries (SO, MO component consumption)

**Use case**: When you want the system to consider future supply/demand.

### Actual Available (Free Quantity)

Formula: `free_qty = on_hand - reserved`

- **on_hand**: Physical quantity in stock
- **reserved**: Quantity already reserved for existing operations

**Use case**: When you want to use only physically available stock that isn't committed.

## How MTS+MTO Split Works

When a procurement is triggered (e.g., MO component request):

1. System calculates available quantity based on the parameter:
   - If `mts_use_actual_available = True`: uses `free_qty`
   - If `mts_use_actual_available = False`: uses `virtual_available`

2. Split decision:
   - **Available >= Requested**: 100% MTS (reserve from stock)
   - **Available <= 0**: 100% MTO (create procurement for full quantity)
   - **0 < Available < Requested**: Split - MTS for available, MTO for remainder

## Example Scenario

Product: 04DC791
- On hand: 564 units
- Reserved: 554 units
- Free qty: 10 units
- Virtual available: -8 units (due to future demand)

Manufacturing Order requests: 15 units

### With `mts_use_actual_available = True` (default)
- Available = 10 units (free_qty)
- MTS: 10 units (reserved from stock)
- MTO: 5 units (procurement created)

### With `mts_use_actual_available = False`
- Available = -8 units (virtual_available)
- MTS: 0 units
- MTO: 15 units (full procurement)

## Technical Details

### Models Extended

- `stock.warehouse`: Added `mts_use_actual_available` field
- `stock.rule`: Overridden `get_mto_qty_to_order()` method

### Method: `get_mto_qty_to_order()`

Determines how much quantity should be procured via MTO.

```python
def get_mto_qty_to_order(self, product, product_qty, product_uom, values):
    # Get warehouse parameter
    warehouse = self.mts_rule_id.location_src_id.warehouse_id
    use_actual = warehouse.mts_use_actual_available if warehouse else False

    # Get available quantity
    if use_actual:
        available = product_location.free_qty
    else:
        available = product_location.virtual_available

    # Calculate MTO quantity
    if available >= product_qty:
        return 0.0  # 100% MTS
    elif available > 0:
        return product_qty - available  # Partial MTO
    else:
        return product_qty  # 100% MTO
```

### Stock Rules Involved

| Rule | Action | Purpose |
|------|--------|---------|
| MTS+MTO MRP (75) | split_procurement | Decides MTS vs MTO split for MRP |
| MTS+MTO (74) | split_procurement | Decides MTS vs MTO split for sales |
| MTO rules (115-117) | pull | Execute MTO procurement |

## Dependencies

- `stock`: Odoo stock management
- `mrp`: Manufacturing module
- `stock_mts_mto_rule`: OCA MTS+MTO base module

## Version History

| Version | Changes |
|---------|---------|
| 16.0.2.2.0 | Added `mts_use_actual_available` parameter |
| 16.0.2.1.1 | Initial MRP extension for MTS+MTO |
