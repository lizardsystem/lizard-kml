google.load('earth', '1');
var ge = null;
var kfc = new KmlFileCollection();
var currentKmlParams = {lift:0.0, exaggeration:1.0, colormap:''};

// "API"
function kmlViewerInit() {
    google.earth.createInstance('map3d', initCallback, failureCallback);
}

function initCallback(pluginInstance) {
    ge = pluginInstance;
    ge.getWindow().setVisibility(true);

    // fly to default view once, on init
    var lookAt = ge.createLookAt('');
    lookAt.setLatitude(52.0938); // utrecht
    lookAt.setLongitude(5.0867);
    lookAt.setRange(600000.0);
    ge.getView().setAbstractView(lookAt);
}

function failureCallback() {
    window.alert("failed to create Google Earth plugin instance");
}

// "API"
function kmlViewerLoadKml(url, isDynamic) {
    if (ge) {
        kfc.loadKmlFile(url, isDynamic);
    }
}

// "API"
function kmlViewerSetLift(lift) {
    currentKmlParams['lift'] = lift;
    kfc.reloadAllDynamic();
}

// "API"
function kmlViewerSetExaggeration(exaggeration) {
    currentKmlParams['exaggeration'] = exaggeration;
    kfc.reloadAllDynamic();
}

// "API"
function kmlViewerSetColormap(colormap) {
    currentKmlParams['colormap'] = colormap;
    $('#colormaps').dialog('close');
    kfc.reloadAllDynamic();
}

// "API"
function kmlViewerUnloadAll() {
    kfc.unloadAll();
}

function addPlacemarkClickListeners(kmlObject) {
    var placemarks = kmlObject.getElementsByType('KmlPlacemark');
    for (var i = 0; i < placemarks.getLength(); ++i) {
        var placemark = placemarks.item(i);
        var url = '/kml/info/'+ placemark.getId() + '/';
        google.earth.addEventListener(placemark, 'click', function(event) { setDescription(event, url);});
    }
}

function setDescription(event, url) {
    var placemark = event.getTarget()
    $.get(url, {}, function(data) { placemark.setDescription(data) });
}

function partial(func /*, 0..n args */) {
    var args = Array.prototype.slice.call(arguments, 1);
    return function() {
        var allArguments = args.concat(Array.prototype.slice.call(arguments));
        return func.apply(this, allArguments);
    };
}

// "overridden" from lizard.js
function setUpTooltips() {
    $(".legend-tooltip-kml").each(function () {
        if (!$(this).data("popup-initialized")) {
            $(this).data("popup-initialized", true);
            $(this).tooltip({
                position: 'bottom left',
                effect: 'fade',
                offset: [0, -10]
            });
        }
    });
}

function KmlFileCollection() {
    this.kmlFiles = [];
    // loads new or reloads existing kml file
    this.loadKmlFile = function(url, isDynamic) {
        var foundKmlFile = null;
        for(var i = 0; i < this.kmlFiles.length; i++) {
            var kmlFile = this.kmlFiles[i];
            if (kmlFile.baseUrl == url) {
                foundKmlFile = kmlFile;
                break;
            }
        }
        if (foundKmlFile == null) {
            foundKmlFile = new KmlFile(url, isDynamic);
            this.kmlFiles.push(foundKmlFile);
            foundKmlFile.load(true);
        }
        else {
            foundKmlFile.load(false);
        }
    };
    // call when params (lift, exaggeration etc) changed
    this.reloadAllDynamic = function() {
        for(var i = 0; i < this.kmlFiles.length; i++) {
            var kmlFile = this.kmlFiles[i];
            if (kmlFile.isDynamic) {
                kmlFile.load(false);
            }
        }
    };
    this.unloadAll = function() {
        for(var i = 0; i < this.kmlFiles.length; i++) {
            var kmlFile = this.kmlFiles[i];
            kmlFile.unload();
        }
        this.kmlFiles.length = 0; // this is no joke
    };
}

function KmlFile(baseUrl, isDynamic) {
    this.baseUrl = baseUrl;
    this.isDynamic = isDynamic;
    this.updateCounter = 0;
    this.kmlObject = null;
    this.fullUrl = function() {
        if (this.isDynamic)
            return this.baseUrl + '?' + jQuery.param(currentKmlParams);
        else
            return this.baseUrl;
    };
    this.load = function(doResetView) {
        this.updateCounter++;
        google.earth.fetchKml(ge, this.fullUrl(), partial(this.finishedLoading, this, this.updateCounter, doResetView));
    };
    this.finishedLoading = function(kmlFile, currentUpdateCount, doResetView, kmlObject) {
        if (kmlFile.updateCounter <= currentUpdateCount) {
            if (kmlObject) {
                // remove currently loaded features, if there are any
                kmlFile.unload();
                // add new features
                kmlFile.kmlObject = kmlObject;
                ge.getFeatures().appendChild(kmlObject);
                // add click handlers
                if (kmlFile.isDynamic)
                    addPlacemarkClickListeners(kmlObject);
                // fly to view defined by KML, if desired
                if (doResetView && kmlObject.getAbstractView()) {
                    ge.getView().setAbstractView(kmlObject.getAbstractView());
                }
            }
            else {
                window.alert("failed to load KML data");
            }
        }
    };
    this.unload = function() {
        if (this.kmlObject != null) {
            ge.getFeatures().removeChild(this.kmlObject);
        }
    };
}
