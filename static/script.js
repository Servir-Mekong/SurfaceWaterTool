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
	this.aoiParams = {};
	this.waterParams = {};
  
   // Initialize the UI components.
  this.initDatePickers();
  this.initRegionPicker();
	this.toggleBoxes();
  this.opacitySliders();
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
	streetViewControl: false,
	mapTypeControl: true,
	mapTypeControlOptions: {position: google.maps.ControlPosition.RIGHT_BOTTOM}
  };
  var mapEl = $('.map').get(0);
  var map = new google.maps.Map(mapEl, mapOptions);
  return map;
};

// Load basic maps upon loading the main web page
water.App.prototype.loadBasicMaps = function() {
  var name1 = 'AoI_fill';
	var name2 = 'AoI_border';
  $.ajax({
    url: "/get_basic_maps",
    dataType: "json",
    success: function (data) {
		water.instance.aoiParams = {'mapId': data.eeMapId_fill, 'token': data.eeToken_fill};
	  water.instance.showBasicMap(data.eeMapId_fill, data.eeToken_fill, name1, 0);
	  water.instance.setLayerOpacity('AoI_fill', parseFloat($("#aoiControl").val()));
	  water.instance.showBasicMap(data.eeMapId_border, data.eeToken_border, name2, 1);
    },
    error: function (data) {
      console.log(data.responseText);
    }
  });
}

// Push map with mapId and token obtained from EE Python
water.App.prototype.showBasicMap = function(eeMapId, eeToken, name, index) {
  this.showLoadingAlert(name);
  //var mapType = water.App.getEeMapType(eeMapId, eeToken, name);  // obsolete, using ee.MapLayerOverlay instead
  var mapType = new ee.MapLayerOverlay(water.App.EE_URL + '/map', eeMapId, eeToken, {name: name});
  //this.map.overlayMapTypes.push(mapType);        // old, just push to array, will always show latest layer on top
	this.map.overlayMapTypes.setAt(index, mapType);  // new, use index to keep correct zIndex when adding/removing layers
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
  $('.date-picker').datepicker('update', '2016-01-01');
  $('.date-picker-2').datepicker('update', '2016-12-31');

  // Respond when the user updates the dates.
  //$('.date-picker').on('changeDate', this.refreshImage.bind(this));
  
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
			water.instance.waterParams = {'mapId': data.eeMapId, 'token': data.eeToken};
			water.instance.setWaterMap(data.eeMapId, data.eeToken, name, 2)
			//water.instance.setWaterMap(data.eeMapId_temporary, data.eeToken_temporary, name1, 2)
			//water.instance.setWaterMap(data.eeMapId_permanent, data.eeToken_permanent, name2, 3)
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
water.App.prototype.setWaterMap = function(eeMapId, eeToken, name, index) {
  this.showLoadingAlert(name);
  // obtain new layer
  //var mapType = water.App.getEeMapType(eeMapId, eeToken, name);  // obsolete, using ee.MapLayerOverlay instead
  var mapType = new ee.MapLayerOverlay(water.App.EE_URL + '/map', eeMapId, eeToken, {name: name});
  // remove old layer
  this.removeLayer(name);
  // add new layer
  //this.map.overlayMapTypes.push(mapType);        // old, just push to array, will always show latest layer on top
	this.map.overlayMapTypes.setAt(index, mapType);  // new, use index to keep correct zIndex when adding/removing layers
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
      //this.map.overlayMapTypes.removeAt(index);   // old, hard removal
			this.map.overlayMapTypes.setAt(index, null);  // new, instead set null at the same index (to keep length of array intact, used for adding/removing layers and keep their zIndex intact)
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
		//console.log('layer should be toggled on now!');
		if (name == 'water') {
			this.setWaterMap(this.waterParams.mapId, this.waterParams.token, 'water', 2);
		} else if (name == 'AoI_fill') {
			this.showBasicMap(this.aoiParams.mapId, this.aoiParams.token, 'AoI_fill', 0);
			water.instance.setLayerOpacity('AoI_fill', parseFloat($("#aoiControl").val()));
		}
	} else {
		//console.log('layer should be toggled off now!');
		this.removeLayer(name);
	}
}

// ---------------------------------------------------------------------------------- //
// Layer toggle control
// ---------------------------------------------------------------------------------- //

water.App.prototype.toggleBoxes = function() {
	$('#checkbox-aoi').on("change", function() {
		water.instance.toggleLayer('AoI_fill', this.checked);
	});
	$('#checkbox-water').on("change", function() {
		water.instance.toggleLayer('water', this.checked);
	});
}

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
				} else {
					return;
				}
			} else {
				for (var i=0; i<nr_selected; i++) {
					water.instance.removeLayer(name);
				}
				nr_selected = 1;
				water.instance.points = [];
			}
		}
		if (selection == 'Tiles') {
			$.ajax({
				url: "/select_tile",
				data: params,
				dataType: "json",
				success: function (data) {
					water.instance.showMap(data.eeMapId, data.eeToken, name, 4);
					$('.export').attr('disabled', false);
					//water.instance.point = params;
					water.instance.points.push(params);
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
					water.instance.showMap(data.eeMapId, data.eeToken, name, 4);
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
				},
				error: function (data) {
					console.log(data.responseText);
				}
			});
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
		// Allow multiple selection if the user presses and holds down ctrl.  // WORK IN PROGRESS
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
  var name = 'adm_bounds';
  $.ajax({
    url: "/get_adm_bounds_map",
    dataType: "json",
    success: function (data) {
			water.instance.showMap(data.eeMapId, data.eeToken, name, 3);
    },
    error: function (data) {
      console.log(data.responseText);
    }
  });
}

// Load tiles maps
water.App.prototype.loadTilesMap = function() {
  var name = 'tiles';
  $.ajax({
    url: "/get_tiles_map",
    dataType: "json",
    success: function (data) {
			water.instance.showMap(data.eeMapId, data.eeToken, name, 3);
    },
    error: function (data) {
      console.log(data.responseText);
    }
  });
}

// Show map
water.App.prototype.showMap = function(eeMapId, eeToken, name, index) {
  var mapType = new ee.MapLayerOverlay(water.App.EE_URL + '/map', eeMapId, eeToken, {name: name});
  //this.map.overlayMapTypes.push(mapType);        // old, just push to array, will always show latest layer on top
	this.map.overlayMapTypes.setAt(index, mapType);  // new, use index to keep correct zIndex when adding/removing layers
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
			export_name = 'SurfaceWaterTool_' + base_params.time_start + '_' + base_params.time_end;
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
					//water.instance.showMap(data.eeMapId, data.eeToken, 'test', 4);
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
						//water.instance.showMap(data.eeMapId, data.eeToken, 'test', 4);
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
water.App.DEFAULT_CENTER = {lng: 102.0, lat: 12.5};

/** @type {string} The default date format. */
water.App.DATE_FORMAT = 'yyyy-mm-dd';

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
