# tilesToGpkg CLI Usage Examples:

```
tilesToGpkg [-h] [--gpkg_path [PATH]] 
                 [--watch] 
                 [--watch_patterns FILES_PATTERNS [FILES_PATTERNS ...]] 
                 [--extract OUTPUT_DIR SOURCE_GPKG WORKERS = 2]
                 [--dump DEST_PATH [SOURCE_PATH ...]] 
                 [--execute_sql DB_FILE SQL_STATEMENT] 
                 [--debug]
```

Watch a directory for tiles data and insert them into a GeoPackage.

### **Positional Arguments**:

*   **src\_path**: Specify the root folder for tiles retrieval. Default is the current working directory. You can provide a custom source path.

### **Optional Arguments**:

*   **\-h, --help**: Show this help message and exit.
*   **\--gpkg\_path \[GPKG\_PATH\]**: Specify the GeoPackage path. Default is './terrain-tiles.gpkg'. You can provide a custom GeoPackage path.
*   **\--watch**: Use the file watcher. If provided, the script will watch for new and moved files. Default behavior is iterating through the source path searching for tiles.
*   **\--watch\_patterns WATCH\_PATTERNS**: Specify watch patterns if using the watcher. Default is \['\*.terrain', 'layer.json'\].
*   **\--debug**: Enable verbose logging for debugging, may hit performance.
*   **\--dump DUMP \[DUMP ...\]**: Dumps (append) one GeoPackage db to another using ogr2ogr.
*   **\--execute_sql DB_FILE SQL_STATEMENT** Execute SQL statements on an SQLite3 database.
*   **\--extract OUTPUT_DIR SOURCE_GPKG WORKERS = 2** Extract data from gpkg (generated with this CLI) back to files. Optionally, include the number of workers for parallel processing. (Default 2)

1. **Clone this Repository**

2. **Build the Docker Image:**
    ```bash
    docker build -t tiles-to-gpkg-cli .
    ```
   
   This command builds the Docker image locally using the provided Dockerfile.

3. **Run the Docker Container:**
    ```bash
    docker run -it --name ttgpkg --rm \
    -v "/path/to/your/data/folder":/data \
    tiles-to-gpkg-cli:v1.0.0
    ```

    Replace `/path/to/your/data/folder` with the actual path to the folder containing your QMESH data.

4. **Execute Commands:**

    Once inside the container, you can execute `tilesToGpkg` commands on your data.


### **Examples**:

##### Watch a Directory for Specific File Patterns:

`tilesToGpkg PATH_TO_DIR/terrain_new --watch --watch_patterns "*.terrain" "layer.json" "foo.*"`

##### Populate a GeoPackage from a Directory:

`tilesToGpkg PATH_TO_DIR/terrain_new --watch_patterns "*.terrain" "layer.json" "foo.*"`

##### Extract layer data from GPKG 
`tilesToGpkg --extract /source.gpkg /output/my_layer_tiles`

#### **Helpers**:

##### Dump Data from One GeoPackage to Another:

`tilesToGpkg PATH_TO_DIR/terrain_new --dump DEST_PATH SOURCE_PATH1 SOURCE_PATH2`

##### Execute SQL Statements on an SQLite3 Database:

`tilesToGpkg --execute_sql DB_FILE "SELECT * FROM your_table WHERE condition;"`

**Print duplications:**

`tilesToGpkg --execute_sql DB_FILE "SELECT COUNT(fid), zoom_level, tile_column, tile_row FROM terrain_tiles GROUP BY zoom_level, tile_column, tile_row HAVING COUNT(fid) > 1 ORDER BY COUNT(fid) DESC;"`

**Remove duplications:**

`tilesToGpkg --execute_sql DB_FILE "DELETE FROM terrain_tiles WHERE fid NOT IN ( SELECT fid FROM terrain_tiles GROUP BY zoom_level, tile_column, tile_row)"`


#### **For more information, run `tilesToGpkg --help`**.

