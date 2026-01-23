
{
    "name": "Stock MTS+MTO Rule MRP",
    "summary": "Configure MTS+MTO route for manufacturing.",
    "version": "16.0.2.2.0",
    "category": "Warehouse",
    "website": "https://www.bring.out.ba",
    "author": "bring.out doo Sarajevo",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
        "mrp",
        "stock_mts_mto_rule"
    ],
    "data": [
        "views/stock_warehouse_views.xml",
    ],
}
