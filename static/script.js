/**
 * @fileoverview Runs the Surface Water Tool application. The code is executed in the
 * user's browser. It communicates with the App Engine backend, renders output
 * to the screen, and handles user interactions.
 */

// Set the namespace
water = {};

// Starts the Surface Water Tool application. The main entry point for the app.
water.boot = function() {
	
	// create the app
	var app = new water.App();
	
	// save app to instance
	water.instance = app;
};

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

/**
 * Creates a Google Map for the given map type rendered.
 * The map is anchored to the DOM element with the CSS class 'map'.
 * @return {google.maps.Map} A map instance with the map type rendered.
 */
water.App.createMap = function() {
  var mapOptions = {
    center: water.App.DEFAULT_CENTER,
    zoom: water.App.DEFAULT_ZOOM,
	maxZoom: water.App.MAX_ZOOM,
	//disableDefaultUI: true,
	streetViewControl: false
  };
  var mapEl = $('.map').get(0);
  var map = new google.maps.Map(mapEl, mapOptions);
  return map;
};

// Load basic maps upon loading the main web page
water.App.prototype.loadBasicMaps = function() {
  var name1 = 'AoI_border';
  var name2 = 'AoI_fill';
  $.ajax({
    url: "/get_basic_maps",
    dataType: "json",
    success: function (data) {
	  water.instance.showBasicMap(data.eeMapId_fill, data.eeToken_fill, name2);
	  water.instance.setLayerOpacity('AoI_fill', parseFloat($("#aoiControl").val()));
	  water.instance.showBasicMap(data.eeMapId_border, data.eeToken_border, name1);
    },
    error: function (data) {
      console.log(data.responseText);
    }
  });
}

// Push map with mapId and token obtained from EE Python
water.App.prototype.showBasicMap = function(eeMapId, eeToken, name) {
  this.showLoadingAlert(name);
  //var mapType = water.App.getEeMapType(eeMapId, eeToken, name);  // obsolete, using ee.MapLayerOverlay instead
  var mapType = new ee.MapLayerOverlay(water.App.EE_URL + '/map', eeMapId, eeToken, {name: name});
  this.map.overlayMapTypes.push(mapType);
  // handle layer loading alerts
  mapType.addTileCallback((function(event) {
    if (event.count === 0) {
      this.removeLoadingAlert(name);
    } else {
	  this.showLoadingAlert(name);
	}
  }).bind(this));
};

// ---------------------------------------------------------------------------------- //
// Date picker
// ---------------------------------------------------------------------------------- //

// Initializes the date pickers.
water.App.prototype.initDatePickers = function() {
  // Create the date pickers.
  $('.date-picker').datepicker({
    format: 'yyyy-mm-dd',
    viewMode: 'days',
    minViewMode: 'days',
    autoclose: true,
    startDate: new Date('1988-01-01'),
    endDate: new Date()
  });
  $('.date-picker-2').datepicker({
    format: 'yyyy-mm-dd',
    viewMode: 'days',
    minViewMode: 'days',
    autoclose: true,
    startDate: new Date('1988-01-01'),
    endDate: new Date()
  });

  // Set default dates.
  $('.date-picker').datepicker('update', '2014-01-01');
  $('.date-picker-2').datepicker('update', '2014-12-31');

  // Respond when the user updates the dates.
  //$('.date-picker').on('changeDate', this.refreshImage.bind(this));
  
  // Respond when the user clicks the 'submit' button.
  $('.dateSubmit').on('click', this.refreshImage.bind(this));
};


/**
 * Returns the currently selected time period as a parameter.
 * @return {Object} The current time period in a dictionary.
 */
water.App.prototype.getTimeParams = function() {
  return {time_start: $('.date-picker').val(), time_end: $('.date-picker-2').val()};
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

water.App.prototype.getExpertParams = function() {
  return {
    climatology: $(".climatology-input").is(':checked'),
	month_index: parseInt($("#monthsControl").val()),
	defringe: $(".defringe-input").is(':checked'),
	pcnt_perm: parseFloat($('.percentile-input-perm').val()),
	pcnt_temp: parseFloat($('.percentile-input-temp').val()),
	water_thresh: parseFloat($('.water-threshold-input').val()),
	veg_thresh: parseFloat($('.veg-threshold-input').val()),
	hand_thresh: parseFloat($('.hand-threshold-input').val()),
	cloud_thresh: parseFloat($('.cloud-threshold-input').val())
  };
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

// Get all relevant info for new layer
water.App.prototype.getAllParams = function() {
  var timeParams   = this.getTimeParams();
  var expertParams = this.getExpertParams();
  return $.extend(timeParams, expertParams);
};

// Updates the image based on the current control panel config.
water.App.prototype.refreshImage = function() {
  
  var name = 'water';
  //var name1 = 'water_temporary';
  //var name2 = 'water_permanent';
  
  // obtain params
  var params = this.getAllParams();
  //console.log(params);  // for debugging/testing
    
  // check if map is already active (if so, return early)
  // or if time period is too short (if so, return early and give warning)
  // or, otherwise, update the map
  if (this.currentLayer['time_start'] === params['time_start'] && 
	  this.currentLayer['time_end'] === params['time_end'] && 
	  this.currentLayer['climatology'] === params['climatology'] && 
	  this.currentLayer['month_index'] === params['month_index'] && 
	  this.currentLayer['defringe'] === params['defringe'] && 
	  this.currentLayer['pcnt_perm'] === params['pcnt_perm'] && 
	  this.currentLayer['pcnt_temp'] === params['pcnt_temp'] &&
	  this.currentLayer['water_thresh'] === params['water_thresh'] && 
	  this.currentLayer['veg_thresh'] === params['veg_thresh'] && 
	  this.currentLayer['hand_thresh'] === params['hand_thresh'] && 
	  this.currentLayer['cloud_thresh'] === params['cloud_thresh']) {
	$('.warnings span').text('')
	$('.warnings').hide();
    return;
  } else if (params['climatology'] == true && this.numberOfDays(params['time_start'], params['time_end']) < water.App.MINIMUM_TIME_PERIOD_CLIMATOLOGY) {
	$('.warnings span').text('Warning! Time period for climatology is too short! Make sure it is at least 3 years (1095 days)!')
	$('.warnings').show();
    return;
  } else if (this.numberOfDays(params['time_start'], params['time_end']) < water.App.MINIMUM_TIME_PERIOD_REGULAR) {
	$('.warnings span').text('Warning! Time period is too short! Make sure it is at least 90 days!')
	$('.warnings').show();
    return;
  } else {
    
    //remove warnings
	$('.warnings span').text('')
	$('.warnings').hide();
	
    // remove map layers
	this.removeLayer(name);
	//this.removeLayer(name1);
	//this.removeLayer(name2);
	
	// add climatology slider if required
	if (params['climatology'] == true) {
	  $("#monthsControlSlider").show();
	} else {
	  $("#monthsControlSlider").hide();
	};
	
    // query new map
    $.ajax({
      url: "/get_water_map",
	  data: params,
      dataType: "json",
      success: function (data) {
		water.instance.setWaterMap(data.eeMapId, data.eeToken, name)
		//water.instance.setWaterMap(data.eeMapId_temporary, data.eeToken_temporary, name1)
        //water.instance.setWaterMap(data.eeMapId_permanent, data.eeToken_permanent, name2)
      },
      error: function (data) {
        console.log(data.responseText);
      }
    });
	
	// update current layer check
	this.currentLayer = params;
  }
};

// Push map with mapId and token obtained from EE Python
water.App.prototype.setWaterMap = function(eeMapId, eeToken, name) {
  //console.log(eeMapId)  // for debugging/testing
  this.showLoadingAlert(name);
  // obtain new layer
  //var mapType = water.App.getEeMapType(eeMapId, eeToken, name);  // obsolete, using ee.MapLayerOverlay instead
  var mapType = new ee.MapLayerOverlay(water.App.EE_URL + '/map', eeMapId, eeToken, {name: name});
  // remove old layer
  this.removeLayer(name);
  // add new layer
  this.map.overlayMapTypes.push(mapType);
  // handle layer loading alerts
  mapType.addTileCallback((function(event) {
    if (event.count === 0) {
      this.removeLoadingAlert(name);
    } else {
	  this.showLoadingAlert(name);
	}
  }).bind(this));
};

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
// Alerts
// ---------------------------------------------------------------------------------- //

water.App.prototype.showLoadingAlert = function(name) {
  if (name == 'water') {
    $(".waterAlert").show();
  } else if (name == 'AoI_fill') {
    $(".aoiAlert").show();
  } else if (name == 'water_permanent') {
    $(".waterPermAlert").show();
  } else if (name == 'water_temporary') {
    $(".waterTempAlert").show();
  } else {
    return
  }
}

water.App.prototype.removeLoadingAlert = function(name) {
  if (name == 'water') {
    $(".waterAlert").hide();
  } else if (name == 'AoI_fill') {
    $(".aoiAlert").hide();
  } else if (name == 'water_permanent') {
    $(".waterPermAlert").hide();
  } else if (name == 'water_temporary') {
    $(".waterTempAlert").hide();
  } else {
    return
  }
}

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

/** @type {string} The Earth Engine API URL. */
water.App.EE_URL = 'https://earthengine.googleapis.com';

/** @type {number} The default zoom level for the map. */
water.App.DEFAULT_ZOOM = 7;

/** @type {number} The max allowed zoom level for the map. */
water.App.MAX_ZOOM = 14;

/** @type {Object} The default center of the map. */
water.App.DEFAULT_CENTER = {lng: 104.0, lat: 12.5};

/** @type {string} The default date format. */
water.App.DATE_FORMAT = 'yyyy-mm-dd';

/** @type {number} The minimum allowed time period in days. */
water.App.MINIMUM_TIME_PERIOD_REGULAR = 90;

/** @type {number} The minimum allowed time period in days when climatology is activated. */
water.App.MINIMUM_TIME_PERIOD_CLIMATOLOGY = 1095;