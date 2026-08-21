import { patch } from "@web/core/utils/patch";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";

patch(GeneratePrinterData.prototype, {
    get commonExtraData() {
        const extraData = super.commonExtraData;
        const table = this.order.table_id;
        extraData.table_alias = table?.table_alias || table?.table_number || false;
        return extraData;
    },
});