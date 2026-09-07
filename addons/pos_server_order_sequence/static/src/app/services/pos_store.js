import { PosStore } from "@point_of_sale/app/services/pos_store";
import DeviceIdentifierSequence from "@point_of_sale/app/utils/devices_identifier_sequence";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    setNextOrderRefs(order) {
        order.pos_reference = "";
        order.tracking_number = "";
    },
});

patch(DeviceIdentifierSequence.prototype, {
    saveUnusedNumber() {},
});
