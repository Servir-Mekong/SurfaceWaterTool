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
  // create and display the map
  this.map = water.App.createMap();

  // drawing manager
  this.drawingManager = water.App.createDrawingManager(this.map);

  // The currently active layer
  //(used to prevent reloading when requested layer is the same)
  this.currentLayer = {};
	this.aoiParams = {};
	this.handParams = {};
	this.waterParams = {};

   // initialize the UI components
  this.initDatePickers();
  this.initRegionPicker();
	this.toggleBoxes();
  this.opacitySliders();
  this.climatologySlider();
  this.initExport();
	this.loadSearchBox();

	// set default parameters
	this.setDefaultParams();

  // load the background map
  this.loadBackground();

   // load the default image
  //this.refreshImage();  // calculate new layer based on initial params
	this.loadDefault();  // use pre-calculated layer
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
		zoomControl: true,
		zoomControlOptions: {position: google.maps.ControlPosition.LEFT_TOP},
		//disableDefaultUI: true,
		streetViewControl: false,
		mapTypeControl: true,
		mapTypeControlOptions: {position: google.maps.ControlPosition.TOP_LEFT},
		fullscreenControl: false
  };
  var mapEl = $('.map').get(0);
  var map = new google.maps.Map(mapEl, mapOptions);
  return map;
};

// Load background map upon loading the main web page
water.App.prototype.loadBackground = function() {
  $.ajax({
    url: "/get_background",
    dataType: "json",
    success: function (data) {
			// AoI
			water.instance.aoiParams = {'mapId': data.AoImapId, 'token': data.AoItoken, 'tile_url': data.AoIMapURL};
			if ($('#checkbox-aoi').is(':checked')){
				water.instance.showBackground(data.AoIMapURL, 'AoI', water.App.Z_INDEX_AOI);
				water.instance.setLayerOpacity('AoI', parseFloat($("#aoiControl").val()));
			}
			// HAND
			water.instance.handParams = {'mapId': data.HANDmapId, 'token': data.HANDtoken, 'tile_url': data.HANDMapURL};
			if ($('#checkbox-hand').is(':checked')){
				water.instance.showBackground(data.HANDMapURL, 'hand', water.App.Z_INDEX_HAND);
				water.instance.setLayerOpacity('hand', parseFloat($("#handControl").val()));
			}
    },
    error: function (data) {
      console.log(data.responseText);
    }
  });
}

// Load default water map upon loading the main web page
water.App.prototype.loadDefault = function() {
	// obtain default params and set those in current layer check
  //var params        = this.getAllParams();
	//this.currentLayer = params;
	// set map layer
  $.ajax({
    url: "/get_default",
    dataType: "json",
    success: function (data) {
			water.instance.waterParams = {'mapId': data.eeMapId, 'token': data.eeToken, 'tile_url': data.eeMapURL};
			water.instance.setWaterMap(data.eeMapURL, 'water', water.App.Z_INDEX_WATER);
    },
    error: function (data) {
      console.log(data.responseText);
    }
  });
}

// Push map with mapId and token obtained from EE Python
water.App.prototype.showBackground = function(eeMapURL, name, index) {
  // start by adding layer to loading list (also activates loading message)
  //this.addLoadingLayer(name);
  $(".spinner").show();
	// obtain new layer
  var mapType = this.getEeMapType(eeMapURL, name);
	// add new layer
	this.map.overlayMapTypes.setAt(index, mapType);
  $(".spinner").hide();
  // handle layer loading alerts
  // mapType.addTileCallback((function(event) {
  //   if (event.count === 0) {
  //     this.removeLoadingLayer(name);
  //   } else {
	//   this.addLoadingLayer(name);
	// }
  // }).bind(this));
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
  //$('.date-picker').datepicker('update', '2017-01-01');
  //$('.date-picker-2').datepicker('update', '2017-12-31');
  // Respond when the user clicks the 'submit' button.
  $('.submit').on('click', this.refreshImage.bind(this));
};


/**
 * Returns the currently selected time period as a parameter.
 * @return {Object} The current time period in a dictionary.
 */
water.App.prototype.getTimeParams = function() {
  return {time_start: $('.date-picker').val(), time_end: $('.date-picker-2').val()};
};

// ---------------------------------------------------------------------------------- //
// Expert controls input
// ---------------------------------------------------------------------------------- //

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
		cloud_thresh: parseInt($('.cloud-threshold-input').val())
  };
};

water.App.prototype.climatologySlider = function() {
  $("#monthsControl").on("slideStop", this.updateSlider.bind(this));
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

water.App.prototype.setParams = function(params) {
	// set input parameters
	$('.date-picker').val(params['time_start']);
	$('.date-picker-2').val(params['time_end']);
	$(".climatology-input").attr('checked', Boolean(params['climatology']));
	$("#monthsControl").val(params['month_index']);
	$(".defringe-input").attr('checked', Boolean(params['defringe']));
	$('.percentile-input-perm').val(params['pcnt_perm']);
	$('.percentile-input-temp').val(params['pcnt_temp']);
	$('.water-threshold-input').val(params['water_thresh']);
	$('.veg-threshold-input').val(params['veg_thresh']);
	$('.hand-threshold-input').val(params['hand_thresh']);
	$('.cloud-threshold-input').val(params['cloud_thresh']);
}

water.App.prototype.setDefaultParams = function() {
	this.setParams(water.App.DEFAULT_PARAMS);
}

water.App.prototype.updateSlider = function() {
	if (water.App.EXAMPLE_MONTHS_ACTIVE) {
		// get slider value
		var month = parseInt($("#monthsControl").val());
		// get mapid and token (calculated when specific example is opened)
		var month_data = water.instance.exampleParams[month];
		// update map using pre-calculated example
		water.instance.waterParams = {'mapId': month_data.eeMapId, 'token': month_data.eeToken, 'tile_url': month_data.eeMapURL};
		water.instance.setWaterMap(month_data.eeMapURL, 'water', water.App.Z_INDEX_WATER);
	} else {
		// update map with new calculation
		this.refreshImage();
	}
}

// Updates the image based on the current control panel config.
water.App.prototype.refreshImage = function() {
  $(".spinner").show();
  // obtain params
  var params = this.getAllParams();

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

  // remove map layer(s)
	this.removeLayer('water');

	// add climatology slider if required
	if (params['climatology'] == true) {
	  $(".months-slider").show();
	} else {
	  $(".months-slider").hide();
	};

	// query new map(s)
	$.ajax({
		url: "/get_water_map",
		data: params,
		dataType: "json",
		success: function (data) {
			water.instance.waterParams = {'mapId': data.eeMapId, 'token': data.eeToken, 'tile_url': data.eeMapURL};
			if ($('#checkbox-water').is(':checked')){
				water.instance.setWaterMap(data.eeMapURL, 'water', water.App.Z_INDEX_WATER);
				water.instance.setLayerOpacity('water', parseFloat($("#waterControl").val()));
			}
		},
		error: function (data) {
			console.log(data.responseText);
		}
	});

	// update current layer check
	this.currentLayer = params;
  }
};


/**
 * Generates a Google Maps map type (or layer) for the passed-in EE map id. See:
 * https://developers.google.com/maps/documentation/javascript/maptypes#ImageMapTypes
 * @param {string} eeMapURL The Earth Engine gee tile url.
 * @return {google.maps.ImageMapType} A Google Maps ImageMapType object for the
 *     EE map with the given ID and token.
 */
water.App.prototype.getEeMapType = function(eeMapURL, name) {
  var eeMapOptions = {
      getTileUrl: function (tile, zoom) {
            var url = eeMapURL.replace('{x}', tile.x)
                              .replace('{y}', tile.y)
                              .replace('{z}', zoom);
            return url;
        },
      tileSize: new google.maps.Size(256, 256),
      name: name,
      opacity: 1.0
    };
    var mapType = new google.maps.ImageMapType(eeMapOptions);

  return mapType;
};


// Push map with mapId and token obtained from EE Python
water.App.prototype.setWaterMap = function(eeMapURL, name, index) {
  var mapType = this.getEeMapType(eeMapURL, name);

  // start by adding layer to loading list (also activates loading message)
  //this.addLoadingLayer(name);
  $(".spinner").show();
  // obtain new layer
  //var mapType = new ee.MapLayerOverlay(mapType);
  // remove old layer
  //this.removeLayer(name);
  // add new layer
	this.map.overlayMapTypes.setAt(index, mapType);
  $(".spinner").hide();
  // handle layer loading alerts
  // mapType.addTileCallback((function(event) {
  //   if (event.count === 0) {
  //     this.removeLoadingLayer(name);
  //   } else {
	//   this.addLoadingLayer(name);
	// }
  // }).bind(this));
};

/**
 * Removes the map layer(s) with the given name.
 * @param {string} name The name of the layer(s) to remove.
 */
water.App.prototype.removeLayer = function(name) {
  this.map.overlayMapTypes.forEach((function(mapType, index) {
    if (mapType && mapType.name == name) {
		  // set null at relevant index (to keep length of array intact, used for adding/removing layers and keep their zIndex intact)
			this.map.overlayMapTypes.setAt(index, null);
    }
  }).bind(this));
};

/**
 * Changes the opacity of the map layer(s) with the given name.
 * @param {string} name The name of the layer(s) for which to change opacity.
 * @param {float} value The value to use for opacity of the layer(s).
 */
water.App.prototype.setLayerOpacity = function(name, value) {
  this.map.overlayMapTypes.forEach((function(mapType, index) {
    if (mapType && mapType.name == name) {
			var overlay = this.map.overlayMapTypes.getAt(index);
      overlay.setOpacity(value);
    }
  }).bind(this));
};

/**
 * Toggles map layer(s) on/off.
 * @param {string} name The name of the layer(s) to toggle on/off.
 * @param {boolean} toggle Whether to toggle the layer(s) on (true) or off (false).
 */
 water.App.prototype.toggleLayer = function(name, toggle) {
	if (toggle) {
		if (name == 'water') {
			this.setWaterMap(this.waterParams.tile_url, 'water', water.App.Z_INDEX_WATER);
			water.instance.setLayerOpacity('water', parseFloat($("#waterControl").val()));
		} else if (name == 'hand') {
			this.showBackground(this.handParams.tile_url, 'hand', water.App.Z_INDEX_HAND);
			water.instance.setLayerOpacity('hand', parseFloat($("#handControl").val()));
		} else if (name == 'AoI') {
			this.showBackground(this.aoiParams.tile_url, 'AoI', water.App.Z_INDEX_AOI);
			water.instance.setLayerOpacity('AoI', parseFloat($("#aoiControl").val()));
		}
	} else {
		this.removeLayer(name);
	}
}

// ---------------------------------------------------------------------------------- //
// Layer toggle and opacity control
// ---------------------------------------------------------------------------------- //

water.App.prototype.toggleBoxes = function() {
	$('#checkbox-aoi').on("change", function() {
		water.instance.toggleLayer('AoI', this.checked);
	});
	$('#checkbox-hand').on("change", function() {
		water.instance.toggleLayer('hand', this.checked);
	});
	$('#checkbox-water').on("change", function() {
		water.instance.toggleLayer('water', this.checked);
	});
}

water.App.prototype.opacitySliders = function() {
  $("#aoiControl").on("slide", function(slideEvt) {
		water.instance.setLayerOpacity('AoI', slideEvt.value);
  });
  $("#aoiControl").on("slideStop", function(slideEvt) {
		water.instance.setLayerOpacity('AoI', slideEvt.value);
  });
	$("#handControl").on("slide", function(slideEvt) {
		water.instance.setLayerOpacity('hand', slideEvt.value);
  });
  $("#handControl").on("slideStop", function(slideEvt) {
		water.instance.setLayerOpacity('hand', slideEvt.value);
  });
  $("#waterControl").on("slide", function(slideEvt) {
		water.instance.setLayerOpacity('water', slideEvt.value);
  });
  $("#waterControl").on("slideStop", function(slideEvt) {
		water.instance.setLayerOpacity('water', slideEvt.value);
  });
}

// ---------------------------------------------------------------------------------- //
// Alerts
// ---------------------------------------------------------------------------------- //

water.App.prototype.addLoadingLayer = function(name) {
	if (!water.App.LOADING_LAYERS.includes(name)) {
		water.App.LOADING_LAYERS.push(name);
	}
	this.checkLoadingAlert();
}

water.App.prototype.removeLoadingLayer = function(name) {
	if (water.App.LOADING_LAYERS.includes(name)) {
		var temp_index = water.App.LOADING_LAYERS.indexOf(name);
		water.App.LOADING_LAYERS.splice(temp_index, 1);
	}
	this.checkLoadingAlert();
}

water.App.prototype.checkLoadingAlert = function() {
	if (water.App.LOADING_LAYERS.length > 0) {
		$(".spinner").show();
	} else {
		$(".spinner").hide();
	}
}

// ---------------------------------------------------------------------------------- //
// Region selection
// ---------------------------------------------------------------------------------- //

// Initializes the region picker.
water.App.prototype.initRegionPicker = function() {

	// Respond when the user changes the selection
	$("input[name='polygon-selection-method']").change(polygonSelectionMethod);

	// initialize keydown storage variable
	var ctrl_key_is_down = false;
	// initialize number of selected polygons storage variable
	var nr_selected = 0;

	function polygonSelectionMethod() {
		// clear warnings
		$('.warnings span').text('');
		$('.warnings').hide();
		// reset Export button
		$('.export').attr('disabled', true);
		// reset keydown storage
		ctrl_key_is_down = false;
		// get the selected variable name
		var selection  = $("input[name='polygon-selection-method']:checked").val();
		// clear previously selected polygons
		for (var i=0; i<nr_selected; i++) {
			water.instance.removeLayer('selected_polygon');
		}
		// reset number of selected polygons
		nr_selected = 0;
		// reset clicked points
		water.instance.points = [];
		// carry out action based on selection
		if (selection == "Tiles"){
			// cancel drawing
			$('.region .cancel').click();
			// clear existing overlays
			water.instance.removeLayer('adm_bounds');
			$('.region .clear').click();
			// show overlay on map
			water.App.prototype.loadTilesMap();
		} else if (selection == "Adm. bounds"){
			// cancel drawing
			$('.region .cancel').click();
			// clear existing overlays
			water.instance.removeLayer('tiles');
			$('.region .clear').click();
			// show overlay on map
			water.App.prototype.loadAdmBoundsMap();
		} else if (selection == "Draw polygon"){
			// clear existing overlays
			water.instance.removeLayer('adm_bounds');
			water.instance.removeLayer('tiles');
			// setup drawing
			$('.region .draw').click();
		}
	}

	this.map.addListener('click', function(event) {
    $(".spinner").show();
		var selection = $("input[name='polygon-selection-method']:checked").val();
		if (selection == 'Tiles' || selection == 'Adm. bounds') {
			var coords = event.latLng;
			var lat = coords.lat();
			var lng = coords.lng();
			var params = {lat: lat, lng: lng};
			var name = 'selected_polygon';
			if (ctrl_key_is_down) {
				// check if current selection doesn't exceed allowed maximum
				if (nr_selected < water.App.MAX_SELECTION) {
					nr_selected += 1;
					if (selection == 'Tiles') {
						$.ajax({
							url: "/select_tile",
							data: params,
							dataType: "json",
							success: function (data) {
								water.instance.showMap(data.eeMapURL, name, water.App.Z_INDEX_POLY + nr_selected - 1);
								$('.export').attr('disabled', false);
								//water.instance.point = params;
								water.instance.points.push(params);
                $(".spinner").hide();
							},
							error: function (data) {
								console.log(data.responseText);
							}
						});
					} else if (selection == 'Adm. bounds') {
						console.log('NOT IMPLEMENTED YET FOR ADMIN BOUNDS!');
					}
				} else {
					return;
				}
			} else {
				for (var i=0; i<nr_selected; i++) {
					water.instance.removeLayer(name);
				}
				nr_selected = 1;
				water.instance.points = [];
				if (selection == 'Tiles') {
					$.ajax({
						url: "/select_tile",
						data: params,
						dataType: "json",
						success: function (data) {
							water.instance.showMap(data.eeMapURL, name, water.App.Z_INDEX_POLY);
							$('.export').attr('disabled', false);
							//water.instance.point = params;
							water.instance.points.push(params);
              $(".spinner").hide();
						},
						error: function (data) {
							console.log(data.responseText);
						}
					});
				} else if (selection == 'Adm. bounds') {
					$('.warnings span').text('')
					$('.warnings').hide();
					$.ajax({
						url: "/select_adm_bounds",
						data: params,
						dataType: "json",
						success: function (data) {
							water.instance.showMap(data.eeMapURL, name, water.App.Z_INDEX_POLY);
							//console.log(data.size);
							if (data.size > water.App.AREA_LIMIT_2) {
								$('.export').attr('disabled', true);
								$('.warnings span').text('The selected area is larger than ' + water.App.AREA_LIMIT_2 + ' km2. This exceeds the current limitations for downloading data. ' +
																				 'Please use one of the other region selection options to download data for this area.')
								$('.warnings').show();
							} else if (data.size > water.App.AREA_LIMIT_1) {
								$('.export').attr('disabled', false);
								$('.warnings span').text('The selected area is larger than ' + water.App.AREA_LIMIT_1 + ' km2. This is near the current limitation for downloading data. '+
																				 'Please be warned that the download might result in a corrupted zip file. You can give it a try or use  one of the other region selection options to download data for this area.')
								$('.warnings').show();
							} else {
								$('.export').attr('disabled', false);
							}
							//water.instance.point = params;
							water.instance.points.push(params);
              $(".spinner").hide();
						},
						error: function (data) {
							console.log(data.responseText);
						}
					});
				}
			}
		}
	});

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

  // handle actions when user presses certain keys
  $(document).keydown((function(event) {
		// Cancel region selection and related items if the user presses escape.
    if (event.which == 27) {
			// remove drawing mode
			this.setDrawingModeEnabled(false);
			// remove region selection
			$("input[name='polygon-selection-method']:checked").attr('checked', false);
			// clear map overlays
			water.instance.removeLayer('adm_bounds');
			water.instance.removeLayer('tiles');
			for (var i=0; i<nr_selected; i++) {
				water.instance.removeLayer('selected_polygon');
			}
			// clear any existing download links
			$('#link1').removeAttr('href');
			$('#link2').removeAttr('href');
			$('#link3').removeAttr('href');
			$('#link4').removeAttr('href');
			$('#link_metadata').removeAttr('href');
			$('#link_metadata').removeAttr('download');
			// remove download link(s) message
			$('#link1').css('display', 'none');
			$('#link2').css('display', 'none');
			$('#link3').css('display', 'none');
			$('#link4').css('display', 'none');
			$('#link_metadata').css('display', 'none');
			// reset variables
			water.instance.points = [];
			nr_selected = 0;
			// disable export button
			$('.export').attr('disabled', true);
			// hide export panel
			$('.download_panel').css('display', 'none');
		}
		// Allow multiple selection if the user presses and holds down ctrl.
		if (event.which == 17) {
			var selection = $("input[name='polygon-selection-method']:checked").val();
			if (selection == 'Tiles' || selection == 'Adm. bounds') {
				if (ctrl_key_is_down) {
					return;
				}
				ctrl_key_is_down = true;
			}
		}

  }).bind(this));
	// clear ctrl key event if key is released
	$(document).keyup((function(event) {
		if (event.which == 17) {
			ctrl_key_is_down = false;
		}
	}).bind(this));

  // Respond when the user cancels polygon drawing.
  //$('.region .cancel').click(this.setDrawingModeEnabled.bind(this, false));  // original function
	$('.region .cancel').click((function() {
		this.setDrawingModeEnabled(false);
		if ($("input[name='polygon-selection-method']:checked").val() == 'Draw polygon') {
			$("input[name='polygon-selection-method']:checked").attr('checked', false);
		}
	}).bind(this));

  // Respond when the user clears the polygon.
  //$('.region .clear').click(this.clearPolygon.bind(this));  // original function
	$('.region .clear').click((function() {
		// try to clear polygon (won't work if no polygon was drawn, try/catch to make it work)
		try {
			this.clearPolygon();
		} catch(err) {
			//console.log('Trying to remove a drawn polygon from map, but results in error:')
			//console.log(err);
		}
		if ($("input[name='polygon-selection-method']:checked").val() == 'Draw polygon') {
			$("input[name='polygon-selection-method']:checked").attr('checked', false);
		}
		$('.warnings span').text('');
		$('.warnings').hide();
	}).bind(this));
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
	var drawn_polygon_size = google.maps.geometry.spherical.computeArea(opt_overlay.getPath()) / 1e6;
	//console.log(drawn_polygon_size);
	if (drawn_polygon_size > water.App.AREA_LIMIT_2) {
		$('.export').attr('disabled', true);
		$('.warnings span').text('The drawn polygon is larger than ' + water.App.AREA_LIMIT_2 + ' km2. This exceeds the current limitations for downloading data. ' +
														 'Please draw a smaller polygon or use one of the other region selection options to download data for this area.')
		$('.warnings').show();
	} else if (drawn_polygon_size > water.App.AREA_LIMIT_1) {
		$('.export').attr('disabled', false);
		$('.warnings span').text('The drawn polygon is larger than ' + water.App.AREA_LIMIT_1 + ' km2. This is near the current limitation for downloading data. ' +
														 'Please be warned that the download might result in a corrupted zip file. You can give it a try, or draw a smaller polygon, or ' +
														 'use  one of the other region selection options to download data for this area.')
		$('.warnings').show();
	} else {
		$('.export').attr('disabled', false);
	}
  this.currentPolygon = opt_overlay;
  $('.region').addClass('selected');
  this.setDrawingModeEnabled(false);
};

/**
* Clear polygons from the map when changing region selection modes
**/
var clearMap = function(){
	// remove all polygons
	this.map.data.forEach(function (feature) {
	  this.map.data.remove(feature);
	});
}

// Load administrative boundaries maps
water.App.prototype.loadAdmBoundsMap = function() {
  $(".spinner").show();
  var name = 'adm_bounds';
  $.ajax({
    url: "/get_adm_bounds_map",
    dataType: "json",
    success: function (data) {
			water.instance.showMap(data.eeMapURL, name, 3);
      $(".spinner").hide();
    },
    error: function (data) {
      console.log(data.responseText);
    }
  });
}

// Load tiles maps
water.App.prototype.loadTilesMap = function() {
  $(".spinner").show();
  var name = 'tiles';
  $.ajax({
    url: "/get_tiles_map",
    dataType: "json",
    success: function (data) {
			water.instance.showMap(data.eeMapURL, name, 3);
      $(".spinner").hide();
    },
    error: function (data) {
      console.log(data.responseText);
    }
  });
}

// Show map
water.App.prototype.showMap = function(eeMapURL, name, index) {
  var mapType = water.App.prototype.getEeMapType(eeMapURL, name);
	this.map.overlayMapTypes.setAt(index, mapType);
  $(".spinner").hide();
};

// ---------------------------------------------------------------------------------- //
// Export functionality
// ---------------------------------------------------------------------------------- //

water.App.prototype.initExport = function() {
	$('.export').click(function () {
		// show panel
		$('.download_panel').css('display', 'block');
		// show prep message
		$('#download_prep').css('display', 'block');
		// clear any existing download links
		$('#link1').removeAttr('href');
		$('#link2').removeAttr('href');
		$('#link3').removeAttr('href');
		$('#link4').removeAttr('href');
		$('#link_metadata').removeAttr('href');
		$('#link_metadata').removeAttr('download');
		// remove download link(s) message
		$('#link1').css('display', 'none');
		$('#link2').css('display', 'none');
		$('#link3').css('display', 'none');
		$('#link4').css('display', 'none');
		$('#link_metadata').css('display', 'none');
		// get base parameters and export filename
		var base_params = water.App.prototype.getAllParams();
		var export_name = $("input[name='filename']").val();
		if (export_name == "") {
			export_name = 'SWMT_' + base_params.time_start + '_' + base_params.time_end;
		}
		// get download link(s)
		var region_selection = $("input[name='polygon-selection-method']:checked").val();
		if (region_selection == 'Draw polygon') {
			var coords_array = water.instance.currentPolygon.latLngs.b[0].b;
			var coords_list  = []
			coords_array.forEach(function(coords) {
				var lat = coords.lat();
				var lng = coords.lng();
				coords_list.push([lng,lat]);
			});
			var params = $.extend(base_params, {coords: JSON.stringify(coords_list)}, {export_name: export_name});
			$.ajax({
				url: "/export_drawn",
				data: params,
				dataType: "json",
				success: function (data) {
					// hide prep message
					$('#download_prep').css('display', 'none');
					// show result
					//console.log(data);
					//window.location.replace(data);
					$('#link1').css('display', 'block');
					$('#link1').attr('href', data);
				},
				error: function (data) {
					console.log(data.responseText);
				}
			});
		} else {
			// use asynchronous ajax calls to allow getting/showing multiple download links at once
			var async_ajax_call_export_counter  = 0;
			var async_ajax_call_export_function = function(params) {
				$.ajax({
					url: "/export_selected",
					async: true,
					data: params,
					dataType: "json",
					success: function (data) {
						// hide prep message
						$('#download_prep').css('display', 'none');
						// show result
						//console.log(data);
						//window.location.replace(data);
						$('#link' + (async_ajax_call_export_counter+1)).css('display', 'block');
						$('#link' + (async_ajax_call_export_counter+1)).attr('href', data);
						async_ajax_call_export_counter++;
						if (async_ajax_call_export_counter < water.instance.points.length) {
							point  = water.instance.points[async_ajax_call_export_counter];
							params = $.extend(base_params, point, {export_name: export_name});
							async_ajax_call_export_function(params);
						}
					},
					error: function (data) {
						console.log(data.responseText);
						async_ajax_call_export_counter++;
						if (async_ajax_call_export_counter < water.instance.points.length) {
							point  = water.instance.points[async_ajax_call_export_counter];
							params = $.extend(base_params, point, {export_name: export_name});
							async_ajax_call_export_function(params);
						}
					}
				});
			}
			var point  = water.instance.points[0];
			var params = $.extend(base_params, point, {export_name: export_name}, {region_selection: region_selection});
			async_ajax_call_export_function(params);
		}
		// get metadata
		var metadata_header = Object.keys(water.App.prototype.getAllParams()).join().toString();
		var metadata_values = $.map(water.App.prototype.getAllParams(), function(x){return x}).join().toString();
		var metadata_csv    = metadata_header + '\n' + metadata_values
		$('#link_metadata').css('display', 'block');
		$('#link_metadata').attr('download', export_name + '.csv');
		$('#link_metadata').attr('href', encodeURI("data:text/csv;charset=utf-8" + ',' + metadata_csv));
	});
};

// ---------------------------------------------------------------------------------- //
// Examples
// ---------------------------------------------------------------------------------- //

water.App.prototype.loadExample = function(example_id) {
	// handle visualization of app components
	$(".map").css("display", "block");
	$(".ui").css("display", "block");
	$(".legend").css("display", "block");
	$("#examples").css("display", "none");
	$("#about").css("display", "none");
	$(".months-slider").hide();
	$("#searchbox").css("display", "block");

	// remove old water layer
	water.instance.removeLayer('water');

	// carry out actions based on example id
	water.App.EXAMPLE_MONTHS_ACTIVE = false;
	if (example_id === 'example_1') {
		this.setParams(water.App.EXAMPLE_PARAMS_1);
		water.App.setMapCoords(water.App.EXAMPLE_CENTER_1, water.App.EXAMPLE_ZOOM_1);
	} else if (example_id === 'example_2') {
		this.setParams(water.App.EXAMPLE_PARAMS_2);
		water.App.setMapCoords(water.App.EXAMPLE_CENTER_2, water.App.EXAMPLE_ZOOM_2);
	} else if (example_id === 'example_3') {
		this.setParams(water.App.EXAMPLE_PARAMS_3);
		water.App.setMapCoords(water.App.EXAMPLE_CENTER_3, water.App.EXAMPLE_ZOOM_3);
	} else if (example_id === 'example_4') {
		this.setParams(water.App.EXAMPLE_PARAMS_4);
		water.App.setMapCoords(water.App.EXAMPLE_CENTER_4, water.App.EXAMPLE_ZOOM_4);
	} else if (example_id === 'example_5') {
		this.setParams(water.App.EXAMPLE_PARAMS_5);
		water.App.setMapCoords(water.App.EXAMPLE_CENTER_5, water.App.EXAMPLE_ZOOM_5);
		water.App.EXAMPLE_MONTHS_ACTIVE = true;
	}

	// update map
	if (example_id !== 'example_5') {
		params = {'example_id':example_id};
		$.ajax({
			url: "/get_example_map",
			data: params,
			dataType: "json",
			success: function (data) {
				water.instance.waterParams = {'mapId': data.eeMapId, 'token': data.eeToken, 'tile_url':data.eeMapURL};
				water.instance.setWaterMap(data.eeMapURL, 'water', water.App.Z_INDEX_WATER);
			},
			error: function (data) {
				console.log(data.responseText);
			}
		});
	} else {
		//this.addLoadingLayer('example');
    $(".spinner").show();
		$.ajax({
			url: "/get_example_months",
			dataType: "json",
			success: function (data) {
				$(".months-slider").show();
				water.instance.exampleParams = data;
				water.instance.waterParams = {'mapId': data[1].eeMapId, 'token': data[1].eeToken, 'tile_url':data[1].eeMapURL};
				water.instance.setWaterMap(data[1].eeMapURL, 'water', water.App.Z_INDEX_WATER);
				water.instance.removeLoadingLayer('example');
			},
			error: function (data) {
				console.log(data.responseText);
				water.instance.removeLoadingLayer('example');
			}
		});
	}
}

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
}

water.App.setMapCoords = function(center, zoom) {
	water.instance.map.panTo(center);
	water.instance.map.setZoom(zoom);
}

water.App.prototype.loadSearchBox = function() {
	var searchBox = new google.maps.places.Autocomplete(
		(document.getElementById('searchbox')), {types:['geocode']}
	);
	searchBox.addListener('place_changed', function() {
		var place = searchBox.getPlace();
		if (!place.geometry) {
			// User entered the name of a Place that was not suggested and
			// pressed the Enter key, or the Place Details request failed.
			//console.log("No location found for input: '" + place.name + "'");
			return;
		}
		// If the place has a geometry, then present it on a map.
		if (place.geometry.viewport) {
			water.instance.map.fitBounds(place.geometry.viewport);
		} else {
			water.instance.map.setCenter(place.geometry.location);
		}
	});
	return searchBox;
}

/** @type {string} The Earth Engine API URL. */
water.App.EE_URL = 'https://earthengine.googleapis.com';

/** @type {number} The default zoom level for the map. */
water.App.DEFAULT_ZOOM = 7;

/** @type {number} The max allowed zoom level for the map. */
water.App.MAX_ZOOM = 14;

/** @type {object} The default center of the map. */
water.App.DEFAULT_CENTER = {lng: 106.5, lat: 12.5};

/** @type {string} The default date format. */
water.App.DATE_FORMAT = 'yyyy-mm-dd';

/** @type {number} The z-index of map layers. */
water.App.Z_INDEX_AOI = 0;
water.App.Z_INDEX_HAND = 1;
water.App.Z_INDEX_PCNT = 2;
water.App.Z_INDEX_CLOUD = 3;
water.App.Z_INDEX_WATER = 4;
water.App.Z_INDEX_POLY  = 5;

/** @type {number} The minimum allowed time period in days. */
water.App.MINIMUM_TIME_PERIOD_REGULAR = 90;

/** @type {number} The minimum allowed time period in days when climatology is activated. */
water.App.MINIMUM_TIME_PERIOD_CLIMATOLOGY = 1095;

/** @type {number} The max allowed selection of polygons for download/export. */
water.App.MAX_SELECTION = 4;

/** @type {number} Soft limit on download area size. */
water.App.AREA_LIMIT_1 = 15000;

/** @type {number} Hard limit on download area size. */
water.App.AREA_LIMIT_2 = 20000;

/** @type {object} List storing map layers that are loading. */
water.App.LOADING_LAYERS = [];

/** @type {boolean} stores whether the example with months slider is active. */
water.App.EXAMPLE_MONTHS_ACTIVE = false;

/** @type {object} The center of the map for different examples. */
water.App.EXAMPLE_CENTER_1 = {lng: 105.5, lat: 11.65};
water.App.EXAMPLE_CENTER_2 = {lng: 96.95, lat: 18.1};
water.App.EXAMPLE_CENTER_3 = {lng: 100.5, lat: 15.1};
water.App.EXAMPLE_CENTER_4 = {lng: 96.77, lat: 24.26};
water.App.EXAMPLE_CENTER_5 = {lng: 104.6, lat: 12.81};

/** @type {number} The zoom level for the map for different examples. */
water.App.EXAMPLE_ZOOM_1 = 9;
water.App.EXAMPLE_ZOOM_2 = 11;
water.App.EXAMPLE_ZOOM_3 = 8;
water.App.EXAMPLE_ZOOM_4 = 11;
water.App.EXAMPLE_ZOOM_5 = 9;

/** @type {object} The input parameters for different examples. */
// default values
water.App.DEFAULT_PARAMS = {
	time_start: '2017-01-01',
	time_end: '2017-12-31',
	climatology: 0,
	month_index: 1,
	defringe: 0,
	pcnt_perm: 40,
	pcnt_temp: 8,
	water_thresh: 0.3,
	veg_thresh: 0.5,
	hand_thresh: 50,
	cloud_thresh: -1
};
// Permanent and temporary water
water.App.EXAMPLE_PARAMS_1 = {
	time_start: '2014-01-01',
	time_end: '2014-12-31',
	climatology: 0,
	month_index: 1,
	defringe: 0,
	pcnt_perm: 40,
	pcnt_temp: 8,
	water_thresh: 0.3,
	veg_thresh: 0.5,
	hand_thresh: 50,
	cloud_thresh: -1
};
// Reservoirs
water.App.EXAMPLE_PARAMS_2 = {
	time_start: '2008-01-01',
	time_end: '2011-12-31',
	climatology: 0,
	month_index: 1,
	defringe: 0,
	pcnt_perm: 40,
	pcnt_temp: 8,
	water_thresh: 0.3,
	veg_thresh: 0.6,
	hand_thresh: 50,
	cloud_thresh: -1
};
// Floods
water.App.EXAMPLE_PARAMS_3 = {
	time_start: '2011-02-01',
	time_end: '2012-01-31',
	climatology: 0,
	month_index: 1,
	defringe: 0,
	pcnt_perm: 40,
	pcnt_temp: 8,
	water_thresh: 0.3,
	veg_thresh: 0.6,
	hand_thresh: 50,
	cloud_thresh: -1
};
// River morphology / erosion
water.App.EXAMPLE_PARAMS_4 = {
	time_start: '2008-01-01',
	time_end: '2017-12-31',
	climatology: 0,
	month_index: 1,
	defringe: 0,
	pcnt_perm: 50,
	pcnt_temp: 8,
	water_thresh: 0.3,
	veg_thresh: 0.5,
	hand_thresh: 50,
	cloud_thresh: -1
};
// Seasonal inundation
water.App.EXAMPLE_PARAMS_5 = {
	time_start: '1988-01-01',
	time_end: '2017-12-31',
	climatology: 1,
	month_index: 1,
	defringe: 0,
	pcnt_perm: 40,
	pcnt_temp: 8,
	water_thresh: 0.3,
	veg_thresh: 0.5,
	hand_thresh: 50,
	cloud_thresh: -1
};
