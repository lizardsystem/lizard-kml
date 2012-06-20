/* Javascript functions for the lizard user interface */

// jslint configuration.  Don't put spaces before 'jslint' and 'global'.
/*jslint browser: true */
/*global $, OpenLayers, window */

// Globals that we ourselves define.
var hiddenStuffHeight, mainContentHeight, sidebarHeight, mainContentWidth,
    verticalItemHeight, accordion, resizeTimer, cachedScrollbarWidth;

// Csrf-for-ajax fix suggested in
// https://docs.djangoproject.com/en/1.3/ref/contrib/csrf/#ajax
$(document).ajaxSend(function (event, xhr, settings) {
    function getCookie(name) {
        var cookie, cookies, cookieValue = null, i;
        if (document.cookie && document.cookie !== '') {
            cookies = document.cookie.split(';');
            for (i = 0; i < cookies.length; i++) {
                cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host, protocol, sr_origin, origin;
        host = document.location.host; // host + port
        protocol = document.location.protocol;
        sr_origin = '//' + host;
        origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
            (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});


function scrollbarWidth() {
    return cachedScrollbarWidth;
}

function calculateScrollbarWidth() {
    // Copied from http://jdsharp.us/jQuery/minute/calculate-scrollbar-width.php
    var div, w1, w2;
    div = $('<div style="width:50px;height:50px;overflow:hidden;' +
            'position:absolute;top:-200px;left:-200px;">' +
            '<div style="height:100px;"></div>');
    // Append our div, do our calculation and then remove it
    $('body').append(div);
    w1 = $('div', div).innerWidth();
    div.css('overflow-y', 'scroll');
    w2 = $('div', div).innerWidth();
    $(div).remove();
    cachedScrollbarWidth = (w1 - w2);
}


/**
 * Resize the main window to get an image that is better suited for printing.
 * The image will be printed as soon as all graphs have reloaded.
 *
 * BTW, in Google Chrome too frequent calls to window.print() are ignored:
 * stackoverflow.com/questions/5282719/javascript-print-blocked-by-chrome
 */
function printPage() {
    var max_image_width = 850, graphsToReload;
    if ($("#main").width() > max_image_width) {
        $("#main").width(max_image_width);
        window.print();
    } else {
        // Already proper size.
        window.print();
    }
}


function calculateHiddenStuffHeight() {
    // Calculate once.  If opened, the height isn't 5 but 208 or so...
    hiddenStuffHeight = $("#ui-datepicker-div").outerHeight(true);
}


function stretchOneSidebarBox() {
    /* Stretch out one sidebarbox so that the sidebar is completely filled. */
    var minHeight, stillAvailable, newHeight, sidebarboxStretched,
        includeMargin;
    minHeight = 100; // not smaller than this
    newHeight = $("#sidebar").height();  // Start with total available
    // Subtract other box sizes.
    $("#sidebar > *").not(".sidebarbox-stretched").each(function () {
        newHeight -= $(this).outerHeight(includeMargin = true);
    });
    // Now remove margin from sidebarbox-stretched, 1px
    sidebarboxStretched = $("#sidebar .sidebarbox-stretched");
    newHeight -= ($(sidebarboxStretched).outerHeight(includeMargin = true) -
                  $(sidebarboxStretched).height());
    newHeight = newHeight < minHeight ? minHeight : newHeight;
    $("#sidebar .sidebarbox-stretched").height(newHeight);
}


function fillScreen() {
    /* Resize the main body elements (#sidebar, #content and #map) so that we
    fill the screen completely.

    Detect the height of the window and subtract the known vertical elements
    like header, footer and main content margin/border.

    The resulting height is available as "mainContentHeight".  */

    var viewportHeight, bottomMargin, headerHeight,
        stuffAroundSidebar, footerHeight, menubarHeight,
        stuffAroundMainContent, mainAreaWidth, sidebarWidth, collapserWidth,
        mainDivWidth, viewportWidth;
    // Width.
    viewportWidth = $("body").innerWidth();
    mainAreaWidth = viewportWidth - $("#page").outerWidth(true) +
        $("#page").innerWidth();
    sidebarWidth = $("#sidebar").outerWidth(true);
    collapserWidth = $("#collapser").outerWidth(true);
    mainDivWidth = mainAreaWidth - sidebarWidth - collapserWidth - 2;
    // ^^^ 2px border for the content.
    $("#main").width(mainDivWidth);
    mainContentWidth = $("#content").innerWidth();

    // Height.
    viewportHeight = $(window).height() - hiddenStuffHeight;
    bottomMargin = $("#page").outerHeight(true) - $("#page").innerHeight();
    headerHeight = $("#header").outerHeight(true);
    stuffAroundSidebar = $("#sidebar").outerHeight(true) -
        $("#sidebar").innerHeight();
    sidebarHeight = viewportHeight - headerHeight - bottomMargin -
        stuffAroundSidebar;
    footerHeight = $("#footer").outerHeight(true);
    menubarHeight = $("#menubar").outerHeight(true);
    stuffAroundMainContent = $("#content").outerHeight(true) -
        $("#content").innerHeight();
    mainContentHeight = viewportHeight - headerHeight - bottomMargin -
        footerHeight - menubarHeight -
        stuffAroundMainContent;
    $("#sidebar").height(sidebarHeight);
    $("#collapser").height(sidebarHeight);
    $("#content").height(mainContentHeight);
    $("#textual").height(mainContentHeight);
    $("#map").height(mainContentHeight);
    // The next one ought to be in lizard-map.  For that we'd need a proper
    // set of events that other code can listen to.  So for the time being...
    $('#graph-popup-content').css(
        'max-height',
        mainContentHeight - 30);
    $('.popup-content').css(
        'max-height',
        mainContentHeight - 30);
}


function setUpPrintButton() {
    $('#print-button').addClass('ss_sprite');
    $('#print-button').addClass('ss_printer');
    $('#print-button').toggle(
        function () {
            printPage();
            $('#print-button').removeClass('ss_printer');
            $('#print-button').addClass('ss_arrow_right');
            $('#print-button').data("html", $('#print-button').html());
            $('#print-button').html('&nbsp;&nbsp;');
            return false;
        },
        function () {
            $('#print-button').removeClass('ss_arrow_right');
            $('#print-button').addClass('ss_printer');
            $('#print-button').html($('#print-button').data("html"));
            fillScreen();
            return false;
        }
    );
}


function showExampleMap() {
    /* Show an example map.  For use with the lizardgis.html template.  */
    var map, wms;
    map = new OpenLayers.Map('map');
    wms = new OpenLayers.Layer.WMS(
        "OpenLayers WMS",
        "http://labs.metacarta.com/wms/vmap0", {layers: 'basic'});
    map.addLayer(wms);
    map.zoomToMaxExtent();
}


function divideVerticalSpaceEqually() {
    /* For #evenly-spaced-vertical, divide the vertical space evenly between
    the .vertical-item elements.  Take note of the 4px border between
    them.
    Note that a "not-evenly-spaced" element will be given half the
    space.
    Handy for forms underneath the graphs.
    */
    var numberOfItems, numberOfDoubleItems;
    numberOfItems = $('#evenly-spaced-vertical > .vertical-item').length;
    numberOfDoubleItems = $('#evenly-spaced-vertical > .double-vertical-item').length;
    verticalItemHeight = Math.floor(
        (mainContentHeight / (numberOfItems + 2 * numberOfDoubleItems))) - 1;
    $('#evenly-spaced-vertical > .vertical-item').height(verticalItemHeight);
    $('#evenly-spaced-vertical > .double-vertical-item').height(2 * verticalItemHeight);
}


function setUpCollapsibleSidebarBoxes() {
    /* Headers with .collapsible are set up so jquery(ui) nicely collapses the
       headers when clicked.
    */
    $(".collapsible").each(function () {
        $(this).prepend("<span class='ui-icon ui-icon-triangle-1-s'></span>");
    });
    $(".collapsible").toggle(
        function () {
            $('.ui-icon', this).removeClass('ui-icon-triangle-1-s');
            $('.ui-icon', this).addClass('ui-icon-triangle-1-e');
            $(this).next().slideUp(stretchOneSidebarBox);
        },
        function () {
            $('.ui-icon', this).addClass('ui-icon-triangle-1-s');
            $('.ui-icon', this).removeClass('ui-icon-triangle-1-e');
            $(this).next().slideDown(stretchOneSidebarBox);
        });
}


function setUpCollapsibleSidebar() {
    /* Set up the sidebar to be opened/closed completely */
    $("#collapser").toggle(
        function () {
            $("#sidebar").fadeOut(function () {
                $("#page").removeClass("sidebar-open").addClass("sidebar-closed");
                fillScreen();
            });
        },
        function () {
            $("#page").removeClass("sidebar-closed").addClass("sidebar-open");
            $("#main").width($("#main").width() - 310);
            $("#sidebar").fadeIn('slow', function () {
                fillScreen();
                stretchOneSidebarBox();
            });
        });
}


/*
Sets up treestructures with an interactive interface. Use force_initialize.
*/
function setUpTree(force_initialize) {
    $(".automatic-tree").each(function () {
        if (!$(this).data("tree-initialized") || (force_initialize)) {
            $(this).data("tree-initialized", true);
            $(this).treeview({
                collapsed: true
            });
        }
    });
}


function setUpAccordion() {
    $("#accordion").tabs(
        "#accordion .pane",
        {tabs: "h2, h3",
         effect: "slide"});
    /* Set up a global 'accordion' variable to later steer the animation. */
    accordion = $("#accordion").data("tabs");
    $(".accordion-load-next a").live('click', function (event) {
        var pane, nextPaneId, url, newTitle, ourId;
        event.preventDefault();
        pane = $(this).parents(".accordion-load-next");
        nextPaneId = pane.attr("data-next-pane-id");
        url = $(this).attr("href");
        $(nextPaneId).html('<div class="loading" />');
        $.ajax({
            type: "GET",
            url: url,
            success: function (data) {
                // Update all pane titles and the new pane. Data is the whole
                // (new) html page.
                $(".pane").each(function () {
                    // Title of current pane.
                    newTitle = $(data).find("#" + $(this).attr("id")).prev().html();
                    $(this).prev().html(newTitle);
                    // Refresh target pane contents only.
                    ourId = "#" + $(this).attr("id");
                    if (ourId === nextPaneId) {
                        $(this).html($(data).find(ourId));
                    }
                });
            },
            error: function (e) {
                $(nextPaneId).html('<div class="ss_error ss_sprite" />' +
                                   'Fout bij laden paginaonderdeel.');
            }
        });
        $("li.selected", pane).removeClass("selected");
        $(this).parent("li").addClass("selected");
        accordion.click(accordion.getIndex() + 1);
    });
}


/*
sets up the auto resize sidebar and screen
use this function when altering sidebar without reloading the page
*/
function setUpScreen() {
    fillScreen();
    divideVerticalSpaceEqually();
    setUpCollapsibleSidebarBoxes();
    setUpCollapsibleSidebar();
    stretchOneSidebarBox();
}


function setUpPortalTabs() {
    var selected_tab;
    selected_tab = $("#portal-tab-selected").attr("data-selected");
    if (selected_tab === undefined) {
        selected_tab = $("#portal-tab-selected-default")
            .attr("data-selected");
    }
    $(selected_tab).addClass("selected");
}


function restretchExistingElements() {
    fillScreen();
    divideVerticalSpaceEqually();
    stretchOneSidebarBox();
}


/*
Fill the screen (again) when we open the page and when the window is resized.
*/
$(window).resize(function () {
    // Don't re-calculate 50 times while resizing, only when finished.
    if (resizeTimer) {
        clearTimeout(resizeTimer);
    }
    resizeTimer = setTimeout(restretchExistingElements, 300);
});


function setupLizardUi() {
    calculateScrollbarWidth();
    calculateHiddenStuffHeight();
    fillScreen();
    divideVerticalSpaceEqually();
    setUpCollapsibleSidebarBoxes();
    setUpCollapsibleSidebar();
    //setUpTree();
    stretchOneSidebarBox();
    setUpPrintButton();
}
