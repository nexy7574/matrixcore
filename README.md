# MatrixCore

MatrixCore is a client library specifically crafted to
work with nio-bot and is eventually intended to replace
the matrix-nio library, at least in large part.
MatrixCore is built using httpx and pydantic, instead of
aiohttp and dataclasses, which allows for a more
powerfully typed and validated experience.

MatrixCore may eventually be split out into its own separate
package once it reaches maturity, but until then, it will be
an essential part of NioBot v2 going forward.
