from typing import Optional, Dict
from osgeo import gdal, ogr
import threading
from queue import Queue

class OGRConnectionPool:
    def __init__(self, max_connections: int, *args, **kwargs):
        self.max_connections: int = max_connections
        self.connection_args = args
        self.connection_kwargs = kwargs
        self._pool: Queue = Queue(max_connections)
        self._in_use: Dict[ogr.DataSource, int] = {}
        self._lock: threading.Lock = threading.Lock()

        for _ in range(max_connections):
            connection = self._create_connection()
            if connection is None:
                raise FileNotFoundError(f"Couldn't create a connection to GPKG at {self.connection_args}")
            self._pool.put(connection)

    def _create_connection(self) -> ogr.DataSource:
        return gdal.OpenEx(*self.connection_args, **self.connection_kwargs)

    def get_connection(self) -> Optional[ogr.DataSource]:
        with self._lock:
            if not self._pool.empty():
                connection = self._pool.get()
                self._in_use[connection] = self._in_use.get(connection, 0) + 1
                return connection
            else:
                # Pool is empty
                # Return connection from _is_use that has the lease connections
                connection = min(self._in_use, key=self._in_use.get, default=None)
                if connection:
                    self._in_use[connection] += 1
                    return connection
                
                return None

    def release_connection(self, connection: ogr.DataSource) -> None:
        with self._lock:
            if connection in self._in_use:
                self._in_use[connection] -= 1
                if self._in_use[connection] == 0:
                    del self._in_use[connection]
                    self._pool.put(connection)

    def close_all_connections(self) -> None:
        with self._lock:
            while not self._pool.empty():
                connection = self._pool.get()
                connection = None  # Close the connection