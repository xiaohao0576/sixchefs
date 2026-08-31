import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

const DISCOUNT_PRODUCT_CATEGORY_ID = 5;

const PRICELIST_DISCOUNTS = {
    "标准价格表": 0,
    "75折价格": 25,
    "88折价格": 12,
    "9折价格": 10,
    "95折价格": 5,
};

patch(PosStore.prototype, {
    async selectPricelist(pricelist) {
        await super.selectPricelist(...arguments);

        const discount = PRICELIST_DISCOUNTS[pricelist?.name] ?? 0;
        for (const line of this.getOrder().lines) {
            if (line.price_type !== "original" || line.isPartOfCombo()) {
                continue;
            }

            const categoryId = line.product_id.product_tmpl_id.categ_id?.id;
            line.setDiscount(categoryId === DISCOUNT_PRODUCT_CATEGORY_ID ? discount : 0);
        }
    },
});