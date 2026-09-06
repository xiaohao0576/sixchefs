import { patch } from "@web/core/utils/patch";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";
import { getStrNotes } from "@point_of_sale/app/models/utils/order_change";

const PRODUCT_NAME_FIELDS = ["name_en", "name_km", "name_cn"];

function getProductLanguageNames(product) {
    const languageNames = {};
    for (const fieldName of PRODUCT_NAME_FIELDS) {
        languageNames[fieldName] = product?.[fieldName] || product?.raw?.[fieldName] || "";
    }
    return languageNames;
}

function addProductLanguageNames(target, product) {
    Object.assign(target, getProductLanguageNames(product));
}

patch(GeneratePrinterData.prototype, {
    generateLineData() {
        const lines = super.generateLineData(...arguments);
        for (const [index, lineData] of lines.entries()) {
            const line = this.order.lines[index];
            const product = line?.product_id;
            addProductLanguageNames(lineData, product);
            addProductLanguageNames(lineData.product_data, product);
            lineData.note = getStrNotes(line?.getNote?.() || false);
        }
        return lines;
    },

    generatePreparationChanges(orderChange, categoryIdsSet) {
        const changes = super.generatePreparationChanges(...arguments);
        for (const changeType of ["addedQuantity", "removedQuantity", "noteUpdate"]) {
            for (const change of changes[changeType] || []) {
                const product = this.models["product.product"].get(change.product_id);
                addProductLanguageNames(change, product);
                change.product_data = {
                    ...(change.product_data || {}),
                    ...getProductLanguageNames(product),
                };
            }
        }
        return changes;
    },
});