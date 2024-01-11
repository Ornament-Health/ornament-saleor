import graphene


class CheckUpSexEnum(graphene.Enum):
    M = "M"
    F = "F"


class CheckUpStateApprovement(graphene.Enum):
    NEED_TO_ASK = "need-to-ask"
    APPROVED = "approved"
    NOT_APPROVED = "not-approved"
