import { Component, props, proxy, t } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { parseFloat as parseLocalizedFloat } from "@web/views/fields/parsers";
import { DECIMAL, Numpad } from "@point_of_sale/app/components/numpad/numpad";
import { normalizeCancellationReason } from "./cancellation_logic";

const REASONS = [
    "已沽清",
    "质量问题",
    "操作错误",
    "顾客原因",
    "出品超时",
    "换菜",
    "出品部原因",
    "测试",
];

export class PreparationCancellationDialog extends Component {
    static template = "pos_preparation_cancellation.PreparationCancellationDialog";
    static components = { Dialog, Numpad };
    props = props({
        orderline: t.any(),
        getPayload: t.function(),
        close: t.function(),
    });

    setup() {
        this.reasons = REASONS;
        this.state = proxy({
            quantity: this.props.orderline.quantityStr.qtyStr,
            selectedReason: "",
            customReason: "",
            replaceQuantity: true,
        });
    }

    get numpadButtons() {
        return [
            { value: "7" },
            { value: "8" },
            { value: "9" },
            { value: "4" },
            { value: "5" },
            { value: "6" },
            { value: "1" },
            { value: "2" },
            { value: "3" },
            { value: "0" },
            { value: "00" },
            DECIMAL,
        ];
    }

    get reason() {
        return this.state.selectedReason === "custom"
            ? this.state.customReason.trim()
            : normalizeCancellationReason(this.state.selectedReason);
    }

    get cancellationQuantity() {
        const quantity = parseLocalizedFloat(this.state.quantity || "");
        return Number.isFinite(quantity) ? quantity : null;
    }

    get remainingQuantity() {
        const cancellationQuantity = this.cancellationQuantity;
        const currentQuantity = this.props.orderline.getQuantity();
        if (cancellationQuantity === null || cancellationQuantity <= 0 || cancellationQuantity > currentQuantity) {
            return null;
        }
        const rounder = this.props.orderline.models["decimal.precision"].find(
            (precision) => precision.name === "Product Unit"
        );
        const remainingQuantity = rounder.round(currentQuantity - cancellationQuantity);
        return remainingQuantity >= 0 && remainingQuantity < currentQuantity
            ? remainingQuantity
            : null;
    }

    get isValid() {
        return Boolean(this.reason) && this.remainingQuantity !== null;
    }

    selectReason(reason) {
        this.state.selectedReason = reason;
    }

    onCustomReasonInput(event) {
        this.state.customReason = event.target.value;
        this.state.selectedReason = "custom";
    }

    onQuantityInput(event) {
        this.state.quantity = event.target.value;
        this.state.replaceQuantity = false;
    }

    onNumpadClick(value) {
        if (this.state.replaceQuantity) {
            this.state.quantity = "";
            this.state.replaceQuantity = false;
        }
        if (value === DECIMAL.value) {
            if (!this.state.quantity.includes(DECIMAL.value)) {
                this.state.quantity = `${this.state.quantity || "0"}${DECIMAL.value}`;
            }
            return;
        }
        this.state.quantity += value;
    }

    backspace() {
        this.state.replaceQuantity = false;
        this.state.quantity = this.state.quantity.slice(0, -1);
    }

    clear() {
        this.state.quantity = "";
        this.state.replaceQuantity = false;
    }

    confirm() {
        if (!this.isValid) {
            return;
        }
        this.props.getPayload({
            remainingQuantity: this.remainingQuantity,
            reason: this.reason,
        });
        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}