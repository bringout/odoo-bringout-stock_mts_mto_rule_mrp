
from odoo import models, fields, _


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    mts_mto_rule_mrp_id = fields.Many2one("stock.rule", "MTO+MTS MRP rule", check_company=True)
    mts_use_actual_available = fields.Boolean(
        "MTS use actual available instead virtual",
        default=True,
        help="When enabled, MTS+MTO rules will use actual available quantity "
             "(on_hand - reserved) instead of virtual/forecasted quantity "
             "(on_hand + incoming - outgoing) to decide MTS vs MTO split."
    )

    def _update_name_and_code(self, new_name=False, new_code=False):
        res = super(StockWarehouse, self)._update_name_and_code(new_name, new_code)
        if not new_name:
            return res
        for warehouse in self.filtered("mts_mto_rule_mrp_id"):
            warehouse.mts_mto_rule_mrp_id.write(
                {
                    "name": warehouse.mts_mto_rule_id.name.replace(
                        warehouse.name, new_name, 1
                    ),
                }
            )
        return res
    
    def _get_global_route_rules_values(self):

        res = super(StockWarehouse, self)._get_global_route_rules_values()

        # Check if pbm_route_id has rules before accessing
        if not self.pbm_route_id or not self.pbm_route_id.rule_ids:
            return res

        pbm_rule = self.pbm_route_id.rule_ids[0]

        res.update(
            {
                "mts_mto_rule_mrp_id": {
                    "depends": ["delivery_steps", "mto_mts_management"],
                    "create_values": {
                        "action": "pull",
                        "procure_method": "make_to_order",
                        "company_id": self.company_id.id,
                        "auto": "manual",
                        "propagate_cancel": True,
                        "route_id": self._find_global_route(
                            "stock_mts_mto_rule.route_mto_mts",
                            _("Make To Order + Make To Stock"),
                        ).id,
                    },
                    "update_values": {
                        "active": self.mto_mts_management,
                        "name": self._format_rulename(
                            pbm_rule.location_src_id,
                            pbm_rule.location_dest_id,
                            "MTS+MTO MRP"
                        ),
                        "location_dest_id": pbm_rule.location_dest_id.id,
                        "location_src_id": pbm_rule.location_src_id.id,
                        "picking_type_id": pbm_rule.picking_type_id.id,
                    },
                },
            }
        )
        return res
    
    def _create_or_update_global_routes_rules(self):

        res = super(StockWarehouse, self)._create_or_update_global_routes_rules()
        if (
            self.mto_mts_management and self.mts_mto_rule_mrp_id
            and self.mts_mto_rule_mrp_id.action != "split_procurement"
        ):
            # Cannot create or update with the 'split_procurement' action due
            # to constraint and the fact that the constrained rule_ids may
            # not exist during the initial (or really any) calls of
            # _get_global_route_rules_values
            rule_mrp = self.env["stock.rule"].search(
                [
                    ("mto_rule_id", "=", self.pbm_mto_pull_id.id),
                ],
                limit=1,
            )
            if not rule_mrp and self.pbm_route_id and self.pbm_route_id.rule_ids:
                pbm_rule = self.pbm_route_id.rule_ids[0]
                self.mts_mto_rule_mrp_id.write(
                        {
                            "action": "split_procurement",
                            "mts_rule_id": pbm_rule.id,
                            "mto_rule_id": self.pbm_mto_pull_id.id,
                            "picking_type_id": pbm_rule.picking_type_id,
                            "location_src_id": self.pbm_mto_pull_id.location_src_id.id,
                            "location_dest_id": self.pbm_mto_pull_id.location_dest_id.id,
                        }
                    )

        return res
