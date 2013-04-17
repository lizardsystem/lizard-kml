(function (global) {
// Fix missing console logging on browsers like IE.
if (!window.console) window.console = {};
if (!window.console.log) window.console.log = function () { };

// Load the Google Earth plugin API.
google.load('earth', '1');

// Set up Ext JS.
var isExtReady = false;
Ext.BLANK_IMAGE_URL = window.lizard_settings.static_url + '/lizard_kml/extjs-4.2.0/resources/themes/images/default/tree/s.gif';
// Fix an Ext JS bug.
Ext.form.Labelable.errorIconWidth = 16;
Ext.onReady(function () {
    console.log('Ext JS is ready');
    isExtReady = true;
});

// Set up jQuery.
// Disable all animations.
$.fx.off = true;

// Define some semi-configurable globals and constants.
var geDownloadUrl = 'http://www.google.com/earth/explore/products/plugin.html';
var minimalPluginVersion = '6.0.0';
var ge = null;
var kvu = null;
var kfc = null;
var jarkusKmlParams = {
    lift: 40.0,
    exaggeration: 4.0,
    extrude: 0,
    polyalpha: 0.8,
    outline: 0,
    move: 0.1
};
var chartParams = {
    year_from: 1920,
    year_to: 2020
};
var emptyGif = 'data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw%3D%3D';

// Either the Google Earth API, or Ext JS callbacks which are supposed to notify
// everything has been loaded won't work properly, so solve it by polling
// for readyness.
function refreshLoadedModules() {
    if (document.readyState === 'complete' && isExtReady && google.earth) {
        clearInterval(loadInterval);
        console.log('All ready');
        kfc = new KmlFileCollection();
        kvu = new KmlViewerUi(kfc);
        kvu.init();
    }
}
var loadInterval = setInterval(refreshLoadedModules, 200);

// This is still referenced in a Django template fragment (via an <a href="javascript:">).
// This should be refactored to dynamicly load the popup content.
window.kmlViewerSetColormap = function (colormap) {
    jarkusKmlParams.colormap = colormap;
    $('#colormaps').dialog('close');
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
 * Snippet to make old browsers compatible with the new Array.forEach helper.
 * Production steps of ECMA-262, Edition 5, 15.4.4.18
 * Reference: http://es5.github.com/#x15.4.4.18
 */
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
 * Snippet for browsers not supporting Function.bind:
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
 * Parse a version string like "6.3.2" to integers, so different
 * version can be compared.
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
 * Returns true when version string "vcurrent" is higher or equal to
 * version "vmin".
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
    // build functions
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
 * Class which holds all UI components and view state.
 */
function KmlViewerUi(kfc) {
    this.kfc = kfc;

    // components
    this.treeStore = null;
    this.treePanel = null;
    this.jarkusPanel = null;
    this.accordion = null;

    this.tsc = null;
    this.strc = null;

    // etc
    this.previewImageUrl = emptyGif;

    // for multiselection
    this.isMultiSelectEnabled = false;
    this.selectedItems = [];
}

/**
 * Add the UI components to the DOM. This method assumes the DOM is ready.
 */
KmlViewerUi.prototype.init = function () {
    // Object for controlling the Google Earth time slider.
    this.tsc = new GETimeSliderControl();
    // Object for reading the streaming percentage status of Google Earth.
    this.strc = new GEStreamingControl();
    // Resize the ui to its proper sizes (lizard-ui legacy).
	setupLizardUi();
    // Build the Ext JS controls.
    this.initControls();
    // Bind above-content links like play/pause et cetera.
    this.bindUiEvents();
    // Initialize the small preview image in the lower-left area.
    this.initPreviewImage();
    // All ready, remove the loading overlay.
    // Don't initialize Google Earth, until after this is done.
    this.removeLoadingOverlay(this.initGoogleEarth.bind(this));
};

/**
 * Bind the click handlers of the three play/pause buttons on top.
 */
KmlViewerUi.prototype.bindUiEvents = function () {
    var self = this;

    $('.kml-action-defaultview').click(function () {
        self.setDefaultView();
    });
    $('.kml-action-rewind').click(function () {
        self.tsc.rewind();
    });
    $('.kml-action-playpause').click(function () {
        self.tsc.togglePlayPause();
    });
};

/**
 * Initialize the Google Earth plugin instance.
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

/**
 * Shorthand for Ext.create('Ext.slider.Single', args), which sets some sane defaults
 * and adds support for a logarithmic scale.
 */
function buildSlider (args) {
    // Define some sane defaults:
    // - disable animation for performance
    // - show/hide tips when entering/leaving the slider control
    // - immediate show, move and update tip when slider value is changed
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
                this.fireEvent('mychange', slider, newValue, thumb, eOpts);
            }
        }
    };

    // Merge with passed arguments, which always take preference.
    args = Ext.merge(defaultArgs, args);

    // Add some extra event handlers when the slider has a logarithmic scale.
    var logarithmic = args['logarithmic'];
    if (logarithmic) {
        // Delete our custom attribute.
        delete args['logarithmic'];

        // Build a function which can be used to calculate the logarithmic scale.
        var min = args['minValue'];
        var max = args['maxValue'];
        var logaFuncs = buildLogaScaleFuncs(0, 100, min, max);
        var logaFuncFwd = logaFuncs[0];
        var logaFuncRev = logaFuncs[1];
        delete args['minValue']; // so this defaults to 0
        delete args['maxValue']; // so this defaults to 100

        // Ensure value snapping is disabled.
        delete args['increment'];

        // Set initial value, but be sure to reverse it (map to 0-100 range).
        args['value'] = logaFuncRev(args['value']);

        // Set logarithmicValue, when slider is dragged.
        args['listeners']['beforechange'] = function (slider, newValue, oldValue, eOpts) {
            slider.logarithmicValue = Ext.util.Format.round(logaFuncFwd(newValue), slider.decimalPrecision);
        };

        // Replace tipText, so it uses the logarithmicValue.
        var oldTipText = args['tipText'];
        args['tipText'] = function (thumb) {
            return oldTipText({value: thumb.slider.logarithmicValue});
        };

        // See if a logarithmicOnChange event listener is defined.
        // If it is, make sure to pass the it the new value.
        var logarithmicOnChange = args['logarithmicOnChange'];
        if (logarithmicOnChange) {
            args['listeners']['change'] = function (slider, newValue, thumb, eOpts) {
                slider.plugins[0].onSlide(slider, undefined, slider.thumbs[0]);
                logarithmicOnChange(slider.logarithmicValue);
            };
            delete args['logarithmicOnChange'];
        }
    }

    // Build the actual slider with our new args.
    var slider = Ext.create('Ext.slider.Single', args);

    // Calculate the initial value.
    if (logarithmic) {
        slider.logarithmicValue = Ext.util.Format.round(logaFuncFwd(slider.getValue()), slider.decimalPrecision);
    }

    return slider;
}

/**
 * Shorthand for Ext.create('Ext.slider.Multi', args), which fixes things
 * regarding the tooltips.
 */
function buildMultiTipSlider (args) {
    // Manually instanciate the Tip plugins.
    // ExtJS 4.2.0 properly deals with this ("hasTip").
    var thumbCount = args.values.length;
    var plugins = [];
    for (var i=0; i<thumbCount; i++) {
        var plugin = new Ext.slider.Tip(args.tipText ? {getText: args.tipText} : {});
        plugins.push(plugin);
    }

    // Define some sane defaults:
    // - disable animation for performance
    // - show/hide tips when entering/leaving the slider control
    // - immediate show, move and update tip when slider value is changed
    var defaultArgs = {
        animate: false,
        checkChangeBuffer: 100,
        checkChangeEvents: ['change'],
        plugins: plugins,
        listeners: {
            afterrender: function (c) {
                // We need to attach to the actual DOM element, after the control has been rendered.
                this.onMyMouseEnter = function () { this.fireEvent('mymouseenter', c); };
                this.onMyMouseLeave = function () { this.fireEvent('mymouseleave', c); };
                c.getEl().on('mouseenter', this.onMyMouseEnter, c);
                c.getEl().on('mouseleave', this.onMyMouseLeave, c);
            },
            mymouseenter: function (slider) {
                for (var i=0; i<slider.plugins.length; i++) {
                    slider.plugins[i].onSlide(slider, undefined, slider.thumbs[i]);
                }
            },
            mymouseleave: function (slider) {
                for (var i=0; i<slider.plugins.length; i++) {
                    slider.plugins[i].hide();
                }
            },
            change: function (slider, newValue, thumb, eOpts) {
                var pluginIndex = slider.thumbs.indexOf(thumb);
                if (pluginIndex !== -1) {
                    slider.plugins[pluginIndex].onSlide(slider, undefined, thumb);
                }
                this.fireEvent('mychange', slider, newValue, thumb, eOpts);
            },
            destroy: function (c) {
                c.getEl().un('mouseenter', this.onMyMouseEnter, c);
                c.getEl().un('mouseleave', this.onMyMouseLeave, c);
            }
        }
    };

    // Update default args with passed args.
    args = Ext.merge(defaultArgs, args);

    // Instanciate the actual slider.
    var slider = Ext.create('Ext.slider.Multi', args);

    // Remove original event handlers, which don't deal with multiple tips.
    for (var i=0; i<slider.plugins.length; i++) {
        var plugin = slider.plugins[i];
        slider.un({
            scope    : plugin,
            dragstart: plugin.onSlide,
            drag     : plugin.onSlide,
            dragend  : plugin.hide
        });
    }

    // Return the slider instance for later customisation.
    return slider;
}

/**
 * Build the ExtJS controls.
 */
KmlViewerUi.prototype.initControls = function () {
    var self = this;

    // create a panel containing the preview image, and other
    // context-sensitive items
    var previewPanel = Ext.create('Ext.panel.Panel', {
        id: 'previewpanel',
        title: 'Voorbeeld',
        height: 190,
        html: '<div id="kml-preview-container"><img id="kml-preview" src="' + emptyGif + '" alt="preview" width="200" height="150" /></div>'
    });

    // build a model for tree nodes containing some extra kml data
    Ext.define('KmlResourceNode', {
        extend: 'Ext.data.Model',
        fields: ['kml_id', 'text', 'description', 'kml_url', 'slug', 'preview_image_url']
    });
    Ext.data.NodeInterface.decorate(KmlResourceNode);

    // create a store for adapting the json output to KmlResourceNode instances
    this.treeStore = Ext.create('Ext.data.TreeStore', {
        listeners: {
            single: true,
            load: function (thisStore, rootNode, records, successful, eOpts){
                var categories = thisStore.proxy.reader.rawData.categories;
                categories.forEach(function (category) {
                    var categoryNode = rootNode.appendChild({
                        text: category.name,
                        expanded: !category.collapsed_by_default,
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
            url: window.lizard_settings.lizard_kml.api_url + '?format=json',
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
                    var kmlFile = self.kfc.get(id);
                    if (kmlFile) {
                        kmlFile.zoomToExtent();
                    }
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
                        self.kfc.fireUpdate();
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
            bodyStyle: 'padding:2px'
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
            self.tsc.setRate(newValue);
        },
        renderTo: Ext.get('ext-play-rate-slider')
    });

    // create a slider for controlling the yearspan
    // used for drawing charts
    var yearSpan = buildMultiTipSlider({
        fieldLabel: 'Jaarspanne grafieken',
        labelWidth: 120,
        width: 400,
        minValue: 1840,
        maxValue: 2020,
        increment: 1,
        values: [chartParams.year_from, chartParams.year_to],
        tipText: function (thumb) {
            return Ext.String.format('{0}', thumb.value);
        },
        listeners: {
            mychange: function (slider, newValue, thumb, eOpts) {
                var idx = slider.thumbs.indexOf(thumb);
                if (idx === 0) {
                    chartParams.year_from = newValue;
                }
                else if (idx === 1) {
                    chartParams.year_to = newValue;
                }
            }
        },
        renderTo: Ext.get('ext-year-span-slider')
    });
};

/**
 */
KmlViewerUi.prototype.initJarkusPanel = function () {
    var self = this;

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
        value: jarkusKmlParams.lift,
        decimalPrecision: 1,
        tipText: function (thumb) {
            return Ext.String.format('{0} meter', thumb.value);
        },
        logarithmic: true
    });
    lift.on(
        'mouseenter',
        this.showPreviewImage.bind(this, window.lizard_settings.static_url + '/lizard_kml/ophoging.gif')
    );
    lift.on('mouseleave', this.hidePreviewImage.bind(this));

    var exaggeration = buildSlider({
        fieldLabel: 'Opschaling',
        minValue: 1.0,
        maxValue: 50.0,
        value: jarkusKmlParams.exaggeration,
        decimalPrecision: 1,
        tipText: function (thumb) {
            return Ext.String.format('{0} meter', thumb.value);
        },
        logarithmic: true
    });
    exaggeration.on('mouseenter', this.showPreviewImage.bind(
        this,
        window.lizard_settings.static_url + '/lizard_kml/opschaling.gif'
    ));
    exaggeration.on('mouseleave', this.hidePreviewImage.bind(this));

    var extrude = Ext.create('Ext.form.field.Checkbox', {
        fieldLabel: 'Uitvullen',
        boxLabel: 'Ja',
        checked: jarkusKmlParams.extrude == 1,
        listeners: {
            afterrender: function (c) {
                c.getEl().on('mouseenter', function () { this.fireEvent('mouseenter', c); }, c);
                c.getEl().on('mouseleave', function () { this.fireEvent('mouseleave', c); }, c);
            }
        }
    });
    extrude.on('mouseenter', this.showPreviewImage.bind(
        this,
        window.lizard_settings.static_url + '/lizard_kml/uitvullen.png'
    ));
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
        value: jarkusKmlParams.polyalpha,
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
        value: jarkusKmlParams.move,
        decimalPrecision: 1,
        tipText: function (thumb) {
            return Ext.String.format('{0}m', thumb.value);
        }
    });
    move.on('mouseenter', this.showPreviewImage.bind(
        this,
        window.lizard_settings.static_url + '/lizard_kml/verschuiving.png'
    ));
    move.on('mouseleave', this.hidePreviewImage.bind(this));

    var confirm = Ext.create('Ext.button.Button', {
        text: 'Wijzig weergave',
        handler: function() {
            jarkusKmlParams.lift = lift.logarithmicValue;
            jarkusKmlParams.exaggeration = exaggeration.logarithmicValue;
            jarkusKmlParams.extrude = extrude.getValue() ? 1 : 0;
            jarkusKmlParams.polyalpha = polyalpha.getValue();
            jarkusKmlParams.move = move.getValue();
            self.kfc.reloadAllDynamic();
        }
    });

    var multiselect = Ext.create('Ext.button.Button', {
        text: 'Grafiek over meerdere raaien',
        handler: function() {
            self.toggleMultiSelect();
        }
    });

    var actions = Ext.create('Ext.form.FieldSet', {
        title: 'Acties',
        defaults: {
            anchor: '100%'
        },
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
        defaults: {
            anchor: '100%'
        },
        layout: {
            type: 'anchor',
            align: 'stretch'
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
        },
        items: [
            display,
            actions
        ]
    });
};

/**
 * Attach loading event to the preview image.
 */
KmlViewerUi.prototype.initPreviewImage = function () {
    var self = this;
    $('#kml-preview').load(function() {
        // only continue if the users mouse is still on the element
        // for which the preview is shown
        if ($(this).attr('src') == self.previewImageUrl) {
            $('#kml-preview-container').show();
        }
    });
};

/**
 * Load the passed URL and show the bottom left preview image.
 */
KmlViewerUi.prototype.showPreviewImage = function (url) {
    this.previewImageUrl = url;
    $('#kml-preview').attr('src', url);
};

/**
 * Hide the preview image.
 */
KmlViewerUi.prototype.hidePreviewImage = function () {
    this.previewImageUrl = emptyGif;
    $('#kml-preview').attr('src', emptyGif);
    $('#kml-preview-container').hide();
};

/**
 * Show or hide the Jarkus specific controls.
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
 * Disable (make gray) all UI controls.
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
 * Called by the Google Earth plugin.
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
        this.tsc.startControl();

        // start streaming pct checker
        this.strc.startControl();

        // add the global click handler
        this.addGlobalClickHandler();

        // show the right upper controls
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

/**
 * Display either the playing or pause icon in the UI. Can be called from
 * GETimeSliderControl, when upper time limit has been reached.
 */
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

/**
 * Mark a node in the Tree as "loading" and show a spinner.
 */
KmlViewerUi.prototype.setNodeLoading = function (id, loading) {
    this.treePanel.getRootNode().cascadeBy(function (node) {
        var kml_id = node.get('kml_id');
        if (id === kml_id) {
            node.set('loading', loading);
            return false; // NOTE: this exits the cascadeBy loop
        }
    });
};

/**
 * Show a big modal balloon in the center of the map, which isn't
 * attached to a feature.
 */
KmlViewerUi.prototype.showMainBalloon = function (html, maximize) {
    var balloon = ge.createHtmlStringBalloon('');
    balloon.setContentString(html);
    if (maximize === true) {
        var w = Math.round($('#map3d').width() * 0.85);
        var h = Math.round($('#map3d').height() * 0.85);
        balloon.setMinWidth(w);
        balloon.setMinHeight(h);
        balloon.setMaxWidth(w);
        balloon.setMaxHeight(h);
    }
    ge.setBalloon(balloon);
};

/**
 * Enables or disables multiselection.
 */
KmlViewerUi.prototype.toggleMultiSelect = function () {
    if (this.isMultiSelectEnabled) {
        this.stopMultiSelect();
    }
    else {
        this.startMultiSelect();
    }
};

KmlViewerUi.prototype.startMultiSelect = function () {
    this.isMultiSelectEnabled = true;
    this.showMainBalloon('Klik op twee Jarkusraaien, waartussen de grafiek berekend moet worden.');
};

KmlViewerUi.prototype.stopMultiSelect = function () {
     // clear selected items
    this.selectedItems.length = 0;
    this.isMultiSelectEnabled = false;
};

KmlViewerUi.prototype.addGlobalClickHandler = function () {
    google.earth.addEventListener(ge.getGlobe(), 'click', this.clickHandler.bind(this));
};

KmlViewerUi.prototype.clickHandler = function (event) {
    var target = event.getTarget();
    if (target.getType() === 'KmlPlacemark') {
        // this probably means the user click on an item
        // that originates from our custom KML data
        if (this.isMultiSelectEnabled) {
            // don't show the normal popup
            event.preventDefault();
            // pass the clicked placemark
            kvu.addSelectedItem(target);
        }
        else {
            // fetch url to the info panel
            var html = target.getDescription();
            var $link = $(html).find('a[data-dynamic-info="true"]');
            // don't do anything if there's no dynamic info link
            if ($link.length == 1) {
                // don't show the normal balloon
                event.preventDefault();
                var url = $link.attr('href');
                var urlParams = $.extend({}, chartParams);
                // retrieve the info HTML fragment
                $.get(
                    url,
                    urlParams,
                    function (data) {
                        var balloon = ge.createHtmlDivBalloon('');
                        //balloon.setFeature(target);
                        // create a div containing the placemark info,
                        // so we can have JavaScript augment it (using jQuery Tabs)
                        var div = document.createElement('DIV');
                        div.innerHTML = data;
                        balloon.setContentDiv(div);
                        var w = Math.round($('#map3d').width() * 0.85);
                        var h = Math.round($('#map3d').height() * 0.85);
                        balloon.setMinWidth(w);
                        balloon.setMinHeight(h);
                        balloon.setMaxWidth(w);
                        balloon.setMaxHeight(h);
                        ge.setBalloon(balloon);
                        // fill out the div
                        var $tabs = $(div).find('.tabs');
                        // initialize tabs, if there are any
                        $tabs.tabs({
                            //heightStyle: 'fill'
                        });
                        // fix tabs height causing jumping behaviour
                        // the tab contents should scroll
                        $tabs.find('.ui-tabs-panel.ui-widget-content').css({
                            //'height': 'auto',
                            //'overflow-y': 'auto'
                        });
                    }
                );
            }
        }
    }
};

KmlViewerUi.prototype.addSelectedItem = function (item) {
    var id = item.getId();
    console.log('selected ' + id);
    // store clicked items
    this.selectedItems.push(parseInt(id));
    var itemIndex = this.selectedItems.length;
    if (this.selectedItems.length === 2) {
        this.twoItemsSelected();
    }
    else {
        var balloon = ge.createHtmlStringBalloon('');
        balloon.setFeature(item);
        balloon.setContentString('Selectie item nummer ' + itemIndex + ', met ID ' + id + '.');
        ge.setBalloon(balloon);
    }
};

KmlViewerUi.prototype.twoItemsSelected = function () {
    // found out ID's of the selected transects
    var id_min = Math.min.apply(null, this.selectedItems);
    var id_max = Math.max.apply(null, this.selectedItems);

    // stop multi selection mode
    this.stopMultiSelect();

    // show the chart
    var url = window.lizard_settings.lizard_kml.jarkusmean_chart_url + '?id_min=' + id_min + '&id_max=' + id_max;
    if ((id_max - id_min) < 500) {
        this.showMainBalloon(
            '<p>Gemiddelde voor raaien ' + id_min + ' tot en met ' + id_max + '</p>' +
            '<img src="' + url + '" width="1100" height="800" class="spinner-when-loading" />',
            true
        );
    }
    else {
        this.showMainBalloon('Te veel items geselecteerd.');
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
 * Google Earth timeslider / play / pause control.
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
    var begin = this.getExtentBegin();
    if (begin) {
        this.setCurrentTime(begin);
    }
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
            // update the UI
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

/**
 * Returns true when we are playing past the max time of the loaded KML data.
 */
GETimeSliderControl.prototype.isPastEnd = function () {
    return this.getCurrentTimeEnd() >= this.getExtentEnd();
};

/**
 * Returns the current datetime.
 */
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


/**
 * Jump to a specific time.
 */
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

/**
 * Start listening for changes in Google Earths getStreamingPercent.
 */
GEStreamingControl.prototype.startControl = function () {
    this.interval = window.setInterval(this.tick.bind(this), 500);
};

/**
 * Update the UI with the new value of ge.getStreamingPercent.
 */
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
     * Timeout reference, while an update is scheduled.
     */
    this.updateTimeout = null;
}

/**
 * Ensure that an update of the loaded KML files happens somewhere in the near future.
 */
KmlFileCollection.prototype.fireUpdate = function () {
    // Prevent the previous update from occurring.
    if (this.updateTimeout !== null) {
        clearTimeout(this.updateTimeout);
    }

    // Start a new one.
    var self = this;
    this.updateTimeout = setTimeout(function () {
        self.update();
        // Reset the timeout so we know none are scheduled anymore.
        self.updateTimeout = null;
    }, 300);
};

/**
 * Refreshes the loaded KML files based on the state of the checkboxes in the
 * checkbox tree.
 *
 * Fired after a while, so user can rapidly click some checkboxes and not break things.
 */
KmlFileCollection.prototype.update = function () {
    // Get an assoc. array of checked items from the Tree control.
    var checked = kvu.getChecked();

    // Unload any non-checked KML files.
    for (var i in this.kmlFiles) {
        var kmlFile = this.kmlFiles[i];
        if (!(kmlFile.id in checked)) {
            kmlFile.unload();
            delete this.kmlFiles[kmlFile.id];
        }
    }

    // Load all checked KML files.
    for (var i in checked) {
        var item = checked[i];
        if (!(item.id in this.kmlFiles)) {
            this.startLoadingKmlFile(item.id, item.url, item.slug);
        }
    }
};

/**
 * Create a new KmlFile entry, and try loading it in the Google Earth plugin.
 */
KmlFileCollection.prototype.startLoadingKmlFile = function (id, url, slug) {
    var k = new KmlFile(id, url, slug);
    this.kmlFiles[id] = k;
    k.load(function () {
        return kvu.isChecked(id);
    });
};

/**
 * Reloads all 'special' KML files in the collection.
 * Called when params (lift, exaggeration etc) change.
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
 * Find a KML file by id (primary key, '4').
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
 * Find a KML file by slug ('jarkus').
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
 * Unload and remove all loaded KML files.
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
 * A KML resource, which can add and remove itself from the Google Earth plugin.
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
    if (this.slug === "jarkus") {
        // Circumvent Google Earths aggressive caching by adding a random parameter.
        var random = (new Date()).toString();
        var params = $.extend({}, jarkusKmlParams, {'random': random});
        return this.baseUrl + '?' + $.param(params);
    }
    else {
        return this.baseUrl;
    }
};

/**
 * Ask Google Earth to fetch the KML and convert it to an object.
 * Ensures beforeAddCallback is called before actually adding the object.
 *
 * The return value of beforeAddCallback determines whether to continue once loaded,
 * so the user can decide to not continue at all.
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
        // Check if the KML is still needed.
        var doContinue = true;
        if (beforeAddCallback !== undefined) {
            doContinue = beforeAddCallback();
        }
        if (doContinue) {
            // Add new features to Google Earth.
            this.kmlObject = kmlObject;
            ge.getFeatures().appendChild(kmlObject);
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
 * Zoom to extent, if KML file has one defined.
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
}(this));