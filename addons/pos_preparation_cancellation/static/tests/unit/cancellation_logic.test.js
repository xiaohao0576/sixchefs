import { describe, expect, test } from "@odoo/hoot";
import { getFilledOrder, setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import {
    applyOrderlineCancellation,
    canCancelOrderline,
    normalizeCancellationReason,
} from "@pos_preparation_cancellation/app/cancellation_logic";

definePosModels();

describe("preparation cancellation", () => {
    test("keeps the configured reason unchanged", () => {
        expect(normalizeCancellationReason("质量问题")).toBe("质量问题");
        expect(typeof normalizeCancellationReason("质量问题")).toBe("string");
    });

    test("only allows positive regular or combo parent lines", () => {
        const line = {
            combo_parent_id: false,
            order_id: { isRefund: false },
            refunded_orderline_id: false,
            getQuantity: () => 2,
        };

        expect(canCancelOrderline(line)).toBe(true);
        expect(canCancelOrderline({ ...line, combo_parent_id: {} })).toBe(false);
        expect(canCancelOrderline({ ...line, order_id: { isRefund: true } })).toBe(false);
        expect(canCancelOrderline({ ...line, refunded_orderline_id: {} })).toBe(false);
        expect(canCancelOrderline({ ...line, getQuantity: () => 0 })).toBe(false);
        expect(canCancelOrderline({ ...line, getQuantity: () => -1 })).toBe(false);
    });

    test("keeps a zero-quantity line and overwrites notes for the whole combo", () => {
        const notes = [];
        const child = {
            getCustomerNote: () => "old child note",
            setCustomerNote: (note) => notes.push(["child", note]),
        };
        const parent = {
            combo_line_ids: [child],
            getAllLinesInCombo: () => [parent, child],
            getCustomerNote: () => "old parent note",
            setCustomerNote: (note) => notes.push(["parent", note]),
        };
        parent.setQuantity = (quantity) => {
            expect(quantity).toBe(0);
            expect(notes).toEqual([
                ["parent", "质量问题"],
                ["child", "质量问题"],
            ]);
            return true;
        };

        expect(applyOrderlineCancellation(parent, 0, "质量问题")).toBe(true);
    });

    test("includes the cancellation reason in kitchen removal data", async () => {
        const store = await setupPosEnv();
        const order = await getFilledOrder(store);
        const orderline = order.lines[0];
        const originalQuantity = orderline.getQuantity();
        order.updateLastOrderChange();

        applyOrderlineCancellation(orderline, originalQuantity - 1, "质量问题");

        const removedLine = order
            .getChanges()
            .removedQuantity.find((line) => line.product_id === orderline.product_id.id);
        expect(removedLine.quantity).toBe(-1);
        expect(removedLine.customer_note).toBe("质量问题");
    });
});