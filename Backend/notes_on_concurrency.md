## Concurrent Access Support

- The application uses SQLAlchemy’s `create_engine` with connection pooling (`pool_pre_ping`, `pool_recycle`).  
  This allows multiple database connections to be used at the same time.

- Each FastAPI request gets its own `SessionLocal()` instance through the `get_db` dependency, and the session is closed when the request ends.  
  This ensures requests do **not** share session state.

- The `employees` router uses `get_db`, so each request already has its own isolated database session.

### What This Means

- Multiple users can read from the database at the same time, as long as MySQL is configured to support the expected concurrency.

- SQLAlchemy handles connection pooling and session isolation automatically.  
  No extra concurrency code is required in these modules.

- When adding write operations, continue using the same dependency pattern and use `commit()`/`rollback()` in your request handlers.  
  The database’s transaction isolation will handle concurrent writes safely.
