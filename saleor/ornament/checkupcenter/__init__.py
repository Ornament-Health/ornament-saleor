from django.utils.translation import pgettext_lazy


class CheckUpStateStatus:
    """Represents possible statuses of a checkup state.

    The following statuses are possible:
    - FULL - all biomarkers and invivo are filled.
    - PARTIAL - some of biomarkers and invivo are filled.
    - MOST_FILLED - state between 1 year and partial state but with more filled data.
    """

    PARTIAL = "partial"
    FULL = "full"
    MOST_FILLED = "most-filled"

    CHOICES = [
        (PARTIAL, pgettext_lazy("checkup status", "Partial")),
        (FULL, pgettext_lazy("checkup status", "Full")),
        (MOST_FILLED, pgettext_lazy("checkup status", "Most filled")),
    ]


class CheckUpStateApprovement:
    """Represents possible values of a checkup state approvement.

    The following statuses are possible:
    - APPROVED - checkup approved to be processed next time,
    - NOT_APPROVED - checkup not approved to be processed until 1 yaer after last full state,
    - NEED_TO_ASK - it is required to ask user about checkup processing behaviour.
    """

    NEED_TO_ASK = "need-to-ask"
    APPROVED = "approved"
    NOT_APPROVED = "not-approved"

    CHOICES = [
        (NEED_TO_ASK, pgettext_lazy("payment approvement", "Need to ask")),
        (APPROVED, pgettext_lazy("payment approvement", "Approved")),
        (NOT_APPROVED, pgettext_lazy("payment approvement", "Not approved")),
    ]
