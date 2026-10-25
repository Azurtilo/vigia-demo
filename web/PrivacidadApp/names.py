"""How an author is shown once the account may have been erased (spec 014)."""

ERASED_PREFIX = "eliminado-"


def is_erased(user):
    # The prefix alone could be chosen at sign-up; an erased account is also
    # inactive and has no usable password.
    return (
        user.username.startswith(ERASED_PREFIX)
        and not user.is_active
        and not user.has_usable_password()
    )


def author_name(user):
    if is_erased(user):
        return "Cuenta eliminada"
    return user.get_full_name() or user.username
