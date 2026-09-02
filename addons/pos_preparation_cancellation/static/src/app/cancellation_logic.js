export function normalizeCancellationReason(reason) {
    return String(reason || "");
}

export function isOrderlineSentToKitchen(orderline) {
    if (!orderline) {
        return false;
    }

    if (
        Array.isArray(orderline.prep_line_ids) &&
        orderline.prep_line_ids.length > 0
    ) {
        return true;
    }

    return typeof orderline.prepQty === "number" && orderline.prepQty > 0;
}

export function getPreparedQuantity(orderline) {
    if (typeof orderline?.prepQty === "number") {
        return orderline.prepQty;
    }
    return (
        orderline?.prep_line_ids?.reduce(
            (quantity, prepLine) => quantity + prepLine.quantity - prepLine.cancelled,
            0
        ) || 0
    );
}

export function hasUnsentQuantity(orderline) {
    return Boolean(orderline && orderline.getQuantity() > getPreparedQuantity(orderline));
}

export function canEditOrderline(orderline) {
    return !isOrderlineSentToKitchen(orderline);
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