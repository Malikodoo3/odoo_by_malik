/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

export class MarginInfo extends Component {
    static template = "smart_margin_dashboard.MarginInfo";
    static components = { Dialog };
    static props = {
        margin: Object,  
        close: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            totals: {
                total_revenue: 0,
                total_cogs: 0,
                total_overhead: 0,
                tax_on_company: 0,
                discount_on_company: 0,
                net_margin: 0,
                margin_percentage: 0,
            },
            lines: [],
        });

        onWillStart(async () => {
            await this.computeMargin();
        });
    }

    async computeMargin() {
        const margin = this.props.margin;
        if (!margin || !margin.order_id) return;

        const orderLines = await this.orm.call(
            'sale.order.line',
            'search_read',
            [[['order_id', '=', margin.order_id[0]]], 
            ['product_id','price_unit','price_subtotal','price_total','product_uom_qty','discount_amount']]
        );

        const params = await this.orm.call('ir.config_parameter', 'get_param', ['smart_margin.overhead_type', 'percent']);
        const overheadType = params || 'percent';
        const overheadValue = parseFloat(await this.orm.call('ir.config_parameter', 'get_param', ['smart_margin.overhead_value', '0'])) || 0;
        const overheadApplyOn = await this.orm.call('ir.config_parameter', 'get_param', ['smart_margin.overhead_apply_on', 'unit']) || 'unit';

        let totalRevenue = 0;
        let totalCogs = 0;
        let totalOverhead = 0;
        let totalTax = 0;
        let totalDiscount = 0;

        let lines = [];

        for (const line of orderLines) {
            const landedCost = line.product_id[0] ? await this.orm.call('product.product', 'read', [[line.product_id[0]], ['standard_price']]).then(res => res[0].standard_price || 0) : 0;
            const lineCogs = landedCost * line.product_uom_qty;

            let lineOverhead = 0;
            if (overheadApplyOn === 'unit') {
                lineOverhead = overheadType === 'fixed' ? overheadValue * line.product_uom_qty : lineCogs * overheadValue / 100;
            } else if (overheadApplyOn === 'product') {
                lineOverhead = overheadType === 'fixed' ? overheadValue : lineCogs * overheadValue / 100;
            }

            const tax = Math.max(line.price_total - line.price_subtotal, 0);
            const discount = line.discount_amount || 0;
            const lineMargin = line.price_total - (lineCogs + lineOverhead + tax + discount);

            totalRevenue += line.price_total;
            totalCogs += lineCogs + lineOverhead + tax + discount;
            totalOverhead += lineOverhead;
            totalTax += tax;
            totalDiscount += discount;

            lines.push({
                product_name: line.product_id ? line.product_id[1] : '',
                qty: line.product_uom_qty,
                unit_price: line.price_unit,
                landed_cost: landedCost,
                overhead: lineOverhead,
                tax_on_company: tax,
                discount_on_company: discount,
                line_margin: lineMargin,
            });
        }

        const netMargin = totalRevenue - totalCogs;
        const marginPercentage = totalRevenue ? (netMargin / totalRevenue * 100) : 0;

        this.state.totals = {
            total_revenue: totalRevenue,
            total_cogs: totalCogs,
            total_overhead: totalOverhead,
            tax_on_company: totalTax,
            discount_on_company: totalDiscount,
            net_margin: netMargin,
            margin_percentage: marginPercentage,
        };

        this.state.lines = lines;
    }
}