"""Compare Hugo builds of nijho.lt before and after a theme change."""


class ParityError(ValueError):
    """A problem with the input, such as a broken file or an empty build; the message names it."""
