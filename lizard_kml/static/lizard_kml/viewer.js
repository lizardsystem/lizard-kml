google.load('earth', '1');
var ge = null;
var initialKmlUrl = null;

function kmlViewerInit(argInitialKmlUrl) {
    initialKmlUrl = argInitialKmlUrl;
    google.earth.createInstance('map3d', initCallback, failureCallback);
}

function kmlViewerLoadKml(kmlUrl) {
    if (ge) {
        // remove currently loaded features
        var features = ge.getFeatures();
        while (features.getFirstChild())
           features.removeChild(features.getFirstChild());
    
        // have the plugin download and parse the requested KML file
        google.earth.fetchKml(ge, kmlUrl, finishedLoading);
    }
}

function initCallback(pluginInstance) {
    ge = pluginInstance;
    ge.getWindow().setVisibility(true);

    kmlViewerLoadKml(initialKmlUrl);
}

function failureCallback() {
    window.alert("failed to create Google Earth plugin instance");
}

function finishedLoading(kmlObject) {
    if (kmlObject) {
        ge.getFeatures().appendChild(kmlObject);
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
    else {
        window.alert("failed to load KML data");
    }
}
