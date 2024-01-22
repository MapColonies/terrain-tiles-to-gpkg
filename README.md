# tilesToGpkg CLI

```
tilesToGpkg [-h] [--gpkg_path [PATH]] 
                 [--watch] 
                 [--watch_patterns FILES_PATTERNS [FILES_PATTERNS ...]] 
                 [--extract SOURCE_GPKG OUTPUT_DIR [WORKERS = 2]]
                 [--dump DEST_PATH [SOURCE_PATH ...]] 
                 [--execute_sql DB_FILE SQL_STATEMENT] 
                 [--debug]
```

Watch a directory for tiles data and insert them into a GeoPackage.


## Generated GeoPackage Tables

### terrain_tiles Table

| cid | name       | type       | notnull | pk |
|----:|------------|------------|--------:|---:|
|   0 | fid        | INTEGER    |       1 |  1 |
|   1 | zoom_level | MEDIUMINT  |      0 |  0 |
|   2 | tile_column | MEDIUMINT |      0 |  0 |
|   3 | tile_row   | MEDIUMINT  |      0 |  0 |
|   4 | tile_data  | BLOB (Gzipped QMesh Tile) |      0 |  0 |

### Notes:
- `fid`: Feature ID
- `zoom_level`: Zoom level
- `tile_column`, `tile_row`: Indices
- `tile_data`: Gzipped QMesh Tile (ready for serving and using by Cesium.JS)

### layer_json Table

| cid | name | type   | notnull | pk |
|----:|------|--------|--------:|---:|
|   0 | fid  | INTEGER |      1 |  1 |
|   1 | data | TEXT    |      0 |  0 |

### Notes:
- `fid`: Feature ID
- `data`: JSON representation of layer information
- The `layer_json` table stores metadata used by Cesium.JS for rendering and interacting with the terrain. It includes information about tile availability, grid system details, and other relevant data required by Cesium.JS.


## **Arguments**

### **Positional Arguments**:

*   **src\_path**: Specify the root folder for tiles retrieval. Default is the current working directory. You can provide a custom source path.

### **Optional Arguments**:

*   **\-h, --help**: Show this help message and exit.
*   **\--gpkg\_path \[GPKG\_PATH\]**: Specify the GeoPackage path. Default is './terrain-tiles.gpkg'. You can provide a custom GeoPackage path.
*   **\--watch**: Use the file watcher. If provided, the script will watch for new and moved files. Default behavior is iterating through the source path searching for tiles.
*   **\--watch\_patterns WATCH\_PATTERNS**: Specify watch patterns if using the watcher. Default is \['\*.terrain', 'layer.json'\].
*   **\--debug**: Enable verbose logging for debugging, may hit performance.
*   **\--dump DUMP \[DUMP ...\]**: Dumps (append) one GeoPackage db to another using [ogr2ogr](https://gdal.org/programs/ogr2ogr.html#cmdoption-ogr2ogr-append).
*   **\--execute_sql DB_FILE SQL_STATEMENT** Execute SQL statements on an SQLite3 database.
*   **\--extract SOURCE_GPKG OUTPUT_DIR WORKERS = 2** Extract data from gpkg (generated with this CLI) back to files. Optionally, include the number of workers for parallel processing. (Default 2)

## **Run from Docker**

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

## Permission Considerations

### Handling User and Group IDs

If you encounter permission issues when working with files or directories inside the Docker container, it may be related to the user and group IDs used during the image build process. This can lead to mismatches with the user IDs on the host machine.

To address this, we provide flexibility in setting user and group IDs during the Docker image build. The default values are often set based on the first user and group on the host system.

During runtime, if you experience permission problems, you can override the default user and group IDs by using the `-u` option with the `docker run` command.

### Example Scenario

Consider a situation where files created by the `tilesToGpkg` CLI end up locked within the system. This can occur if the CLI creates files with credentials from a different user. In such cases, you might face challenges accessing or modifying those files, leading to potential permission conflicts.


### Usage

* If you want to use the default user and group IDs set during the image build, simply run the command as mentioned before:
```bash
docker run -it --name ttgpkg --rm \
-v "/path/to/your/data/folder":/data \
tiles-to-gpkg-cli:v1.0.0
```

* If you encounter permission issues and want to override the default user and group IDs at runtime, use the following command:
```bash
docker run \
  -it \
  -u <your-desired-uid>:<your-desired-gid> \
  --name ttgpkg \
  --rm \
  -v "/path/to/your/data/folder":/data \
  tiles-to-gpkg-cli:v1.0.0
```
Replace `<your-desired-uid>` and `<your-desired-gid>` with the desired user and group IDs. You can use `id -u` and `id -g `on the host machine to find your current user and group IDs.

### Recommendation
It is recommended to use the default user and group IDs first, as they should fit most use cases. Only adjust the user and group IDs at runtime if you encounter permission issues. This approach provides a balance between flexibility and simplicity, allowing you to address specific issues as needed.

## History Recording for Job Progress

The `tilesToGpkg` CLI includes a history recording feature to keep track of the job progress when building the GeoPackage. This functionality is especially useful in scenarios where the script may have stopped, and you want to resume the process without overriding or duplicating already copied tiles.

### How It Works

When the CLI is used to insert tiles into a GeoPackage, it records the job progress in a history database. This history database keeps track of the directories that have been successfully processed, along with a count of how many tiles have been processed in each directory.

### Managing History Records

If, for any reason, you need to re-run the script for a specific directory that was not fully copied, you can manage the history records using the `--execute_sql` tool provided by the CLI.

#### Example:

To remove the history record for a specific directory (e.g., '12/1234') from the history database and allow the script to consider it for processing again, you can use the following command:

```bash
tilesToGpkg --execute_sql /path/to/your/output.gpkg.history.sqlite "DELETE FROM history WHERE directory = '12/1234';"
```
This ensures that the next run of the script will consider the '12/1234' directory for processing, allowing you to close any gaps in the GeoPackage without restart the whole process from scratch.

### Note on Duplications

When removing a partially complete directory, some files may already have been processed, and duplications might occur. It is up to you to handle duplication removal after the directory is reprocessed. See the "Remove Duplications" in the examples section to learn how to efficiently manage duplications.

### History Database Details

The history database name will be `<output_gpkg_name>.history.sqlite`. It contains a table named `history` with columns `directory` representing the directory path (e.g., '12/1234') and `tiles_count` representing the count of tiles processed in that directory.

### Note

It's important to handle the history database with caution, as modifying it directly can impact the integrity of the job progress tracking. Always ensure that you understand the implications of any changes made to the history records.

## **Examples**

##### Watch a Directory for Specific File Patterns:

```bash
tilesToGpkg PATH_TO_DIR/terrain_new --watch --watch_patterns "*.terrain" "layer.json" "foo.*"
```

##### Populate a GeoPackage from a Directory:

```bash
tilesToGpkg PATH_TO_DIR/terrain_new --watch_patterns "*.terrain" "layer.json" "foo.*"
```

##### Extract layer data from GPKG 

```bash
tilesToGpkg --extract /source.gpkg /output/my_layer_tiles
```

## **Helpers**

##### Dump Data from One GeoPackage to Another:

```bash
tilesToGpkg PATH_TO_DIR/terrain_new --dump DEST_PATH SOURCE_PATH1 SOURCE_PATH2
```

##### Execute SQL Statements on an SQLite3 Database:

```bash
tilesToGpkg --execute_sql DB_FILE "SELECT * FROM your_table WHERE condition;"
```

##### Print duplications:

```bash
tilesToGpkg --execute_sql DB_FILE "SELECT COUNT(fid), zoom_level, tile_column, tile_row FROM terrain_tiles GROUP BY zoom_level, tile_column, tile_row HAVING COUNT(fid) > 1 ORDER BY COUNT(fid) DESC;"
```

##### Remove duplications:

```bash
tilesToGpkg --execute_sql DB_FILE "DELETE FROM terrain_tiles WHERE fid NOT IN ( SELECT fid FROM terrain_tiles GROUP BY zoom_level, tile_column, tile_row)"
```

#### **For more information, run `tilesToGpkg --help`**.

