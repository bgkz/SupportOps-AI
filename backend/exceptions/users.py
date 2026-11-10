class UserCreationError(Exception):
    pass


class EmailAlreadyExistError(Exception):
    pass


class EmailNotVerifiedError(Exception):
    pass


class UserRetrievalError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserUpdateError(Exception):
    pass
