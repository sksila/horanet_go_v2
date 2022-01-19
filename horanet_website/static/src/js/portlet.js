(function() {
    $(document).ready(function() {
        // initialisations standard des portlets
        $(".column").sortable({
            connectWith: ".column",
            handle: ".portlet-header",
            cancel: ".portlet-toggle",
            placeholder: "portlet-placeholder ui-corner-all"
        });

        $(".portlet")
            .addClass("ui-widget-content ui-helper-clearfix ui-corner-all")
            .find(".portlet-header")
            .prepend("<span class='fa fa-chevron-down portlet-toggle'></span>");

        $(".portlet .ui-widget-header").click(function() {
            var icon = $(this).find(".fa").first();
            icon.toggleClass("fa-chevron-up fa-chevron-down");
            icon.closest(".portlet").find(".portlet-content").toggle();
        });
    })
})();
