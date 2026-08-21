import { patch } from "@web/core/utils/patch";
import { ComboPage } from "@pos_self_order/app/pages/combo_page/combo_page";

function isFullIncludedCombo(combo) {
    const comboItems = getAvailableComboItems(combo);
    return (
        combo.qty_free > 0 &&
        combo.qty_max === combo.qty_free &&
        comboItems.length === combo.qty_free
    );
}

function getAvailableComboItems(combo) {
    return combo.combo_item_ids.filter((item) => item.product_id?.self_order_available);
}

patch(ComboPage.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.state) {
            this.autoSelectFullIncludedChoices();
        }
    },

    canSelectAllComboItems(combo) {
        return isFullIncludedCombo(combo) && getAvailableComboItems(combo).every(
            (item) => !this.hasAttribute(item.product_id)
        );
    },

    autoSelectFullIncludedChoices() {
        for (const [choiceIndex, choice] of this.comboChoices.entries()) {
            const choiceState = (this.state.choices[choiceIndex] ??= {});
            if (this.getSelectedItems(choiceState).length || !this.canSelectAllComboItems(choice)) {
                continue;
            }
            choiceState.selectedItems = {};
            choiceState.selectedItemsOrder = [];
            for (const comboItem of getAvailableComboItems(choice)) {
                choiceState.selectedItems[comboItem.id] = { item: comboItem, qty: 1 };
                choiceState.selectedItemsOrder.push(comboItem.id);
            }
        }
    },
});