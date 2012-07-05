// fix missing console logging
if (!window.console) window.console = {};
if (!window.console.log) window.console.log = function () { };

// load Google Earth plugin
google.load('earth', '1');

// configure Ext JS
var isExtReady = false;
Ext.BLANK_IMAGE_URL = '/static_media/lizard_kml/extjs-4.1.1-rc2/resources/themes/images/default/tree/s.gif';
Ext.form.Labelable.errorIconWidth = 16 // fix for Extjs bug
Ext.onReady(function () {
    console.log('Ext ready');
    isExtReady = true;
});
// Ext.scopeResetCSS = true;
// Ext.Loader.setConfig({
//     enabled : true
// });
// Ext.require('Ext.fx.Anim');
// Ext.require('Ext.data.Tree');
// Ext.require('Ext.tree.Panel');

// globals and constants
var geDownloadUrl = 'http://www.google.com/earth/explore/products/plugin.html';
var minimalPluginVersion = '6.2.0';
var ge = null;
var kvu = null;
var kfc = null;
var tsc = null;
var jarkusKmlParams = {
    lift:40.0,
    exaggeration:4.0,
    extrude:0,
    polyalpha:0.8,
    outline:0,
    move:0.1
};

// either the Google or Ext callbacks won't work properly, so
// solve it with this
function refreshLoadedModules() {
    if (document.readyState === 'complete' && isExtReady && google.earth) {
        clearInterval(loadInterval);
        console.log('All ready');
        kvu = new KmlViewerUi();
        kfc = new KmlFileCollection();
        // object for controlling the Google Earth time slider.
        tsc = new GETimeSliderControl();
        strc = new GEStreamingControl();
        kvu.init();
    }
}
var loadInterval = setInterval(refreshLoadedModules, 200);

// TEMP
function kmlViewerSetColormap(colormap) {
    jarkusKmlParams['colormap'] = colormap;
    $('#colormaps').dialog('close');
}
// TEMP
function addPlacemarkClickListeners(kmlObject) {
    var placemarks = kmlObject.getElementsByType('KmlPlacemark');
    for (var i = 0; i < placemarks.getLength(); ++i) {
        var placemark = placemarks.item(i);
        var url = '/kml/info/'+ placemark.getId() + '/';
        google.earth.addEventListener(placemark, 'click', function (event) {
            setDescription(event, url);
        });
    }
}
// TEMP
function setDescription(event, url) {
    var placemark = event.getTarget();
    $.get(url, {}, function (data) {
        placemark.setDescription(data)
    });
}

/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */
/* ************************************************************************ */

// Production steps of ECMA-262, Edition 5, 15.4.4.18
// Reference: http://es5.github.com/#x15.4.4.18
if ( !Array.prototype.forEach ) {

  Array.prototype.forEach = function( callback, thisArg ) {

    var T, k;

    if ( this == null ) {
      throw new TypeError( "this is null or not defined" );
    }

    // 1. Let O be the result of calling ToObject passing the |this| value as the argument.
    var O = Object(this);

    // 2. Let lenValue be the result of calling the Get internal method of O with the argument "length".
    // 3. Let len be ToUint32(lenValue).
    var len = O.length >>> 0; // Hack to convert O.length to a UInt32

    // 4. If IsCallable(callback) is false, throw a TypeError exception.
    // See: http://es5.github.com/#x9.11
    if ( {}.toString.call(callback) != "[object Function]" ) {
      throw new TypeError( callback + " is not a function" );
    }

    // 5. If thisArg was supplied, let T be thisArg; else let T be undefined.
    if ( thisArg ) {
      T = thisArg;
    }

    // 6. Let k be 0
    k = 0;

    // 7. Repeat, while k < len
    while( k < len ) {

      var kValue;

      // a. Let Pk be ToString(k).
      //   This is implicit for LHS operands of the in operator
      // b. Let kPresent be the result of calling the HasProperty internal method of O with argument Pk.
      //   This step can be combined with c
      // c. If kPresent is true, then
      if ( k in O ) {

        // i. Let kValue be the result of calling the Get internal method of O with argument Pk.
        kValue = O[ k ];

        // ii. Call the Call internal method of callback with T as the this value and
        // argument list containing kValue, k, and O.
        callback.call( T, kValue, k, O );
      }
      // d. Increase k by 1.
      k++;
    }
    // 8. return undefined
  };
}

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
 * Does what it says.
 */
function parseVersionString(str) {
    if (typeof(str) !== 'string') { return false; }
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
    if (running.major !== minimum.major)
        return (running.major > minimum.major);
    else {
        if (running.minor !== minimum.minor)
            return (running.minor > minimum.minor);
        else {
            if (running.patch !== minimum.patch)
                return (running.patch > minimum.patch);
            else
                return true;
        }
    }
}

/**
 * Returns two functions which convert values in the range of
 * [fmin, fmax] to the range [tmin, max] logarithmically.
 */
function buildLogaScaleFuncs(fmin, fmax, tmin, tmax) {
    // the result should be between min and max
    var minv = tmin == 0 ? 0 : Math.log(tmin);
    var maxv = Math.log(tmax);
    // calculate adjustment factor
    var scale = (maxv - minv) / (fmax - fmin);
    // build function
    var fwd = function(value) {
        return Math.exp(minv + scale * (value - fmin));
    };
    var rev = function(value) {
        return (Math.log(value) - minv) / scale + fmin;
    };
    return [fwd, rev];
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
    this.treeStore = null;
    this.treePanel = null;
    this.jarkusPanel = null;
    this.accordion = null;
}

/**
 * This method assumes the DOM is ready.
 */
KmlViewerUi.prototype.init = function () {
    // (lizard-ui) resize the ui
	setupLizardUi();
    // build the Ext.js controls
    this.initControls();
    // bind above-content links etc.
    this.bindUiEvents();
    // remove loading overlay
    // don't initialize Google Earth until after this is done 
    this.removeLoadingOverlay(this.initGoogleEarth.bind(this));
};

/**
 */
KmlViewerUi.prototype.bindUiEvents = function () {
    $('.kml-action-defaultview').click(function () {
        kvu.setDefaultView();
    });
    $('.kml-action-rewind').click(function () {
        tsc.rewind();
    });
    $('.kml-action-playpause').click(function () {
        tsc.togglePlayPause();
    });
};

/**
 * Initialize the main Google Earth plugin instance.
 */
KmlViewerUi.prototype.initGoogleEarth = function () {
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
                'en volg de instructies op, om deze te installeren. Herlaad vervolgens deze website, door deze opnieuw te bezoeken.'
            );
        }
        else {
            google.earth.createInstance('map3d', this.geInitCallback.bind(this), this.geFailureCallback.bind(this));
        }
    }
};

function buildSlider (args) {
    var defaultArgs = {
        animate: false,
        checkChangeBuffer: 100,
        checkChangeEvents: ['change'],
        listeners: {
            afterrender: function (c) {
                c.getEl().on('mouseenter', function () { this.fireEvent('mouseenter', c); }, c);
                c.getEl().on('mouseleave', function () { this.fireEvent('mouseleave', c); }, c);
            },
            mouseenter: function (slider) {
                slider.plugins[0].onSlide(slider, undefined, slider.thumbs[0]);
            },
            mouseleave: function (slider) {
                slider.plugins[0].hide();
            },
            change: function (slider, newValue, thumb, eOpts) {
                slider.plugins[0].onSlide(slider, undefined, slider.thumbs[0]);
            }
        }
    };

    args = Ext.merge(defaultArgs, args);

    var logarithmic = args['logarithmic'];
    if (logarithmic) {
        // delete our custom signaling flag
        delete args['logarithmic'];

        // build a function which can be used to calculate the logarithmic scale
        var min = args['minValue'];
        var max = args['maxValue'];
        var logaFuncs = buildLogaScaleFuncs(0, 100, min, max);
        var logaFuncFwd = logaFuncs[0];
        var logaFuncRev = logaFuncs[1];
        delete args['minValue']; // so this defaults to 0
        delete args['maxValue']; // so this defaults to 100

        // ensure snapping is disabled
        delete args['increment'];

        // set initial value, but be sure to reverse it (map to 0-100 range)
        args['value'] = logaFuncRev(args['value']);

        // set logarithmicValue on change
        args['listeners']['beforechange'] = function (slider, newValue, oldValue, eOpts) {
            slider.logarithmicValue = Ext.util.Format.round(logaFuncFwd(newValue), slider.decimalPrecision);
        };

        // replace tipText so it uses the logarithmicValue
        var oldTipText = args['tipText'];
        args['tipText'] = function (thumb) {
            return oldTipText({value: thumb.slider.logarithmicValue});
        };

        // see if a logarithmicOnChange event is defined
        var logarithmicOnChange = args['logarithmicOnChange'];
        if (logarithmicOnChange) {
            args['listeners']['change'] = function (slider, newValue, thumb, eOpts) {
                slider.plugins[0].onSlide(slider, undefined, slider.thumbs[0]);
                logarithmicOnChange(slider.logarithmicValue);
            };
            delete args['logarithmicOnChange'];
        }
    }

    var slider = Ext.create('Ext.slider.Single', args);
    if (logarithmic) {
        // calculate initial value
        slider.logarithmicValue = Ext.util.Format.round(logaFuncFwd(slider.getValue()), slider.decimalPrecision);
    }
    return slider;
}

/**
 * Build the ExtJS controls.
 */
KmlViewerUi.prototype.initControls = function () {
    // create a panel containing the preview and other
    // context-sensitive items
    var previewPanel = Ext.create('Ext.panel.Panel', {
        id: 'previewpanel',
        title: 'Voorbeeld',
        //collapsed: true,
        height: 190,
        html: '<div id="kml-preview-container"><img id="kml-preview" src="data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw%3D%3D" alt="preview" width="200" height="150" /></div>'
    });

    // build a model for tree nodes containing some extra kml data
    Ext.define('KmlResourceNode', {
        extend: 'Ext.data.Model',
        fields: ['kml_id', 'text', 'description', 'kml_url', 'slug', 'preview_image_url']
    });
    Ext.data.NodeInterface.decorate(KmlResourceNode);

    // create a store for adapting the json output
    this.treeStore = Ext.create('Ext.data.TreeStore', {
        listeners: {
            single: true,
            load: function (thisStore, rootNode, records, successful, eOpts){
                var categories = thisStore.proxy.reader.rawData.categories;
                categories.forEach(function (category) {
                    var categoryNode = rootNode.appendChild({
                        text: category.name,
                        expanded: true,
                        leaf: false
                    });
                    category.kml_resources.forEach(function (k) {
                        var krn = new KmlResourceNode({
                            kml_id: k.id,
                            text: k.name,
                            description: k.description,
                            leaf: true,
                            checked: false,
                            kml_url: k.kml_url,
                            slug: k.slug,
                            preview_image_url: k.preview_image_url
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

    var contextMenu = new Ext.menu.Menu({
        animCollapse: false,
        items: [
            {
                text: 'Zoom',
                iconCls: 'icon-zoom-in',
                handler: function (thisItem, event) {
                    var id = thisItem.parentMenu.node.get('kml_id');
                    var kmlFile = kfc.get(id);
                    if (kmlFile)
                        kmlFile.zoomToExtent();
                }
            },
        ]
    });

    // create the tree panel (and view)
    this.treePanel = Ext.create('Ext.tree.Panel', {
        title: 'Kaartlagen',
        store: this.treeStore,
        rootVisible: false,
        plain: false,
        multiSelect: false,
        animate: false,
        useArrows: true,
        lines: false,
        stateful: false,
        border: false,
        listeners: {
            itemclick: function (thisView, node, item, index, event, eOpts) {
                if (!node.isLeaf()) {
                    // user clicked on a category, collapse / expand it
                    if (node.isExpanded()) {
                        node.collapse();
                    }
                    else {
                        node.expand();
                    }
                }
                else {
                    if (node instanceof KmlResourceNode) {
                        // user clicked on a 'leaf' node, set the checkbox
                        var checked = !(node.get('checked'));
                        node.set('checked', checked);
                        // enable jarkus panel if use activated that
                        if (node.get('slug') === 'jarkus') {
                            kvu.setJarkusPanelEnabled(checked);
                        }
                        kfc.fireUpdate();
                    }
                }
            },
            // checkchange: function (node, checked, eOpts) {
            // },
            itemmouseenter: function (thisView, node, item, index, event, eOpts) {
                if (node instanceof KmlResourceNode) {
                    kvu.showPreviewImage(node.get('preview_image_url'));
                }
            },
            itemmouseleave: function (thisView, node, item, index, event, eOpts) {
                if (node instanceof KmlResourceNode) {
                    kvu.hidePreviewImage();
                }
            },
            /*
            mouseenter: {
                element: 'el',
                fn: function (thisView, event, eOpts) {
                    previewPanel.expand();
                }
            },
            mouseleave: {
                element: 'el',
                fn: function (thisView, event, eOpts) {
                    previewPanel.collapse();
                }
            },
            */
            itemcontextmenu: function (thisView, node, item, index, event) {
                if (node instanceof KmlResourceNode) {
                    contextMenu.node = node;
                    contextMenu.showAt(event.getXY());
                    event.stopEvent();
                }
            }
        }
    });

    // create the Jarkus controls
    this.initJarkusPanel();

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
            this.jarkusPanel,
            previewPanel
        ],
        renderTo: Ext.get('ext-left-controls')
    });

    // create a slider for controlling the play speed
    var playRate = buildSlider({
        fieldLabel: 'Afspeelsnelheid',
        width: 300,
        minValue: 0.5,
        maxValue: 10.0,
        value: 5.0,
        decimalPrecision: 1,
        tipText: function (thumb) {
            return Ext.String.format('{0} jaar per seconde', thumb.value);
        },
        logarithmic: true,
        logarithmicOnChange: function (newValue) {
            tsc.setRate(newValue);
        },
        renderTo: Ext.get('ext-play-rate-slider')
    });
};

/**
 */
KmlViewerUi.prototype.initJarkusPanel = function () {
    // build colormaps dialog
    $("#colormaps").dialog({
        title: 'Selecteer kleurenmap',
        autoOpen: false,
        height: 362,
        width: 216,
        position: 'left middle',
        zIndex: 10005 // above slider thumbs
    });

    var lift = buildSlider({
        fieldLabel: 'Ophoging',
        minValue: 0.0,
        maxValue: 200.0,
        value: 40.0,
        decimalPrecision: 1,
        tipText: function (thumb) {
            return Ext.String.format('{0} meter', thumb.value);
        },
        logarithmic: true
    });
    lift.on('mouseenter', this.showPreviewImage.bind(this, '/static_media/lizard_kml/ophoging.gif'));
    lift.on('mouseleave', this.hidePreviewImage.bind(this));

    var exaggeration = buildSlider({
        fieldLabel: 'Opschaling',
        minValue: 1.0,
        maxValue: 50.0,
        value: 4.0,
        decimalPrecision: 1,
        tipText: function (thumb) {
            return Ext.String.format('{0} meter', thumb.value);
        },
        logarithmic: true
    });
    exaggeration.on('mouseenter', this.showPreviewImage.bind(this, '/static_media/lizard_kml/opschaling.gif'));
    exaggeration.on('mouseleave', this.hidePreviewImage.bind(this));

    var extrude = Ext.create('Ext.form.field.Checkbox', {
        fieldLabel: 'Uitvullen',
        boxLabel: 'Ja',
        listeners: {
            afterrender: function (c) {
                c.getEl().on('mouseenter', function () { this.fireEvent('mouseenter', c); }, c);
                c.getEl().on('mouseleave', function () { this.fireEvent('mouseleave', c); }, c);
            }
        }
    });
    extrude.on('mouseenter', this.showPreviewImage.bind(this, '/static_media/lizard_kml/uitvullen.png'));
    extrude.on('mouseleave', this.hidePreviewImage.bind(this));

    var colormaps = Ext.create('Ext.button.Button', {
        text: 'Kleurenmap',
        handler: function() {
            $("#colormaps").dialog("open");
        }
    });

    var polyalpha = buildSlider({
        fieldLabel: 'Transparantie',
        increment: 0.1,
        minValue: 0.0,
        maxValue: 1.0,
        value: 0.8,
        decimalPrecision: 1,
        tipText: function (thumb) {
            return Ext.String.format('{0}%', thumb.value * 100);
        }
    });

    var move = buildSlider({
        fieldLabel: 'Verschuiving',
        increment: 0.1,
        minValue: 0.0,
        maxValue: 2.0,
        value: 0.1,
        decimalPrecision: 1,
        tipText: function (thumb) {
            return Ext.String.format('{0}m', thumb.value);
        }
    });
    move.on('mouseenter', this.showPreviewImage.bind(this, '/static_media/lizard_kml/verschuiving.png'));
    move.on('mouseleave', this.hidePreviewImage.bind(this));

    var confirm = Ext.create('Ext.button.Button', {
        text: 'Wijzig weergave',
        handler: function() {
            jarkusKmlParams['lift'] = lift.logarithmicValue;
            jarkusKmlParams['exaggeration'] = exaggeration.logarithmicValue;
            jarkusKmlParams['extrude'] = extrude.getValue() ? 1 : 0;
            jarkusKmlParams['polyalpha'] = polyalpha.getValue();
            jarkusKmlParams['move'] = move.getValue();
            kfc.reloadAllDynamic();
        }
    });

    var multiselect = Ext.create('Ext.button.Button', {
        text: 'Grafiek over meerdere raaien',
        handler: function() {
            kvu.startMultiSelect();
        }
    });

    var actions = Ext.create('Ext.form.FieldSet', {
        title: 'Acties',
        defaults: {anchor: '100%'},
        layout: {
            type: 'anchor',
            align: 'stretch'
        },
        items: [
            multiselect
        ]
    });

    var display = Ext.create('Ext.form.FieldSet', {
        title: 'Weergave',
        defaults: {anchor: '100%'},
        layout: {
            type: 'anchor',
            align: 'stretch'
            //padding: 5
        },
        items: [
            lift,
            exaggeration,
            extrude,
            colormaps,
            polyalpha,
            move,
            confirm
        ]
    });

    this.jarkusPanel = Ext.create('Ext.panel.Panel', {
        title: 'Jarkus',
        collapsed: true,
        disabled: true,
        layout: {
            type: 'vbox',
            align: 'stretch'
            //padding: 5
        },
        items: [
            display,
            actions
        ]
    });
};

/**
 */
KmlViewerUi.prototype.showPreviewImage = function (url) {
    var $preview = $('#kml-preview');
    $preview.load(function() {
        // only continue if the users mouse is still on the element
        // for which the preview is shown
        if ($(this).attr('src') == url) {
            $('#kml-preview-container').show();
        }
    });
    $preview.attr('src', url);
};

/**
 */
KmlViewerUi.prototype.hidePreviewImage = function () {
    $('#kml-preview-container').hide();
};

/**
 */
KmlViewerUi.prototype.setJarkusPanelEnabled = function (enabled) {
    this.jarkusPanel.setDisabled(!enabled);
    if (enabled)
        this.jarkusPanel.expand();
    else
        this.jarkusPanel.collapse();
};

/**
 * Get an associative array of some data in the treenodes which are checked.
 */
KmlViewerUi.prototype.getChecked = function () {
    var checked = {};
    this.treePanel.getChecked().forEach(function (node) {
        var kml_id = node.get('kml_id');
        checked[kml_id] = {
            id: kml_id,
            url: node.get('kml_url'),
            slug: node.get('slug')
        };
    });
    return checked;
};

/**
 * Test the treenode belonging to an kml_id is checked.
 */
KmlViewerUi.prototype.isChecked = function (id) {
    var found = false;
    this.treePanel.getChecked().forEach(function (node) {
        var kml_id = node.get('kml_id');
        if (id === kml_id) {
            found = true;
            return false; // NOTE: this exits the forEach loop
        }
    });
    return found;
};

/**
 * Disable (make gray') all UI controls.
 */
KmlViewerUi.prototype.setControlsDisabled = function (disabled) {
    this.accordion.setDisabled(disabled);
};

/**
 * Fade out the overlay. Passed callback is called when the fade is finished.
 */
KmlViewerUi.prototype.removeLoadingOverlay = function (callback) {
    var loader = Ext.get('loader');
    loader.fadeOut({
        delay: 500,
        duration: 500,
        remove: true,
        callback: callback
    });
};

/**
 * Called by the Google Earth plugin 
 */
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

        // enable nav control
        ge.getNavigationControl().setVisibility(ge.VISIBILITY_AUTO);

        // enable the atmosphere
        ge.getOptions().setAtmosphereVisibility(true);
    
        // make the plugin visible
        ge.getWindow().setVisibility(true);
    
        // fly to default view once, on init
        this.setDefaultView();
    
        // start timeslider control
        tsc.startControl();

        // start streaming pct checker
        strc.startControl();

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
    if ($el.length !== 0) {
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

KmlViewerUi.prototype.setPlaying = function (playing) {
    if (playing) {
        $(".kml-action-playpause").addClass("icon-pause");
        $(".kml-action-playpause").removeClass("icon-play");
    }
    else {
        $(".kml-action-playpause").removeClass("icon-pause");
        $(".kml-action-playpause").addClass("icon-play");
    }
};

KmlViewerUi.prototype.setNodeLoading = function (id, loading) {
    this.treePanel.getRootNode().cascadeBy(function (node) {
        var kml_id = node.get('kml_id');
        if (id === kml_id) {
            node.set('loading', loading);
            return false; // NOTE: this exits the forEach loop
        }
    });
};

KmlViewerUi.prototype.startMultiSelect = function () {
    var kmlObject = kfc.getBySlug('jarkus').kmlObject;
    var placemarks = kmlObject.getElementsByType('KmlPlacemark');
    var len = placemarks.getLength();

    google.earth.executeBatch(ge, function () {
        for (var i = 0; i < len; ++i) {
            var placemark = placemarks.item(i);
            google.earth.addEventListener(placemark, 'click', function (event) {
                var clickItem = event.getTarget();
                console.log(clickItem.getId());

                var balloon = ge.createHtmlStringBalloon('');
                balloon.setMaxWidth(600);
                balloon.setContentString('<a href="#" onclick="alert(\'Running some JavaScript!\');">Alert!</a>');
                ge.setBalloon(balloon);

                event.preventDefault();
            });
        }
    });
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
    this.secondsInYear = 60 * 60 * 24 * 365; // amount of seconds in a year
    this.realSecondsPerDataYear = 5.0;
    this.isPlaying = false; // keep our own playing / stopped state
    this.animationStopInterval = null;
}

GETimeSliderControl.prototype.startControl = function () {
    this.animationStopInterval = window.setInterval(this.animationStopTick.bind(this), 1000);
};

GETimeSliderControl.prototype.togglePlayPause = function () {
    // true if an animation is playing without us having
    // initiated it
    var isPlayingExternal = ge.getTime().getRate() > 0;
    if (this.isPlaying || isPlayingExternal) {
        // pause
        this.pause();
    }
    else {
        // play
        if (this.isPastEnd()) {
            // at end, so rewind first
            this.rewind();
        }
        this.play();
    }
};

GETimeSliderControl.prototype.rewind = function () {
    this.pause();
    this.setCurrentTime(this.getExtentBegin());
};

GETimeSliderControl.prototype.setRate = function (rate) {
    this.realSecondsPerDataYear = rate;
    if (this.isPlaying) {
        // 'live' update the speed when playing
        ge.getTime().setRate(this.secondsInYear * this.realSecondsPerDataYear);
    }
};

GETimeSliderControl.prototype.play = function () {
    this.isPlaying = true;
    kvu.setPlaying(true);
    ge.getTime().setRate(this.secondsInYear * this.realSecondsPerDataYear);
};

GETimeSliderControl.prototype.pause = function () {
    ge.getTime().setRate(0);
    this.isPlaying = false;
    kvu.setPlaying(false);
};

GETimeSliderControl.prototype.animationStopTick = function () {
    if (this.isPlaying) {
        if (ge.getTime().getRate() == 0) {
            // playback has been stopped by some other means,
            // like the timeslider
            this.isPlaying = false;
            kvu.setPlaying(false);
        }
        else if (this.isPastEnd()) {
            // FIX for Google bug: stop playing past extents
            // we are past the extents, pause the animation
            this.pause();
            // revert time to the end of the extents
            this.setCurrentTime(this.getExtentEnd());
        }
    }
};

GETimeSliderControl.prototype.getExtentBegin = function () {
    var extents = ge.getTime().getControl().getExtents();
    return extents.getBegin().get();
};

GETimeSliderControl.prototype.getExtentEnd = function () {
    var extents = ge.getTime().getControl().getExtents();
    return extents.getEnd().get();
};

GETimeSliderControl.prototype.isPastEnd = function () {
    return this.getCurrentTimeEnd() >= this.getExtentEnd();
};

GETimeSliderControl.prototype.getCurrentTimeEnd = function () {
    var currentTime = ge.getTime().getTimePrimitive();
    var currentTimeEnd;
    if (currentTime.getType() === 'KmlTimeSpan') {
        currentTimeEnd = currentTime.getEnd().get();
    } else {
        currentTimeEnd = currentTime.getWhen().get();
    }
    return currentTimeEnd;
};

GETimeSliderControl.prototype.setCurrentTime = function (time) {
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
 * Google Earth streaming percentage listener.
 */
function GEStreamingControl() {
    this.$el = $('#kml-stream-percentage');
    this.$number = $('#kml-stream-percentage .number');
    this.interval = null;
}

GEStreamingControl.prototype.startControl = function () {
    this.interval = window.setInterval(this.tick.bind(this), 500);
};

GEStreamingControl.prototype.tick = function () {
    var pct = ge.getStreamingPercent();
    if (pct != 0) {
        this.$number.html(pct);
        if (pct == 100) {
            this.$el.addClass('ready');
        }
        else {
            this.$el.removeClass('ready');
        }
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
 * Manages the collection of KML files loaded in the viewer.
 */
function KmlFileCollection() {
    /**
     * Array of KmlFile objects, maps id to object.
     */
    this.kmlFiles = {};
    /**
     * True while an update is happening.
     */
    this.updateTimeout = null;
}

/**
 * Ensure that an update of the loaded KML files happens somewhere in the near future.
 */
KmlFileCollection.prototype.fireUpdate = function () {
    // stop the old timeout
    if (this.updateTimeout !== null) {
        clearTimeout(this.updateTimeout);
    }

    // set a new one
    this.updateTimeout = setTimeout(this.update.bind(this), 300);
};

/**
 * Refreshes the loaded Kml files based on the state of the checkboxes in the
 * checkbox tree.
 */
KmlFileCollection.prototype.update = function () {
    // reset the timeout
    this.updateTimeout = null;

    // get a assoc. array of checked items
    var checked = kvu.getChecked();

    // unload nonchecked kml files
    for (var i in this.kmlFiles) {
        var kmlFile = this.kmlFiles[i];
        if (!(kmlFile.id in checked)) {
            kmlFile.unload();
            delete this.kmlFiles[kmlFile.id];
        }
    }

    // load all checked kml files
    for (var i in checked) {
        var item = checked[i];
        if (!(item.id in this.kmlFiles)) {
            this.startLoadingKmlFile(item.id, item.url, item.slug);
        }
    }
};

/**
 * Create a new KmlFile entry and try loading it in the Google Earth plugin.
 */
KmlFileCollection.prototype.startLoadingKmlFile = function (id, url, slug) {
    var k = new KmlFile(id, url, slug);
    this.kmlFiles[id] = k;
    k.load(function () {
        return kvu.isChecked(id);
    });
};

/**
 * Call this when params (lift, exaggeration etc) change.
 */
KmlFileCollection.prototype.reloadAllDynamic = function () {
    for (var i in this.kmlFiles) {
        var kmlFile = this.kmlFiles[i];
        if (kmlFile.slug === "jarkus" && kmlFile.kmlObject !== null) {
            kmlFile.unload();
            kmlFile.load();
        }
    }
};

/**
 */
KmlFileCollection.prototype.get = function (id) {
    for (var i in this.kmlFiles) {
        var kmlFile = this.kmlFiles[i];
        if (kmlFile.id === id) {
            return kmlFile;
        }
    }
};

/**
 */
KmlFileCollection.prototype.getBySlug = function (slug) {
    for (var i in this.kmlFiles) {
        var kmlFile = this.kmlFiles[i];
        if (kmlFile.slug === slug) {
            return kmlFile;
        }
    }
};

/**
 * Remove all loaded KML files.
 */
KmlFileCollection.prototype.unloadAll = function () {
    for (var i in this.kmlFiles) {
        var kmlFile = this.kmlFiles[i];
        kmlFile.unload();
    }
    this.kmlFiles.length = 0; // clear a JavaScript list (this is no joke)
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
    this.id = id;
    this.baseUrl = baseUrl;
    this.slug = slug;
    this.kmlObject = null;
}

/**
 * Get the url for this KML file.
 */
KmlFile.prototype.fullUrl = function () {
    if (this.slug === "jarkus")
        return this.baseUrl + '?' + jQuery.param(jarkusKmlParams);
    else
        return this.baseUrl;
};

/**
 * Ask Google Earth to fetch the KML and convert it to an object.
 * Ensures beforeAddCallback is called before actually adding the object,
 * based on its return value.
 */
KmlFile.prototype.load = function (beforeAddCallback) {
    var self = this;
    console.log("loading " + this);
    kvu.setNodeLoading(this.id, true);
    google.earth.fetchKml(ge, this.fullUrl(), function (kmlObject) {
        self.finishedLoading(kmlObject, beforeAddCallback);
    });
};

/**
 * Add a object to the Google Earth features.
 * Ensures beforeAddCallback is called before actually adding the object,
 * based on its return value.
 */
KmlFile.prototype.finishedLoading = function (kmlObject, beforeAddCallback) {
    if (kmlObject) {
        console.log("loaded " + this);
        // check if the KML is still needed
        var doContinue = true;
        if (beforeAddCallback !== undefined) {
            doContinue = beforeAddCallback();
        }
        if (doContinue) { 
            // add new features
            this.kmlObject = kmlObject;
            ge.getFeatures().appendChild(kmlObject);
            // add click handlers
            if (this.slug === "jarkus") {
                //addPlacemarkClickListeners(kmlObject);
            }
        }
        else {
            console.log("load canceled");
        }
    }
    else {
        console.log("failed to load " + this);
    }
    kvu.setNodeLoading(this.id, false);
};

/**
 * Remove the KML data from the Google Earth plugin.
 */
KmlFile.prototype.unload = function () {
    if (this.kmlObject !== null) {
        ge.getFeatures().removeChild(this.kmlObject);
        this.kmlObject = null;
    }
};

/**
 * Zoom to extent if KML file has one defined.
 */
KmlFile.prototype.zoomToExtent = function () {
    var view = this.kmlObject.getAbstractView();
    if (view) {
        ge.getView().setAbstractView(view);
    }
};

/**
 * Return a string representing this object.
 */
KmlFile.prototype.toString = function () {
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
