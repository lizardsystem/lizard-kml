google.load('earth', '1');
var ge = null;
var initialKmlUrl = null;
var currentKmlUrl = null;
var currentKmlParams = {lift:0, exaggeration:0};
var isInitial = true;

// "API"
function kmlViewerInit(argInitialKmlUrl) {
    initialKmlUrl = argInitialKmlUrl;
    google.earth.createInstance('map3d', initCallback, failureCallback);
}

function initCallback(pluginInstance) {
    ge = pluginInstance;
    ge.getWindow().setVisibility(true);

    kmlViewerLoadKml(initialKmlUrl);
}

// "API"
function kmlViewerLoadKml(kmlUrl) {
    if (ge) {
        currentKmlUrl = kmlUrl;
        updateKml();
    }
}

// "API"
function kmlViewerSetLift(lift) {
    currentKmlParams['lift'] = lift;
    updateKml();
}

// "API"
function kmlViewerSetExaggeration(exaggeration) {
    currentKmlParams['exaggeration'] = exaggeration;
    updateKml();
}

// TODO: deal with "cancelled" updates, when sliders were adjusted during an update
function updateKml() {
    if (ge && currentKmlUrl && currentKmlParams) {
        // remove currently loaded features
        var features = ge.getFeatures();
        while (features.getFirstChild()) {
            features.removeChild(features.getFirstChild());
        }
        // have the plugin download and parse the requested KML file
        var url  = currentKmlUrl + '?' + jQuery.param(currentKmlParams);
        google.earth.fetchKml(ge, url, finishedLoading);
    }
}

function failureCallback() {
    window.alert("failed to create Google Earth plugin instance");
}

function finishedLoading(kmlObject) {
    if (kmlObject) {
        ge.getFeatures().appendChild(kmlObject);
        if (isInitial) {
            // 'fly' to default view on initial load
            isInitial = false;
            if (kmlObject.getAbstractView()) {
                // the KML file defines a default view, 'fly' to it
                ge.getView().setAbstractView(kmlObject.getAbstractView());
            }
            else {
                // no default view, 'fly' to a fixed position
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
