$(function (){

    var url = 'http://127.0.0.1:8000/apps/surface-water/';

    var update_button = $("[name='update-button']");

    update_button.click(function () {
        var start_date = $('input#start-date').val();
        var end_date = $('input#end-date').val();
        var data = {
            'start_date': start_date,
            'end_date'  : end_date
        };
        update_map(url + 'update-map');
    });

    function update_map(url, data) {
        // backslash at end of url is required
        if (url.substr(-1) !== "/") {
            url = url.concat("/");
        }

        var xhr = jQuery.ajax({
            type: 'GET',
            url: url,
            dataType: 'json',
            data: data
        });

        xhr.done(function(data) {
            addMapLayer(data);
        })
        .fail(function(xhr, status, error) {
            console.log(xhr.responseText);
        });

        return xhr;
    }

    var addMapLayer = function (data) {

        var map = TETHYS_MAP_VIEW.getMap();

        // remove before adding
        map.getLayers().forEach(function (layer) {
            if (layer.get('name') === 'waterLayer' || layer.get('name') === 'handLayer') {
                console.log(layer.get('name'));
                map.removeLayer(layer);
            }
        });

        // now add the layer
        var waterLayer = new ol.layer.Tile({
            crossOrigin: 'anonymous',
            source: new ol.source.XYZ({
                url: data.waterMapUrl
            })
        });

        var handLayer = new ol.layer.Tile({
            crossOrigin: 'anonymous',
            source: new ol.source.XYZ({
                url: data.handMapUrl
            })
        });

        waterLayer.set('name', 'waterLayer');
        handLayer.set('name', 'handLayer');

        map.addLayer(waterLayer);
        map.addLayer(handLayer);
    };

});
