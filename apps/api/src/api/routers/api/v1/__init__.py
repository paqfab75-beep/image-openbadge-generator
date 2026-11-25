"""The versioned API: the badge generator's routes, served anonymously behind the gateway.

``dependencies`` is the empty declaration on purpose: the gateway already signs every caller in,
and this surface holds no caller-specific data. A subtree without the declaration is refused.
"""

from fastapi import params

segment = "v1"

dependencies: tuple[params.Depends, ...] = ()
