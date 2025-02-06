# Canister - the Cato Networks Internet Security Tester

Canister is a small, simple tool designed to help validate the configuration of security controls in a Cato customer account, and generate security events. It is distributed as a Python module consisting of two main components:

* Catcher, a server which acts as a target for requests and serves up several malware test files.
* Canister, a client which runs the tests and returns the results.

Both can be run independently, i.e. the Catcher can be used with other clients, and Canister can be pointed to any other co-operative web server.

## Catcher

To launch a Catcher instance from the CLI:

```
python -m catcher <ip> <port>
```

where the IP and port are the local IP and port to listen on. The server will continue to run until it is terminated with Control-C. This is not a complete implementation of a public-facing web service and should not be used as such.

To launch a Catcher instance from code:

```
>>> import catcher
>>> C = catcher.Catcher(host="127.0.0.1", port=8020)
>>> C.start()
>>>
```

Catcher launches the server in a separate thread, so execution will return immediately after the call to start(). To stop the server:

```
>>> C.shutdown()
LOG1 2025-02-05 14:25:43.456676+00:00> Shutting down the server
LOG1 2025-02-05 14:25:43.701400+00:00> Exiting server thread
```

## Canister

To run the Canister client with the default test set from the command line:

```
python -m canister <ip> <port>
```

Where the IP and port are the IP and port of the target server, which will usually be an instance of Catcher (but does not have to be). Not all tests use the target server.

To run Canister from code, loading the default set, executing the tests and then printing the results:

```
import canisterset
S = canisterset.CanisterSet(target="10.2.1.251")
S.load(canisterset.DEFAULT)
S.execute()
for T in S:
	print(f'{T.name:<40} {T.success}')
```
