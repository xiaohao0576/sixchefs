import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { PreparationCancellationDialog } from "./cancellation_dialog";
import { applyOrderlineCancellation, canCancelOrderline } from "./cancellation_logic";

export class PreparationCancellationButton extends Component {
    static template = "pos_preparation_cancellation.PreparationCancellationButton";

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }

    get selectedOrderline() {
        return this.pos.getOrder()?.getSelectedOrderline();
    }

    get isVisible() {
        return Boolean(this.selectedOrderline && !this.selectedOrderline.combo_parent_id);
    }

    get isDisabled() {
        return !canCancelOrderline(this.selectedOrderline);
    }

    async onClick() {
        const orderline = this.selectedOrderline;
        if (!canCancelOrderline(orderline)) {
            return;
        }

        const payload = await makeAwaitable(this.dialog, PreparationCancellationDialog, {
            orderline,
        });
        if (!payload) {
            return;
        }

        const result = applyOrderlineCancellation(
            orderline,
            payload.remainingQuantity,
            payload.reason
        );
        if (result !== true) {
            this.dialog.add(AlertDialog, result || {
                title: _t("Cancellation failed"),
                body: _t("The selected item could not be updated."),
            });
        }
    }
}

patch(ControlButtons, {
    components: {
        ...ControlButtons.components,
        PreparationCancellationButton,
    },
});