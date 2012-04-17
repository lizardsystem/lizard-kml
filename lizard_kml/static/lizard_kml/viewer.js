google.load('earth', '1');
var ge = null;
var currentKmlUrl = null;
var currentKmlParams = {lift:0, exaggeration:1};
var updateCounter = 0; // only load latest update

// "API"
function kmlViewerInit() {
    google.earth.createInstance('map3d', initCallback, failureCallback);
}

function initCallback(pluginInstance) {
    ge = pluginInstance;
    ge.getWindow().setVisibility(true);
}

function failureCallback() {
    window.alert("failed to create Google Earth plugin instance");
}

// "API"
function kmlViewerLoadKml(kmlUrl) {
    if (ge) {
        currentKmlUrl = kmlUrl;
        updateKml(true);
    }
}

// "API"
function kmlViewerSetLift(lift) {
    currentKmlParams['lift'] = lift;
    updateKml(false);
}

// "API"
function kmlViewerSetExaggeration(exaggeration) {
    currentKmlParams['exaggeration'] = exaggeration;
    updateKml(false);
}

function updateKml(doResetView) {
    if (ge && currentKmlUrl && currentKmlParams) {
        // remove currently loaded features
        removeOldFeatures();
        // have the plugin download and parse the requested KML file
        var url  = currentKmlUrl + '?' + jQuery.param(currentKmlParams);
        updateCounter++;
        google.earth.fetchKml(ge, url, partial(finishedLoading, updateCounter, doResetView));
    }
}

function finishedLoading(updateCount, doResetView, kmlObject) {
    if (updateCounter <= updateCount) {
        if (kmlObject) {
            // remove currently loaded features (again)
            removeOldFeatures();
            // add new features
            ge.getFeatures().appendChild(kmlObject);
            // fly to view
            if (doResetView) {
                // 'fly' to default view on initial load
                if (kmlObject.getAbstractView()) {
                    // the KML file defines a default view, 'fly' to it
                    ge.getView().setAbstractView(kmlObject.getAbstractView());
                }
                // no default view, 'fly' to a fixed position
                else {
                    var lookAt = ge.createLookAt('');
                    lookAt.setLatitude(52.0938); // utrecht
                    lookAt.setLongitude(5.0867);
                    lookAt.setRange(600000.0);
                    ge.getView().setAbstractView(lookAt);
                }
            }
        }
        else {
            window.alert("failed to load KML data");
        }
    }
    // else: skip the update
}

function removeOldFeatures() {
    // remove currently loaded features
    var features = ge.getFeatures();
    while (features.getFirstChild()) {
        features.removeChild(features.getFirstChild());
    }
}

function partial(func /*, 0..n args */) {
    var args = Array.prototype.slice.call(arguments, 1);
    return function() {
        var allArguments = args.concat(Array.prototype.slice.call(arguments));
        return func.apply(this, allArguments);
    };
}
