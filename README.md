# MatrixCore

MatrixCore is a brand new, modernised Matrix python SDK, built from
the ground up, primarily to serve the needs of [nio-bot](https://pypi.org/p/nio-bot).
Built with [httpx](https://pypi.org/p/httpx) and [pydantic](https://pypi.org/p/pydantic),
MatrixCore allows you to build rich client applications without having to worry about all
of the dirty complicated processing

> [!WARNING]
> MatrixCore is in an early stage, not even alpha, and should not yet be used.
> There is an absence of documentation, aside from any [examples](/examples),
> and a lot of core functionality is either unimplemented or implemented in a
> user-unfriendly way. Please wait for a tagged alpha before you take interest.
> Furthermore, rapid developments are happening daily, so there is
> currently **no stable API**.

> [!IMPORTANT]
> MatrixCore does not currently support E2EE however plans to implement it before
> the first alpha.

## Contact

Want to discuss matrixcore? suggest things? Please contact me in the NioBot Matrix room:
[#niobot:nexy7574.co.uk](https://matrix.to/#/#niobot:nexy7574.co.uk)

## Early adoption guide

In the current absence of documentation, you should refer to [src/matrixcore/core.py](/src/matrixcore/core.py),
inspecting signatures where needed. The client itself, `MatrixCore`, is what you will need to
initialise and interact with.
The client implements all the high-level functionality, such as client-side storage of the sync batches,
event dispatching, and room management.

However, as the client is not yet fully implemented, you may need to interact with the http backend directly via
`MatrixCore.http`. This is an almost stateless client whose sole purpose is to interact with the Matrix API
in an agnostic way (i.e. it does not know about the client's state). A lot more things are implemented here
that do not yet have a higher-level interface, however, they may not be as easy to use as the client.

See the examples/ directory for some examples. [feed_test.py](/examples/feed_test.py)
is a simple client that takes a homeserver and access token, syncs indefinitely, prints all messages sent after the
process started, and listens for messages matching `!matrixcore test`, `!matrixcore ping`, and `!matrixcore time`,
and responds appropriately to them.

## Contributing

Code contributions are not currently accepted at this time as the library is still in a very early stage, and I would
like to finish laying the groundwork first. However, feel free to discuss any issues or enhancements in the
[#niobot:nexy7574.co.uk](https://matrix.to/#/#niobot:nexy7574.co.uk) room.
