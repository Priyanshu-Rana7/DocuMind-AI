from decimal import Decimal
import math
from typing import Any, List


def validate_extracted_invoice(data: Any) -> List[str]:
    """Return non-blocking warnings for arithmetic inconsistencies."""
    tolerance = Decimal("0.02")
    warnings: List[str] = []
    items = data.invoice_items
    amounts = [
        ("subtotal", data.subtotal),
        ("tax", data.tax),
        ("discount", data.discount),
        ("total", data.total),
    ]

    for name, value in amounts:
        if not math.isfinite(value) or value < 0:
            warnings.append(f"{name.capitalize()} must be a finite, non-negative amount.")

    if any(not math.isfinite(value) or value < 0 for _, value in amounts):
        return warnings

    for index, item in enumerate(items, start=1):
        if (
            not math.isfinite(item.quantity)
            or not math.isfinite(item.unit_price)
            or not math.isfinite(item.total)
            or item.quantity < 0
            or item.unit_price < 0
            or item.total < 0
        ):
            warnings.append(f"Line item {index} contains an invalid amount.")
            continue
        expected_total = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
        actual_total = Decimal(str(item.total))
        if abs(expected_total - actual_total) > tolerance:
            warnings.append(
                f"Line item {index} total does not match quantity × unit price."
            )

    if items and data.subtotal:
        item_total = sum((Decimal(str(item.total)) for item in items), Decimal("0"))
        if abs(item_total - Decimal(str(data.subtotal))) > tolerance:
            warnings.append("Line item totals do not match the extracted subtotal.")

    expected_grand_total = (
        Decimal(str(data.subtotal))
        - Decimal(str(data.discount))
        + Decimal(str(data.tax))
    )
    if abs(expected_grand_total - Decimal(str(data.total))) > tolerance:
        warnings.append(
            "Subtotal, discount, and tax do not reconcile with the extracted total."
        )

    return warnings
