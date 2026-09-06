import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    get idleTimeout() {
        return super.idleTimeout.map((step) =>
            step.timeout === 180000 ? { ...step, timeout: 1800000 } : step
        );
    },
});