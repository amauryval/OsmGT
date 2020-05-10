
const HARP_TOKEN = process.env.harpgl_token;

const canvas = document.getElementById('map');
const map = new harp.MapView({
   canvas,
   theme: "https://unpkg.com/@here/harp-map-theme@latest/resources/berlin_tilezen_night_reduced.json",
   //For tile cache optimization:
   maxVisibleDataSourceTiles: 40, 
   tileCacheSize: 100
});

const mapControls = new harp.MapControls(map);
mapControls.maxTiltAngle = 60;
const france = new harp.GeoCoordinates(45.757239, 4.833212);
map.lookAt({ target: france, zoomLevel: 16.1, tilt: 60, heading: 50 });
map.zoomLevel = 18;

const ui = new harp.MapControlsUI(mapControls);
canvas.parentElement.appendChild(ui.domElement);

map.resize(window.innerWidth, window.innerHeight);
window.onresize = () => map.resize(window.innerWidth, window.innerHeight);

map.clearTileCache();


const omvDataSource = new harp.OmvDataSource({
   baseUrl: "https://xyz.api.here.com/tiles/herebase.02",
   apiFormat: harp.APIFormat.XYZOMV,
   styleSetName: "tilezen",
   authenticationCode: HARP_TOKEN,
});

map.addDataSource(omvDataSource);

/*dispay roads*/
fetch('network.geojson')
.then(data => data.json())
.then(data => {
   const geoJsonDataProvider = new harp.GeoJsonDataProvider("network", data);
   const geoJsonDataSource = new harp.OmvDataSource({
      dataProvider: geoJsonDataProvider,
      name: "network"
   });

    map.addDataSource(geoJsonDataSource).then(() => {
       const styles = [{
          "when": "$geometryType ^= 'line'",
          "renderOrder": 1001,
          "technique": "solid-line",
          "attr": {
             "color": "##FF4500",
             "transparent": false,
             "opacity": 1,
             "metricUnit": "Pixel",
             "lineWidth": 2.5
          }
       },
       {
          "when": "$geometryType ^= 'line'",
          "renderOrder": 1000,
          "technique": "solid-line",
          "attr": {
             "color": "#000000",
             "transparent": false,
             "opacity": 1,
             "metricUnit": "Pixel",
             "lineWidth": 3
          }
       }]
       geoJsonDataSource.setStyleSet(styles);
       map.update();
    });
})

/*dispay poi*/
fetch('poi.geojson')
.then(data => data.json())
.then(data => {
   const geoJsonDataProvider = new harp.GeoJsonDataProvider("POIs", data);
   const geoJsonDataSource = new harp.OmvDataSource({
      dataProvider: geoJsonDataProvider,
      name: "POIs"
   });

    map.addDataSource(geoJsonDataSource).then(() => {
       const styles = [{
            when: "$geometryType == 'point'",
            technique: "circles",
            renderOrder: 10001,
            attr: {
                color: "##DC143C",
                size: 8
            }
        },
        {
            when: "$geometryType == 'point'",
            technique: "circles",
            renderOrder: 10000,
            attr: {
                color: "##000000",
                size: 10
            }
        }]
       geoJsonDataSource.setStyleSet(styles);
       map.update();
    });


})


const options = {
    labels: false,
    toneMappingExposure: 1.0,
    outline: {
        enabled: false,
        ghostExtrudedPolygons: false,
        thickness: 0.004,
        color: "#898989"
    },
    bloom: {
        enabled: true,
        strength: 0.5,
        threshold: 0.83,
        radius: 1
    },
    vignette: {
        enabled: true,
        offset: 1.0,
        darkness: 1.0
    },
    sepia: {
        enabled: true,
        amount: 0.55
    }
};

const updateRendering = () => {
    // snippet:effects_example.ts
    map.renderLabels = options.labels;
    map.renderer.toneMappingExposure = options.toneMappingExposure;
    map.mapRenderingManager.outline.enabled = options.outline.enabled;
    map.mapRenderingManager.updateOutline(options.outline);
    map.mapRenderingManager.bloom = options.bloom;
    map.mapRenderingManager.vignette = options.vignette;
    map.mapRenderingManager.sepia = options.sepia;
    // end:effects_example.ts
    map.update();
};

updateRendering();