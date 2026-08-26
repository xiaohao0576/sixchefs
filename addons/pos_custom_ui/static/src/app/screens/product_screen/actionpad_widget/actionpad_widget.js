import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";

patch(ActionpadWidget.prototype, {
    get isSelfOrderTableOrder() {
        const order = this.currentOrder;
        return !!order?.self_ordering_table_id && !order?.table_id;
    },

    get transferActionName() {
        return "Transfer";
    },

    clickTransferOrder() {
        this.pos.startTransferOrder();
    },

    get swapButton() {
        if (this.isSelfOrderTableOrder) {
            return false;
        }
        return super.swapButton;
    },
});