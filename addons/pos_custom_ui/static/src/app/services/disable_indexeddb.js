import { patch } from "@web/core/utils/patch";
import { SelfOrder } from "@pos_self_order/app/services/self_order_service";
import { PosData } from "@point_of_sale/app/services/data_service";

function isIndexedDBDisabled() {
    return new URL(window.location.href).searchParams.get("disable_indexeddb") === "1";
}

patch(PosData.prototype, {
    initIndexedDB() {
        if (isIndexedDBDisabled()) {
            return true;
        }
        return super.initIndexedDB(...arguments);
    },

    initListeners() {
        if (isIndexedDBDisabled()) {
            return true;
        }
        return super.initListeners(...arguments);
    },

    synchronizeLocalDataInIndexedDB() {
        if (isIndexedDBDisabled()) {
            return true;
        }
        return super.synchronizeLocalDataInIndexedDB(...arguments);
    },

    synchronizeServerDataInIndexedDB() {
        if (isIndexedDBDisabled()) {
            return true;
        }
        return super.synchronizeServerDataInIndexedDB(...arguments);
    },

    async getCachedServerDataFromIndexedDB() {
        if (isIndexedDBDisabled()) {
            return {};
        }
        return await super.getCachedServerDataFromIndexedDB(...arguments);
    },

    async getLocalDataFromIndexedDB() {
        if (isIndexedDBDisabled()) {
            return {};
        }
        return await super.getLocalDataFromIndexedDB(...arguments);
    },

    async deleteRecordsInIndexedDB() {
        if (isIndexedDBDisabled()) {
            return true;
        }
        return await super.deleteRecordsInIndexedDB(...arguments);
    },
});

patch(SelfOrder.prototype, {
    shouldUpdateLastOrderChange() {
        if (isIndexedDBDisabled()) {
            return false;
        }
        return super.shouldUpdateLastOrderChange(...arguments);
    },

    async getUserDataFromServer() {
        if (isIndexedDBDisabled()) {
            return;
        }
        return await super.getUserDataFromServer(...arguments);
    },
});