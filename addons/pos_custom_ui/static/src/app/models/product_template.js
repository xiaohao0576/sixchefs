import { ProductTemplate } from "@point_of_sale/app/models/product_template";
import { normalize } from "@web/core/l10n/utils";
import { patch } from "@web/core/utils/patch";

const LOCALIZED_NAME_FIELDS = ["name_cn", "name_en", "name_km"];

patch(ProductTemplate.prototype, {
    get searchString() {
        const baseSearchString = super.searchString;
        return this.cacheValues("posCustomSearchString", () => {
            const localizedNames = LOCALIZED_NAME_FIELDS.map((field) => this[field] || "")
                .filter(Boolean)
                .join(" ");

            return localizedNames
                ? `${baseSearchString} ${normalize(localizedNames)}`
                : baseSearchString;
        });
    },
});