# Aurora Message Search Service

## Design Decisions

For this API service, I assumed that the paginated endpoint would accept a natural-language query to match the content of each message. While a simple SQL implementation like `SELECT * FROM message WHERE message LIKE <user_query>` is possible, it would require scanning all messages on each request and would not meet the latency requirement of <100ms.

To efficiently retrieve results, I used an inverted-index approach. This maps each token to the messages containing it, enabling fast lookups without recomputing token occurrences. For large datasets, an external search engine like Elasticsearch would be suitable, but for our dataset of only 3,349 rows, the deployment and network overhead outweigh the benefits.

An in-memory Python-based index could meet the required latency but would require a custom implementation for building the index and handling pagination. Instead, I chose SQLite with its FTS5 extension, which provides pagination as well as keyword, phrase, and prefix matching out of the box, keeps data local, and avoids networking latency. This approach is lightweight, meets performance requirements, and allows future enhancements such as ranking or weighting with minimal changes. It also scales more gracefully if the dataset grows in the future.

### Performance Improvements

The current implementation achieves endpoint latencies comfortably below 100 ms. Latency can be further reduced to under 30 ms with minimal changes, such as warming SQLite’s page cache on service startup by running a full table scan or configuring SQLite to store the database entirely in memory. Both approaches ensure that queries avoid disk access.

An alternative would be to replace SQLite with a fully in-memory Python-based search engine. While this could offer slightly lower latency, the additional complexity of implementing and maintaining a custom in-memory index makes it suboptimal for this use case.

### Deployment

The service is deployed to the internet at a publicly accessible [url](https://aur-takehome.onrender.com/search) with q <`string`>, limit <`int`> and offset <`int`> as query parameters.  



