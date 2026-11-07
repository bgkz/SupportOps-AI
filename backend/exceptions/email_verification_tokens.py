class EmailVerificationTokenCreationError(Exception):
    pass


class EmailVerificationTokenNotFound(Exception):
    pass


class EmailVerificationTokenExpiredError(Exception):
    pass


class EmailVerificationTokenRetrievalError(Exception):
    pass
