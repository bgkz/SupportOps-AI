class TicketCreationError(Exception):
    pass


class TicketRetrievalError(Exception):
    pass


class DuplicateIdempotencyKeyError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass
