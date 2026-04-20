/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { MarginInfo } from "../margin_info/margin_info";
import { useService } from "@web/core/utils/hooks";
import { Pager } from "@web/core/pager/pager";

export class MarginList extends Component {
    static template = "smart_margin_dashboard.marginList";
    static components = { Pager };

    setup() {
        this.state = useState({
            margins: [],
            offset: 0,
            limit: 10,
            total: 0,
            selectedColors: [],
        });
        this.actionService = useService("action");
        this.orm = useService("orm"); 
        this.dialog = useService("dialog");

        onWillStart(async () => {
            await this.loadMargins();
        });
    }

    async loadMargins() {
        const domain = [];
        
        if (this.state.selectedColors.length > 0) {
            domain.push(['margin_color', 'in', this.state.selectedColors]);
        }

        if (this.state.total === 0) {
            const countResult = await this.orm.call('sale.order.margin', 'search_count', [domain]);
            this.state.total = countResult;
        }

        const result = await this.orm.searchRead(
            'sale.order.margin',
            domain,  
            [],      
            { offset: this.state.offset, limit: this.state.limit }
        );

        this.state.margins = result;
    }

    onPageUpdate({ offset }) {
        this.state.offset = offset;
        this.loadMargins();
    }

    async openSaleOrder(margin) {
        if (!margin || !margin.order_id) return;

        const url = `/web#id=${margin.order_id[0]}&model=sale.order&view_type=form&menu_id=340&action=537`;
        window.open(url, '_blank'); 
    }

    showMarginInfo(margin) {
        this.dialog.add(MarginInfo, {
            margin: margin,
        });
    }
    toggleColor(color) {
        const index = this.state.selectedColors.indexOf(color);
        if (index === -1) {
            this.state.selectedColors.push(color);
        } else {
            this.state.selectedColors.splice(index, 1);
        }
        this.state.offset = 0; 
        this.loadMargins();
    }
    
    downloadXlsx() {
        const payload = { selectedColors: this.state.selectedColors };
        fetch('/smart_margin_dashboard/download_xlsx', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(payload),
        })
        .then(res => res.blob())
        .then(blob => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'margin_report.xlsx';
            link.click();
        })
        .catch(err => {
            console.error("Download failed:", err);
            alert("Download failed.");
        });
    }
}

registry.category("actions").add("smart_margin_dashboard.action_margin_list", MarginList);