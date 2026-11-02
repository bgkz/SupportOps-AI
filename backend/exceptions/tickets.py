class TicketApprovalConflictError(Exception):
    pass


class TicketApprovalPermissionError(Exception):
    pass


class TicketCreationError(Exception):
    pass


class TicketRetrievalError(Exception):
    pass


class DuplicateIdempotencyKeyError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


class TicketClassificationError(Exception):
    pass
