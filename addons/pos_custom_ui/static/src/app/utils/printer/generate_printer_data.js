import { patch } from "@web/core/utils/patch";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
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
        const orderLineIndexes = new Map(
            this.order.lines.map((line, index) => [line.uuid, index])
        );
        const sortChangesByOrder = (changeList) =>
            changeList
                .map((change, index) => {
                    const orderLine = this.order.lines.find(
                        (line) => line.uuid === change.line_uuid
                    );
                    const groupUuid = orderLine?.combo_parent_id?.uuid || orderLine?.uuid;
                    return {
                        change,
                        index,
                        orderIndex: orderLineIndexes.get(groupUuid) ?? Infinity,
                    };
                })
                .sort((a, b) => a.orderIndex - b.orderIndex || a.index - b.index)
                .map(({ change }) => change);

        for (const changeType of ["addedQuantity", "removedQuantity", "noteUpdate"]) {
            changes[changeType] = sortChangesByOrder(changes[changeType] || []);
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

patch(PosOrder.prototype, {
    dataMaker(prepOrPosLine, quantity) {
        const result = super.dataMaker(...arguments);
        const line = prepOrPosLine.pos_order_line_id || prepOrPosLine;
        result.data.line_uuid = line.uuid;
        return result;
    },
});