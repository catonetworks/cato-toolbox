# cato-toolbox
Example scripts, reference code and helper utilities for building automated flows using Cato GraphQL API.
## eventsFeed.py
An example of how to use the eventsFeed() API to extract events from Cato. Features include:
* Marker persistence.
* Multiple stop conditions, including number of events fetched and total execution time.
* Multiple output options, including pretty print, Azure API and network stream.
* Error handling and compression.