import { patch } from "@web/core/utils/patch";
import { ComboConfiguratorPopup } from "@point_of_sale/app/components/popups/combo_configurator_popup/combo_configurator_popup";

function canSelectAllComboItems(combo) {
    const comboItems = combo.combo_item_ids.filter((item) => item.product_id);
    return (
        combo.qty_free > 0 &&
        combo.qty_max === combo.qty_free &&
        comboItems.length === combo.qty_free &&
        comboItems.every((item) => !item.product_id.isConfigurable())
    );
}

patch(ComboConfiguratorPopup.prototype, {
    autoSelectSingleChoices() {
        super.autoSelectSingleChoices(...arguments);
        this.autoSelectFullIncludedChoices();
    },

    autoSelectFullIncludedChoices() {
        for (const combo of this.props.productTemplate.combo_ids) {
            const comboQty = this.state.qty[combo.id];
            if (!comboQty || this.totalQuantityForCombo(combo.id) || !canSelectAllComboItems(combo)) {
                continue;
            }
            for (const comboItem of combo.combo_item_ids) {
                comboQty[comboItem.id] = 1;
            }
        }
    },
});