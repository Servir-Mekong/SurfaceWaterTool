// ---------------------------------------------------------------------------------- //
// The application
// ---------------------------------------------------------------------------------- //

// The main Surface Water Tool application with default settings
water.App = function() {
  // Create and display the map.
  this.map = water.App.createMap();
  
  // The drawing manager, for drawing on the Google Map.
  this.drawingManager = water.App.createDrawingManager(this.map);
  
  // The currently active layer
  //(used to prevent reloading when requested layer is the same).
  this.currentLayer = {};
  
   // Initialize the UI components.
  this.initDatePickers();
  this.initRegionPicker();
  this.opacitySliders();
  this.expertSubmit();
  this.climatologySlider();
  this.initExport();
  
  // Load the basic background maps.
  this.loadBasicMaps();
  
   // Load the default image.
  this.refreshImage();
};

// ---------------------------------------------------------------------------------- //
// Region selection
// ---------------------------------------------------------------------------------- //

// Initializes the region picker.
water.App.prototype.initRegionPicker = function() {
  // Respond when the user chooses to draw a polygon.
  $('.region .draw').click(this.setDrawingModeEnabled.bind(this, true));

  // Respond when the user draws a polygon on the map.
  google.maps.event.addListener(
      this.drawingManager, 'overlaycomplete',
      (function(event) {
        if (this.getDrawingModeEnabled()) {
          this.handleNewPolygon(event.overlay);
        } else {
          event.overlay.setMap(null);
        }
      }).bind(this));

  // Cancel drawing mode if the user presses escape.
  $(document).keydown((function(event) {
    if (event.which == 27) this.setDrawingModeEnabled(false);
  }).bind(this));

  // Respond when the user cancels polygon drawing.
  $('.region .cancel').click(this.setDrawingModeEnabled.bind(this, false));

  // Respond when the user clears the polygon.
  $('.region .clear').click(this.clearPolygon.bind(this));
};

/**
 * Sets whether drawing on the map is enabled.
 * @param {boolean} enabled Whether drawing mode is enabled.
 */
water.App.prototype.setDrawingModeEnabled = function(enabled) {
  $('.region').toggleClass('drawing', enabled);
  var mode = enabled ? google.maps.drawing.OverlayType.POLYGON : null;
  this.drawingManager.setOptions({drawingMode: mode});
};

/**
 * Sets whether drawing on the map is enabled.
 * @return {boolean} Whether drawing mode is enabled.
 */
water.App.prototype.getDrawingModeEnabled = function() {
  return $('.region').hasClass('drawing');
};

// Clears the current polygon from the map and enables drawing.
water.App.prototype.clearPolygon = function() {
  this.currentPolygon.setMap(null);
  $('.region').removeClass('selected');
  $('.export').attr('disabled', true);
};

/**
 * Stores the current polygon drawn on the map and disables drawing.
 * @param {Object} opt_overlay The new polygon drawn on the map. If
 *     undefined, the default polygon is treated as the new polygon.
 */
water.App.prototype.handleNewPolygon = function(opt_overlay) {
  this.currentPolygon = opt_overlay;
  $('.region').addClass('selected');
  $('.export').attr('disabled', false);
  this.setDrawingModeEnabled(false);
};

// ---------------------------------------------------------------------------------- //
// Layer opacity control
// ---------------------------------------------------------------------------------- //

water.App.prototype.opacitySliders = function() {
  $("#aoiControl").on("slide", function(slideEvt) {
	water.instance.setLayerOpacity('AoI_fill', slideEvt.value);
  });
  $("#aoiControl").on("slideStop", function(slideEvt) {
	water.instance.setLayerOpacity('AoI_fill', slideEvt.value);
  });
  // in case of split up permanent and temporary water layers:
  /*
  $("#waterPermControl").on("slide", function(slideEvt) {
	water.instance.setLayerOpacity('water_permanent', slideEvt.value);
  });
  $("#waterPermControl").on("slideStop", function(slideEvt) {
	water.instance.setLayerOpacity('water_permanent', slideEvt.value);
  });
  $("#waterTempControl").on("slide", function(slideEvt) {
	water.instance.setLayerOpacity('water_temporary', slideEvt.value);
  });
  $("#waterTempControl").on("slideStop", function(slideEvt) {
	water.instance.setLayerOpacity('water_temporary', slideEvt.value);
  });
  */
  // in case of merged permanent and temporary water layers:
  $("#waterControl").on("slide", function(slideEvt) {
	water.instance.setLayerOpacity('water', slideEvt.value);
  });
  $("#waterControl").on("slideStop", function(slideEvt) {
	water.instance.setLayerOpacity('water', slideEvt.value);
  });
}

// ---------------------------------------------------------------------------------- //
// Expert controls input
// ---------------------------------------------------------------------------------- //

water.App.prototype.expertSubmit = function() {
  // Respond when the user clicks the 'submit' button.
  $('.reset-and-submit-button .expert-submit').on('click', this.refreshImage.bind(this));
};

// ---------------------------------------------------------------------------------- //
// Climatology slider
// ---------------------------------------------------------------------------------- //

water.App.prototype.climatologySlider = function() {
  $("#monthsControl").on("slideStop", this.refreshImage.bind(this));
}

// ---------------------------------------------------------------------------------- //
// Layer management
// ---------------------------------------------------------------------------------- //
/**
 * Removes the map layer(s) with the given name.
 * @param {string} name The name of the layer(s) to remove.
 */
water.App.prototype.removeLayer = function(name) {
  this.map.overlayMapTypes.forEach((function(mapType, index) {
    if (mapType && mapType.name == name) {
      this.map.overlayMapTypes.removeAt(index);
    }
  }).bind(this));
};

/**
 * Changes the opacity of the map layer(s) with the given name.
 * @param {string} name The name of the layer(s) to remove.
 */
water.App.prototype.setLayerOpacity = function(name, value) {
  this.map.overlayMapTypes.forEach((function(mapType, index) {
    if (mapType && mapType.name == name) {
	  var overlay = this.map.overlayMapTypes.getAt(index);
      overlay.setOpacity(value);
    }
  }).bind(this));
};

// ---------------------------------------------------------------------------------- //
// Export functionality
// ---------------------------------------------------------------------------------- //

// -- PLACEHOLDER UNTIL EXPORT FUNCTIONALITY IS FINISHED --
water.App.prototype.initExport = function() {
  // Temporary click functionality, remove when export functionality is finished!!
  var export_click_count = 0;
  $('.export').click(function () {
	if (export_click_count == 0) {
	  $('.warnings span').text('Export functionality is not implemented yet! This will be activated in the future. Click the export button again to remove this message.');
	  $('.warnings').show();
	  export_click_count = 1;
	} else {
	  $('.warnings span').text('');
	  $('.warnings').hide();
	  export_click_count = 0;
	}
  });
};

// ---------------------------------------------------------------------------------- //
// Static helpers and constants
// ---------------------------------------------------------------------------------- //

// Computes number of days between two dates
water.App.prototype.numberOfDays = function(day1, day2) {
  var oneDay     = 24*60*60*1000; // hours*minutes*seconds*milliseconds
  var firstDate  = new Date(day1);
  var secondDate = new Date(day2);
  return Math.round(Math.abs((firstDate.getTime() - secondDate.getTime())/(oneDay)));
}

/**
 * NOTE: obsolete, using ee.MapLayerOverlay instead!
 * Generates a Google Maps map type (or layer) for the passed-in EE map id. See:
 * https://developers.google.com/maps/documentation/javascript/maptypes#ImageMapTypes
 * @param {string} eeMapId The Earth Engine map ID.
 * @param {string} eeToken The Earth Engine map token.
 * @return {google.maps.ImageMapType} A Google Maps ImageMapType object for the
 *     EE map with the given ID and token.
 */
water.App.getEeMapType = function(eeMapId, eeToken, name) {
  var eeMapOptions = {
    getTileUrl: function(tile, zoom) {
      var url = water.App.EE_URL + '/map/';
      url += [eeMapId, zoom, tile.x, tile.y].join('/');
      url += '?token=' + eeToken;
      return url;
    },
    tileSize: new google.maps.Size(256, 256),
	name: name,
	opacity: 1.0
  };
  return new google.maps.ImageMapType(eeMapOptions);
};

/**
 * Creates a drawing manager for the passed-in map.
 * @param {google.maps.Map} map The map for which to create a drawing
 *     manager.
 * @return {google.maps.drawing.DrawingManager} A drawing manager for
 *     the given map.
 */
water.App.createDrawingManager = function(map) {
  var drawingManager = new google.maps.drawing.DrawingManager({
    drawingControl: false,
    polygonOptions: {
      fillColor: '#ff0000',
      strokeColor: '#ff0000'
    }
  });
  drawingManager.setMap(map);
  return drawingManager;
};
