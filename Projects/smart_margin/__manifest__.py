{
    'name': 'Smart Margin',
    'version': '1.0',
    'summary': 'Real-Time Margin Dashboard with Cost Breakdown',
    'description': 'Compute and display real-time margin for sale orders with cost breakdown.',
    'author': 'Malik Saffour',
    'depends': [
        'base',
        'sale',
        'stock',
        'account',
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/res_config_settings_views.xml",
    ],
    'assets': {
       
        "web.assets_backend": [
            "smart_margin/static/src/margin_info/*.*",
        ]
    },
    'installable': True,
    'application': False,
}