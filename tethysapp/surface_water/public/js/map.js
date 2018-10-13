$(function (){

    var map = TETHYS_MAP_VIEW.getMap();

    var waterMapUrl = $('#water_layer').attr('water_map_url');
    var handMapUrl = $('#hand_layer').attr('hand_map_url');

    var waterLayer = new ol.layer.Tile({
        crossOrigin: 'anonymous',
        source: new ol.source.XYZ({
            url: waterMapUrl
        })
    });

    var handLayer = new ol.layer.Tile({
        crossOrigin: 'anonymous',
        source: new ol.source.XYZ({
            url: handMapUrl
        })
    });

    var baseLayer = new ol.layer.Tile({
            source: new ol.source.XYZ({
            url: 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
        })
    });

    baseLayer.set('name', 'baseLayer');
    waterLayer.set('name', 'waterLayer');
    handLayer.set('name', 'handLayer');
    
    map.removeLayer(map.getLayers().get(0));
    map.addLayer(baseLayer);
    map.addLayer(waterLayer);
    map.addLayer(handLayer);
    
});
