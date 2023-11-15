import time, os, logging, signal
from queue import Queue, Empty
import watchdog.events
import watchdog.observers
import watchdog
from osgeo import gdal, ogr
from src.utils import patterns_match
from src.constants import TERRAIN_TILES_TABLE, LAYER_JSON_TABLE
from src.FileHandler import Handler
from src.HistoryDB import HistoryDatabase

logger = logging.getLogger(__name__)

class TilesToGpkg:
    def __init__(self, source_dir: str, gpkg_path: str, is_watch_mode: bool, watch_patterns: list) -> None:
        self.source_dir = source_dir
        self.is_watch_mode = is_watch_mode
        self.watch_patterns = watch_patterns
        self.gpkg_path = gpkg_path
        self.event_queue = Queue()
        self.history_db = HistoryDatabase(f"{gpkg_path}.history.sqlite")

        # Check if the GeoPackage file already exists
        if os.path.exists(gpkg_path):
            gpkg_dir, gpkg_filename = os.path.split(gpkg_path)
            gpkg_name, gpkg_ext = os.path.splitext(gpkg_filename)

            # Find the next available number to append
            counter = 1
            while os.path.exists(os.path.join(gpkg_dir, f"{gpkg_name}_{counter}{gpkg_ext}")):
                counter += 1

            # Append the number to the filename
            gpkg_name = f"{gpkg_name}_{counter}"

            # Update the GeoPackage path
            self.gpkg_path = os.path.join(gpkg_dir, f"{gpkg_name}{gpkg_ext}")

            logger.info(f"Output file {gpkg_path} already exist, renaming to {self.gpkg_path}")


        gdal.AllRegister()

        signal.signal(signal.SIGINT, self.handle_interrupt)

        driver = ogr.GetDriverByName("GPKG")
        if driver is None:
            logger.error("GeoPackage driver is not available.")
            raise RuntimeError("GeoPackage driver is not available.")

        ds = driver.CreateDataSource(self.gpkg_path)

        if ds is None:
            logger.error("Failed to create GeoPackage.")
            raise RuntimeError("Failed to create GeoPackage.")
        
        self.ds = ds
        self.ds.ExecuteSQL("PRAGMA journal_mode = wal;")

        tiles_table = ds.CreateLayer(TERRAIN_TILES_TABLE, geom_type=ogr.wkbNone)
        layer_json_table = ds.CreateLayer(LAYER_JSON_TABLE, geom_type=ogr.wkbNone)

        layer_json_table.CreateField(ogr.FieldDefn("data", ogr.OFTString))

        tiles_table.CreateField(ogr.FieldDefn("zoom_level", ogr.OFTInteger))
        tiles_table.CreateField(ogr.FieldDefn("tile_column", ogr.OFTInteger))
        tiles_table.CreateField(ogr.FieldDefn("tile_row", ogr.OFTInteger))
        tiles_table.CreateField(ogr.FieldDefn("tile_data", ogr.OFTBinary))

        self.tiles_table = tiles_table
        self.layer_json_table = layer_json_table

        if is_watch_mode:
            observer = self.watch_files_in_dir()

            try:
                while True:
                    self.process_events()
            except KeyboardInterrupt:
                self.stop_watcher()
                observer.stop()
                observer.join()
                time.sleep(2)

        else:
            self.iterate_files_in_dir()
    
    def handle_interrupt(self, signum, frame):
        print("Received KeyboardInterrupt. Stopping...")
        self.stop_watcher()
        raise SystemExit

    def iterate_files_in_dir(self):
        logger.info(f'Iterating over {self.watch_patterns} files in {self.source_dir}.')
        
        for root, _, files in os.walk(self.source_dir):
            root_components = os.path.normpath(root).split(os.path.sep)[-2:]
            if all(component.isdigit() for component in root_components):
                # Presumably tiles directory
                zoom_level, tile_column = map(int, root_components)

                if self.history_db.has_directory(f"{zoom_level}/{tile_column}"):
                    logger.debug(f"Skipping {root}")
                    continue

                for filename in files:
                    if patterns_match(filename, self.watch_patterns):
                        tile_path = os.path.join(root, filename)
                        self.process_tile(tile_path)
        
        logger.info('Indexing GeoPackage...')
        self.ds.ExecuteSQL("CREATE INDEX tiles_idx ON terrain_tiles (zoom_level, tile_column, tile_row)")
        self.history_db.close_connection()

    def watch_files_in_dir(self):
        logger.info(f'Watching {self.source_dir} for {self.watch_patterns} files.')

        event_handler = Handler(self.watch_patterns, self.event_queue)
        observer = watchdog.observers.Observer()
        observer.schedule(event_handler, path=self.source_dir, recursive=True)
        observer.start()

        return observer

    def process_events(self):
        try:
            file_path = self.event_queue.get(timeout=1)
            logger.debug(f"Processing event: {file_path}")
            self.process_tile(file_path)
            self.event_queue.task_done()
        except Empty:
            logger.debug("No events in the queue.")
            pass
        except Exception as e:
            logger.error(f"Error processing events: {e}")
            import traceback
            traceback.print_exc()

    def process_tile(self, tile_path):
        logger.debug(f"Processing {tile_path}")

        if "layer.json" in tile_path:
            with open(tile_path, "r") as jsonFile:
                layerJsonData = jsonFile.read()
            
            logger.debug(layerJsonData)

            layerJsonFeature = ogr.Feature(self.layer_json_table.GetLayerDefn())
            layerJsonFeature.SetField("data", layerJsonData)
            self.layer_json_table.CreateFeature(layerJsonFeature)

            return

        path_components = tile_path.split(os.path.sep)

        try:
            zoom_level = int(path_components[-3])
            tile_column = int(path_components[-2])
            tile_row = int(os.path.splitext(path_components[-1])[0])
        except ValueError:
            logger.error(f"Error processing tile: {tile_path}. Unable to extract zoom level, tile column, or tile row.")
            raise RuntimeError(f"Error processing tile: {tile_path}. Unable to extract zoom level, tile column, or tile row.")
        
        directory = f"{zoom_level}/{tile_column}"

        with open(tile_path, "rb") as tile_file:
            tile_data = tile_file.read()

        feature = ogr.Feature(self.tiles_table.GetLayerDefn())
        feature.SetField("zoom_level", zoom_level)
        feature.SetField("tile_column", tile_column)
        feature.SetField("tile_row", tile_row)
        feature.SetFieldBinaryFromHexString("tile_data", tile_data.hex())
        self.tiles_table.CreateFeature(feature)

        self.history_db.update_history(directory)

        feature = None

    def stop_watcher(self):
        logger.info('Indexing GeoPackage...')
        self.ds.ExecuteSQL("CREATE INDEX tiles_idx ON terrain_tiles (zoom_level, tile_column, tile_row)")
        self.ds = None
        self.history_db.close_connection()