from django.utils.translation import pgettext_lazy


class VoucherScope:
    RETAIL = "retail"
    CORPORATE = "corporate"

    CHOICES = [
        (RETAIL, pgettext_lazy("Voucher: discount scope", "Retail")),
        (CORPORATE, pgettext_lazy("Voucher: discount scope", "Corporate")),
    ]
