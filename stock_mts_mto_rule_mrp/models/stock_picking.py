from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_assign(self):
        self._mts_mto_retry_orphaned_moves()
        return super().action_assign()

    def _mts_mto_retry_orphaned_moves(self):
        """Convert orphaned MTO moves from MTS+MTO split back to MTS.

        When MTS+MTO split_procurement runs at MO confirmation time and stock
        is zero, it routes 100% through MTO. If the upstream MTO purchase fails
        or stock is later received manually, the pick move stays 'waiting' with
        procure_method='make_to_order' forever.

        This method detects such orphaned moves and converts them to MTS so
        that 'Check Availability' can reserve from available stock.
        """
        split_rules = self.env["stock.rule"].search([
            ("action", "=", "split_procurement"),
        ])
        mto_rule_ids = split_rules.mapped("mto_rule_id").ids
        if not mto_rule_ids:
            return

        orphaned = self.move_ids.filtered(
            lambda m: (
                m.state == "waiting"
                and m.procure_method == "make_to_order"
                and m.rule_id.id in mto_rule_ids
                and (
                    not m.move_orig_ids
                    or all(o.state in ("done", "cancel") for o in m.move_orig_ids)
                )
            )
        )
        if orphaned:
            orphaned.procure_method = "make_to_stock"
            orphaned._recompute_state()
