odoo.define('horanet_subscription.DiagramView', function (require) {
    "use strict";

    var DiagramRenderer = require('web_diagram.DiagramRenderer');

    DiagramRenderer.include({
        // Obligation de redéfinir l'ensemble de la méthode car la partie à surcharger est
        // contenue dans une boucle de création d'objet, sans retour de valeur (CuteNode)
        _render: function () {
            var self = this;
            var res_nodes = this.state.nodes
            var res_edges = this.state.edges;
//            this.parent_field = result.parent_field;

            var id_to_node = {};

            var style = {
                edge_color: "#A0A0A0",
                edge_label_color: "#555",
                edge_label_font_size: 10,
                edge_width: 2,
                edge_spacing: 100,
                edge_loop_radius: 100,

                node_label_color: "#333",
                node_label_font_size: 12,
                node_outline_color: "#333",
                node_outline_width: 1,
                node_selected_color: "#0097BE",
                node_selected_width: 2,
                node_size_x: 110,
                node_size_y: 80,
                connector_active_color: "#FFF",
                connector_radius: 4,

                close_button_radius: 8,
                close_button_color: "#333",
                close_button_x_color: "#FFF",

                gray: "#DCDCDC",
                white: "#FFF",

                viewport_margin: 50
            };

            // remove previous diagram
            var canvas = self.$('.o_diagram').empty().get(0);

            var r = new Raphael(canvas, '100%', '100%');

            var graph = new CuteGraph(r, style, canvas.parentNode);

            _.each(res_nodes, function (node) {
                var n = new CuteNode(
                    graph,
                    node.x + 50,  //FIXME the +50 should be in the layout algorithm
                    node.y + 50,
                    CuteGraph.wordwrap(node.name, 14),
                    node.shape === 'rectangle' ? 'rect' : 'circle',
                    node.color);

                n.id = node.id;
                id_to_node[node.id] = n;
            });

            _.each(res_edges, function (edge) {
                var e = new CuteEdge(
                    graph,
                    CuteGraph.wordwrap(edge.signal, 32),
                    id_to_node[edge.s_id],
                    id_to_node[edge.d_id] || id_to_node[edge.s_id]);  //WORKAROUND
                e.id = edge.id;
            });

            CuteNode.double_click_callback = function (cutenode) {
                self.edit_node(cutenode.id);
            };
            CuteNode.destruction_callback = function (cutenode) {
                if (!confirm(_t("Deleting this node cannot be undone.\nIt will also delete all connected transitions.\n\nAre you sure ?"))) {
                    return $.Deferred().reject().promise();
                }
                return new data.DataSet(self, self.node).unlink([cutenode.id]);
            };
            CuteEdge.double_click_callback = function (cuteedge) {
                self.edit_connector(cuteedge.id);
            };

            CuteEdge.creation_callback = function (node_start, node_end) {
                return {label: ''};
            };
            CuteEdge.new_edge_callback = function (cuteedge) {
                self.add_connector(cuteedge.get_start().id,
                    cuteedge.get_end().id,
                    cuteedge);
            };
            CuteEdge.destruction_callback = function (cuteedge) {
                if (!confirm(_t("Deleting this transition cannot be undone.\n\nAre you sure ?"))) {
                    return $.Deferred().reject().promise();
                }
                return new data.DataSet(self, self.connector).unlink([cuteedge.id]);
            };
        }
    });
});

// (function () {
//     var _CuteNode = window.CuteNode;
//     window.CuteNode = function () {
//         return _CuteNode.apply(this, arguments);
//     };
// })();

/*
           _,-""`""-~`)
        (`~           \
         |     a   a   \
         ;        o     ; ___  _,,,,_     _.-~'.
          \      `^`    /`_.-"~      `~-;`      \
           \_      _  .'                 `,     |
             |`-                           \'__/
            /                      ,_       \  `'-.
           /    .-""~~--.            `"-,   ;_    /
          |              \               \  | `""`
           \__.--'`"-.   /_               |'
                      `"`  `~~~---..,     |
                                     \ _.-'`-.
                                      \       \
                                       '.     /
                                         `"~"`
*/
