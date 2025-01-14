# MatrixCore

MatrixCore is a brand new, modernised Matrix python SDK, built from
the ground up, primarily to serve the needs of [nio-bot](https://pypi.org/p/nio-bot).
Built with [httpx](https://pypi.org/p/httpx) and [pydantic](https://pypi.org/p/pydantic),
MatrixCore allows you to build rich client applications without having to worry about all
the dirty complicated processing.

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

Want to discuss MatrixCore? suggest things? Please contact me in the NioBot Matrix room:
[#niobot:nexy7574.co.uk](https://matrix.to/#/#niobot:nexy7574.co.uk)

## Contributing

Please **discuss with me ahead of time** before contributing anything to MatrixCore.
Until the first **beta**, contributions are generally not accepted due to the
unstable nature of the MatrixCore API.
If you discuss with me first, I will tell you whether a contribution would be accepted.

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

See the [examples/](examples/) directory for some examples.
## FAQ

### Why?

Existing SDKs for Python often feel archaic and/or don't support the latest Matrix spec, and commonly suffer from
cruft preventing easy updates. I am making my own SDK from scratch in order to completely rid all of these
downsides from the get-go, and aim to keep this library as up-to-date as possible to ensure a premium SDK
for all Python-based clients.

I also aim to keep the SDK's API consistent too, meaning that each response and error is clearly defined,
which is achieved by making use of pydantic models for most of the interface.
The SDK is also kept extensible by keeping the actual engine (`MatrixCoreHTTPClient`) separate from the
client implementation (`MatrixCore`). This means that if, for whatever reason, you want to use the
HTTP client independently (perhaps in your own independent client), you can do so predictably.
Hell, you can even make your own custom requests with `MatrixCoreHTTPClient._[get/post/put/delete]`,
as long as you define your own pydantic model for the response.

### How long?

MatrixCore is not reaching a stable version any time soon. I am hoping to get the first alpha out by June 2025,
or the end of the year at the latest.
