/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class MarginInfo extends Component {
    static template = "smart_margin.MarginInfo";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            totals: {
                total_revenue: 0,
                total_cogs: 0,
                overhead_amount: 0,
                net_margin: 0,
                margin_percentage: 0,
            },
            lines: [],
        });

        this.orderId = this.props.action?.params?.order_id;
        if (!this.orderId){
            this.orderId = this.props.action?.params?.active_id;
        }

        console.log("OrderId:", this.orderId);

        onWillStart(async () => {
            await this.loadMarginData();
        });
    }

    async loadMarginData() {
        if (!this.orderId) return;

        const margin = await this.orm.searchRead(
            'sale.order.margin',
            [["order_id", "=", this.orderId]],
            ["total_revenue","total_cogs","overhead_amount","net_margin","margin_percentage","currency_id","margin_color"]
        );

        if (!margin.length) return;

        const m = margin[0];

        this.state.totals = {
            total_revenue: m.total_revenue,
            total_cogs: m.total_cogs,
            overhead_amount: m.overhead_amount,
            net_margin: m.net_margin,
            margin_percentage: m.margin_percentage,
            currency_id: m.currency_id[0],
            margin_color:m.margin_color
        };

        const lines = await this.orm.searchRead(
            'sale.order.margin.line',
            [["margin_id", "=", m.id]],
            ["product_id","qty","unit_price","revenue","landed_cost","overhead_cost","total_cost","margin"]
        );

        this.state.lines = lines.map(line => ({
            product_name: line.product_id ? line.product_id[1] : "",
            qty: line.qty,
            unit_price: line.unit_price,
            revenue: line.revenue,
            landed_cost: line.landed_cost,
            overhead_cost: line.overhead_cost,
            total_cost: line.total_cost,
            margin: line.margin,
        }));
    }
    goBack() {
        window.history.back();
    }
}

registry.category("actions").add("smart_margin.action_margin_info", MarginInfo);