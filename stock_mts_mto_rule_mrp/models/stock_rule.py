from odoo import models
from odoo.tools import float_compare


class StockRule(models.Model):
    _inherit = "stock.rule"

    def get_mto_qty_to_order(self, product, product_qty, product_uom, values):
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        src_location_id = self.mts_rule_id.location_src_id.id

        # Get the warehouse to check the parameter
        warehouse = self.mts_rule_id.location_src_id.warehouse_id
        use_actual = warehouse.mts_use_actual_available if warehouse else False

        product_location = product.with_context(location=src_location_id)

        if use_actual:
            # Use free_qty (on_hand - reserved) for actual available
            available = product_location.free_qty
        else:
            # Use virtual_available (on_hand + incoming - outgoing) for forecasted
            available = product_location.virtual_available

        qty_available = product.uom_id._compute_quantity(available, product_uom)

        if float_compare(qty_available, 0.0, precision_digits=precision) > 0:
            if (
                float_compare(qty_available, product_qty, precision_digits=precision)
                >= 0
            ):
                return 0.0
            else:
                return product_qty - qty_available
        return product_qty
