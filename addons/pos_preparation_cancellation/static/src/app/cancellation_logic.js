export function normalizeCancellationReason(reason) {
    return String(reason || "");
}

export function canCancelOrderline(orderline) {
    return Boolean(
        orderline &&
            !orderline.combo_parent_id &&
            !orderline.order_id?.isRefund &&
            !orderline.refunded_orderline_id &&
            orderline.getQuantity() > 0
    );
}

export function applyOrderlineCancellation(orderline, remainingQuantity, reason) {
    const affectedLines = orderline.combo_line_ids?.length
        ? orderline.getAllLinesInCombo()
        : [orderline];
    const previousNotes = affectedLines.map((line) => line.getCustomerNote());
    for (const line of affectedLines) {
        line.setCustomerNote(reason);
    }

    let result;
    try {
        result = orderline.setQuantity(
            remainingQuantity,
            Boolean(orderline.combo_line_ids?.length)
        );
    } catch (error) {
        affectedLines.forEach((line, index) => line.setCustomerNote(previousNotes[index]));
        throw error;
    }
    if (result !== true) {
        affectedLines.forEach((line, index) => line.setCustomerNote(previousNotes[index]));
        return result;
    }
    return true;
}