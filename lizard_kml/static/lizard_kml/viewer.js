// Some plumbing to get all dependencies (Ext, Google Earth API) loaded properly.
var isGoogleEarthApiLoaded = false;
var isExtJsLoaded = false;

function refreshLoadedModules() {
    if (isExtJsLoaded && isGoogleEarthApiLoaded) {
        console.log('All ready');
        kvu.init();
    }
}

// Google Earth plugin
google.setOnLoadCallback(
    function () {
        console.log('GEAPI ready');
        isGoogleEarthApiLoaded = true;
        refreshLoadedModules();
    }
);
google.load('earth', '1');

// Ext JS
Ext.BLANK_IMAGE_URL = '/static_media/lizard_kml/extjs-4.1.1-rc2/resources/themes/images/default/tree/s.gif';
Ext.scopeResetCSS = true;
Ext.onReady(function () {
    console.log('Ext JS ready');
    isExtJsLoaded = true;
    refreshLoadedModules();
});
// Ext.Loader.setConfig({
   // enabled : true
// });
// Ext.require('Ext.fx.Anim');
// Ext.require('Ext.data.Tree');
// Ext.require('Ext.tree.Panel');

// global access these due to common usage
var geDownloadUrl = 'http://www.google.com/earth/explore/products/plugin.html';
var minimalPluginVersion = '6.2.2';
var ge = null;
var kvu = new KmlViewerUi();
var kfc = new KmlFileCollection();


// TEMP
var currentKmlParams = {
    lift:40.0,
    exaggeration:4.0,
    extrude:0,
    polyalpha:0.8,
    outline:0,
    move:0.1
};

/*
// "API"
function kmlViewerLoadKml(url, isDynamic) {
    if (ge) {
        kfc.loadKmlFile(url, isDynamic);
    }
}
*/
/*
// "API"
function kmlViewerUnloadAll() {
    kfc.unloadAll();
}
*/

// TEMP
function kmlViewerSetParam(k, v) {
    currentKmlParams[k] = v;
}

// TEMP
function kmlViewerCommitParams() {
    kfc.reloadAllDynamic();
}

// "API"
function kmlViewerSetColormap(colormap) {
    currentKmlParams['colormap'] = colormap;
    $('#colormaps').dialog('close');
}

/*
*/
// TEMP
function addPlacemarkClickListeners(kmlObject) {
    var placemarks = kmlObject.getElementsByType('KmlPlacemark');
    for (var i = 0; i < placemarks.getLength(); ++i) {
        var placemark = placemarks.item(i);
        var url = '/kml/info/'+ placemark.getId() + '/';
        google.earth.addEventListener(placemark, 'click', function(event) { setDescription(event, url);});
    }
}

// TEMP
function setDescription(event, url) {
    var placemark = event.getTarget()
    $.get(url, {}, function(data) { placemark.setDescription(data) });
}
/*
*/

/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */


/**
 * Shim for browsers not supporting:
 * https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects/Function/bind
 * (mostly < IE9)
 */
if (!Function.prototype.bind) {
    Function.prototype.bind = function (oThis) {
        if (typeof this !== "function") {
            // closest thing possible to the ECMAScript 5 internal IsCallable function
            throw new TypeError("Function.prototype.bind - what is trying to be bound is not callable");
        }
        var aArgs = Array.prototype.slice.call(arguments, 1),
            fToBind = this,
            fNOP = function () {},
            fBound = function () {
                return fToBind.apply(
                    this instanceof fNOP ? this : oThis || window,
                    aArgs.concat(Array.prototype.slice.call(arguments))
                );
            };
        fNOP.prototype = this.prototype;
        fBound.prototype = new fNOP();
        return fBound;
    };
}

/**
 * Currying utility function.
 */
function partial(func /*, 0..n args */) {
    var args = Array.prototype.slice.call(arguments, 1);
    return function() {
        var allArguments = args.concat(Array.prototype.slice.call(arguments));
        return func.apply(this, allArguments);
    };
}

/**
 * Abuse the Location object:
 * https://developer.mozilla.org/en/window.location
 * Works cross-browser.
 */
function parseUrl(url) {
    var a = document.createElement('a');
    a.href = url;
    return a;
}

/**
 * Does what it says.
 */
function parseVersionString(str) {
    if (typeof(str) != 'string') { return false; }
    var v = str.split('.');
    return {
        major: parseInt(v[0]) || 0,
        minor: parseInt(v[1]) || 0,
        patch: parseInt(v[2]) || 0
    }
}

/**
 * Does what it says.
 */
function minVersionMet(vmin, vcurrent) {
    minimum = parseVersionString(vmin);
    running = parseVersionString(vcurrent);
    if (running.major != minimum.major)
        return (running.major > minimum.major);
    else {
        if (running.minor != minimum.minor)
            return (running.minor > minimum.minor);
        else {
            if (running.patch != minimum.patch)
                return (running.patch > minimum.patch);
            else
                return true;
        }
    }
}

/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */

/**
 * UI component.
 */
function KmlViewerUi() {
    /**
     * Attributes
     */
    this.tsc = new GETimeSliderControl();
    this.treePanel = null;
    this.accordion = null;
}

/**
 * This method assumes the DOM is ready.
 */
KmlViewerUi.prototype.init = function() {
    // (lizard-ui) resize the ui
    setupLizardUi();
    this.initControls();
    this.removeLoadingOverlay(this.initGoogleEarth.bind(this));
};

/**
 */
KmlViewerUi.prototype.initGoogleEarth = function() {
    if (!google.earth.isSupported()) {
        this.replaceMapWithErrorMessage(
            'De Google Earth plugin wordt helaas niet ondersteund door uw systeem. ' +
            'Ga naar de website van <a href="' + geDownloadUrl + '">Google Earth</a> ' +
            'voor meer informatie.'
        );
    }
    else {
        if (!google.earth.isInstalled()) {
            this.replaceMapWithErrorMessage(
                'De Google Earth plugin kon niet worden gevonden. ' +
                'Ga naar de website van <a href="' + geDownloadUrl + '">Google Earth</a> ' +
                'en volg de instructies op, om deze te installeren. Herlaadt vervolgens deze website, door deze opnieuw te bezoeken.'
            );
        }
        else {
            google.earth.createInstance('map3d', this.geInitCallback.bind(this), this.geFailureCallback.bind(this));
        }
    }
};

/**
 */
KmlViewerUi.prototype.initControls = function() {
    // build a model for tree nodes containing some extra kml data
    Ext.define('KmlResourceNode', {
        extend: 'Ext.data.Model',
        fields: ['kml_id', 'text', 'description', 'kml_url', 'slug']
    });
    Ext.data.NodeInterface.decorate(KmlResourceNode);

    // create a store for adapting the json output
    var store = Ext.create('Ext.data.TreeStore', {
        listeners: {
            load: function(thisStore, rootNode, records, successful, eOpts){
                var categories = thisStore.proxy.reader.rawData.categories;
                categories.forEach(function(category) {
                    var categoryNode = rootNode.appendChild({
                        text: category.name,
                        expanded: true,
                        leaf: false
                    });
                    category.kml_resources.forEach(function(k) {
                        var krn = new KmlResourceNode({
                            kml_id: k.id,
                            text: k.name,
                            description: k.description,
                            leaf: true,
                            checked: false,
                            kml_url: k.kml_url,
                            slug: k.slug
                        });
                        categoryNode.appendChild(krn);
                    });
                });
            }
        },
        proxy: {
            type: 'ajax',
            url: '/kml/api_drf/?format=json',
            reader: {
                type: 'json'
            }
        }
    });

    // create the tree panel (and view)
    this.treePanel = Ext.create('Ext.tree.Panel', {
        title: 'Kaartlagen',
        store: store,
        rootVisible: false,
        plain: false,
        multiSelect: false,
        animate: false,
        useArrows: true,
        lines: false,
        stateful: false,
        border: false,
        listeners: {
            itemclick: function (thisView, node, item, index, event) {
                if (!node.isLeaf()) {
                    if (node.isExpanded()) {
                        node.collapse();
                    } else {
                        node.expand();
                    }
                }
                else {
                    var checked = !(node.get('checked'));
                    thisView.suspendEvents();
                    node.set('checked', checked);
                    thisView.resumeEvents();
                    //thisView.fireEvent('checkchange', node, checked);
                    if (checked) {
                        kvu.setControlsDisabled(true);
                        kfc.loadKmlFile(node.get('kml_id'), node.get('kml_url'), node.get('slug'));
                    }
                    else {
                        kfc.unloadKmlFile(node.get('kml_id'));
                    }
                }
            },
            checkchange: function (node, checked, eOpts) {
                //console.log('x=' + node.get('kml_url'));
                //kvu.setControlsDisabled(true);
            }
        }
    });

    // create the left accordion
    this.accordion = Ext.create('Ext.container.Container', {
        title: 'Accordion Layout',
        defaults: {
            // applied to each contained panel
            bodyStyle: 'padding:5px'
        },
        disabled: true,
        layout: {
            type: 'accordion',
            animate: false,
            multi: true,
            shrinkToFit: false
        },
        items: [
            this.treePanel,
            {
                title: 'Jarkus',
                html: '<br/>'
            }
        ],
        renderTo: Ext.get('extaccor')
    });
};

KmlViewerUi.prototype.setControlsDisabled = function(disabled) {
    this.accordion.setDisabled(disabled);
}

KmlViewerUi.prototype.removeLoadingOverlay = function(callback) {
    var loader = Ext.get('loader');
    loader.fadeOut({
        delay: 500,
        duration: 500,
        remove: true,
        callback: callback
    });
};

KmlViewerUi.prototype.geInitCallback = function (pluginInstance) {
    // determine version
    // if version detection fails, continue by default
    var acceptVersion = true;
    var vcurrent = pluginInstance.getPluginVersion();
    console.log('current version ' + vcurrent);
    try {
        acceptVersion = minVersionMet(minimalPluginVersion, vcurrent);
    }
    catch (err) {
        console.log('error parsing version: ' + err);
    }

    if (acceptVersion) {
        ge = pluginInstance;

        // enable international borders
        //ge.getLayerRoot().enableLayerById(ge.LAYER_BORDERS, true);
    
        // enable the sun
        //ge.getSun().setVisibility(true);
    
        // enable the atmosphere
        ge.getOptions().setAtmosphereVisibility(true);
    
        // make the plugin visible
        ge.getWindow().setVisibility(true);
    
        // fly to default view once, on init
        this.setDefaultView();
    
        // start timeslider control
        this.tsc.startControl();
        kvu.setControlsDisabled(false);
    }
    else {
        this.replaceMapWithErrorMessage(
            'Er is een verouderde versie van de Google Earth plugin (' + vcurrent + ') gedetecteerd. ' +
            'Om gebruik te maken van deze website, is minimaal versie ' + minimalPluginVersion + ' nodig. ' +
            'Ga naar de website van <a href="' + geDownloadUrl + '">Google Earth</a> ' +
            'om de nieuwste versie te installeren.'
        );
    }
};

KmlViewerUi.prototype.geFailureCallback = function () {
    this.replaceMapWithErrorMessage(
        'De Google Earth plugin kon niet worden gestart. ' +
        'Ga naar de website van <a href="' + geDownloadUrl + '">Google Earth</a> ' +
        'om de nieuwste versie te installeren.'
    );
};

KmlViewerUi.prototype.setDefaultView = function () {
    var lookAt = ge.createLookAt('');
    lookAt.setLatitude(52.0938); // utrecht
    lookAt.setLongitude(5.0867);
    lookAt.setRange(600000.0);
    ge.getView().setAbstractView(lookAt);
};

KmlViewerUi.prototype.replaceMapWithErrorMessage = function (html) {
    var $el;
    $el = $('#map3d-error-message');
    if ($el.length != 0) {
        // already a message on screen
        $el.append('<hr style="margin:0;"/>' + html);
    }
    else {
        // create the message div first
        $el = $('<div></div>')
            .attr('id', 'map3d-error-message')
            .html(html);
        $('#map3d').replaceWith($el);
    }
};

/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */

/**
 * Google Earth timeslider control.
 */
function GETimeSliderControl() {
    /**
     * Attributes
     */
    this.rateStep = 60 * 60 * 24 * 365; // amount of seconds in a year
    this.isPlaying = false; // keep our own playing / stopped state
    this.animationStopInterval = null;
};

GETimeSliderControl.prototype.startControl = function() {
    this.animationStopInterval = window.setInterval(this.animationStopTick.bind(this), 300);
};

GETimeSliderControl.prototype.stopControl = function() {
    if (this.animationStopInterval) {
        window.clearInterval(this.animationStopInterval);
    }
};

GETimeSliderControl.prototype.togglePlayPause = function() {
    // true if an animation is playing without us having
    // initiated it
    var isPlayingExternal = ge.getTime().getRate() > 0;
    if (this.isPlaying || isPlayingExternal) {
        // pause
        this.pause();
    }
    else {
        // 1 real second = 5 timeslider years
        if (this.isPastEnd()) {
            // at end, so rewind first
            this.rewind();
        }
        this.isPlaying = true;
        ge.getTime().setRate(this.rateStep * 5);
    }
};

GETimeSliderControl.prototype.rewind = function() {
    this.pause();
    this.setCurrentTime(this.getExtentBegin());
};

GETimeSliderControl.prototype.pause = function() {
    ge.getTime().setRate(0);
    this.isPlaying = false;
};

GETimeSliderControl.prototype.animationStopTick = function() {
    if (this.isPlaying) {
        if (this.isPastEnd()) {
            // we are past the extents, pause the animation
            this.pause();
            // revert time to the end of the extents
            this.setCurrentTime(this.getExtentEnd());
        }
    }
};

GETimeSliderControl.prototype.getExtentBegin = function() {
    var extents = ge.getTime().getControl().getExtents();
    return extents.getBegin().get();
};

GETimeSliderControl.prototype.getExtentEnd = function() {
    var extents = ge.getTime().getControl().getExtents();
    return extents.getEnd().get();
};

GETimeSliderControl.prototype.isPastEnd = function() {
    return this.getCurrentTimeEnd() >= this.getExtentEnd();
};

GETimeSliderControl.prototype.getCurrentTimeEnd = function() {
    var currentTime = ge.getTime().getTimePrimitive();
    var currentTimeEnd;
    if (currentTime.getType() == 'KmlTimeSpan') {
        currentTimeEnd = currentTime.getEnd().get();
    } else {
        currentTimeEnd = currentTime.getWhen().get();
    }
    return currentTimeEnd;
};

GETimeSliderControl.prototype.setCurrentTime = function(time) {
    var timeStamp = ge.createTimeStamp('');
    timeStamp.getWhen().set(time);
    ge.getTime().setTimePrimitive(timeStamp);
};

/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */

/**
 * Manages the collection of KML files loaded in the viewer.
 */
function KmlFileCollection() {
    /**
     * List of KmlFile objects.
     */
    this.kmlFiles = [];
}

/**
 * Loads a new, or reloads an existing kml file.
 */
KmlFileCollection.prototype.loadKmlFile = function(id, url, slug) {
    var foundKmlFile = null;
    for (var i = 0; i < this.kmlFiles.length; i++) {
        var kmlFile = this.kmlFiles[i];
        if (kmlFile.id == id) {
            foundKmlFile = kmlFile;
            break;
        }
    }
    if (foundKmlFile == null) {
        foundKmlFile = new KmlFile(id, url, slug);
        this.kmlFiles.push(foundKmlFile);
        foundKmlFile.load(true);
    }
    else {
        foundKmlFile.load(false);
    }
};

/**
 * Call this when params (lift, exaggeration etc) change.
 */
KmlFileCollection.prototype.reloadAllDynamic = function() {
    for (var i = 0; i < this.kmlFiles.length; i++) {
        var kmlFile = this.kmlFiles[i];
        if (kmlFile.slug === "jarkus" && kmlFile.kmlObject != null) {
            kmlFile.load(false);
        }
    }
};

/**
 */
KmlFileCollection.prototype.unloadAll = function() {
    for (var i = 0; i < this.kmlFiles.length; i++) {
        var kmlFile = this.kmlFiles[i];
        kmlFile.unload();
    }
    this.kmlFiles.length = 0; // clear a JavaScript list (this is no joke)
};

/**
 */
KmlFileCollection.prototype.unloadKmlFile = function(id) {
    var foundKmlFile = null;
    for (var i = 0; i < this.kmlFiles.length; i++) {
        var kmlFile = this.kmlFiles[i];
        if (kmlFile.id == id) {
            foundKmlFile = kmlFile;
            break;
        }
    }
    if (foundKmlFile != null) {
        foundKmlFile.unload();
    }
};

/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */

/**
 * A KML resource which can add and remove itself from the Google Earth plugin.
 */
function KmlFile(id, baseUrl, slug) {
    /**
     * Attributes
     */
    this.id = id;
    this.baseUrl = baseUrl;
    this.slug = slug;
    this.updateCounter = 0;
    this.kmlObject = null;
}

/**
 */
KmlFile.prototype.fullUrl = function() {
    if (this.slug === "jarkus")
        return this.baseUrl + '?' + jQuery.param(currentKmlParams);
    else
        return this.baseUrl;
};

/**
 */
KmlFile.prototype.load = function(doResetView) {
    // remove currently loaded features, if there are any
    this.unload();
    var kmlFile = this;
    var currentUpdateCount = ++this.updateCounter;
    google.earth.fetchKml(ge, this.fullUrl(), function(kmlObject) {
        kmlFile.finishedLoading(kmlObject, currentUpdateCount, doResetView);
    });
};

/**
 */
KmlFile.prototype.finishedLoading = function(kmlObject, currentUpdateCount, doResetView) {
    //if (this.updateCounter <= currentUpdateCount) {
        if (kmlObject) {
            // add new features
            this.kmlObject = kmlObject;
            ge.getFeatures().appendChild(kmlObject);
            // add click handlers
            if (this.slug === "jarkus") {
                addPlacemarkClickListeners(kmlObject);
            }
            // fly to view defined by KML, if desired
            if (doResetView && kmlObject.getAbstractView()) {
                ge.getView().setAbstractView(kmlObject.getAbstractView());
            }
        }
        else {
            console.log("failed to load KML data");
        }
    //}

    // re-enable controls anyway
    kvu.setControlsDisabled(false);
};

/**
 * Remove the KML data from the Google Earth plugin.
 */
KmlFile.prototype.unload = function() {
    if (this.kmlObject != null) {
        ge.getFeatures().removeChild(this.kmlObject);
        this.kmlObject = null;
    }
};

/**
 * Return a string representing this object.
 */
KmlFile.prototype.toString = function() {
    return 'KmlFile @ ' + this.fullUrl();
};

/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */

// ////////
// ////////
// ////////
// ////////
// TESTS
// ////////
// ////////
// ////////

function refreshNetworkLinks() {
    //var allNetworkLinks = ge.getElementsByType('KmlNetworkLink');
    var allNetworkLinks = ge.getLayerRoot().getElementsByType('KmlNetworkLink');
    var len = allNetworkLinks.getLength();
    alert(len);
    for (var i=0; i<len; i++) {
        var networkLink = allNetworkLinks.item(i);
        var link = networkLink.getLink();
        var oldHref = link.getHref();
        //var location = parseUrl(oldHref);
        //location.search = '?a=b';
        link.setHref(oldHref);
    }
}

function removewms() {
var features = ge.getFeatures();
while (features.getFirstChild())
features.removeChild(features.getFirstChild());
}

function addwms() {
var groundOverlay = ge.createGroundOverlay('');
groundOverlay.setIcon(ge.createIcon(''))
groundOverlay.getIcon().setHref("http://129.206.228.72/cached/osm?LAYERS=osm_auto:all&SRS=EPSG%3A900913&FORMAT=image%2Fpng&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&BBOX=313086.067,6574807.423,626172.1348,6887893.4908&WIDTH=256&HEIGHT=256");
groundOverlay.setLatLonBox(ge.createLatLonBox(''));

var center = ge.getView().copyAsLookAt(ge.ALTITUDE_RELATIVE_TO_GROUND);
var north = center.getLatitude();
var south = center.getLatitude();
var east = center.getLongitude();
var west = center.getLongitude();
var rotation = 0;

var latLonBox = groundOverlay.getLatLonBox();
latLonBox.setBox(north,south,east,west,rotation);
groundOverlay.getIcon().setViewRefreshMode(ge.VIEW_REFRESH_ON_STOP);
ge.getFeatures().appendChild(groundOverlay);
}
