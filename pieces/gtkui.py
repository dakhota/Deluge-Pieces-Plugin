#
# gtkui.py
#
# Copyright (C) 2009 Nick Lanham <nick@afternight.org>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common
from deluge.ui.gtkui.torrentdetails import Tab

from common import get_resource

class MultiSquare(gtk.DrawingArea):
    def __init__(self, numSquares=0, colors=['#000000']):
        gtk.DrawingArea.__init__(self)
        self.numSquares = numSquares

        colormap = self.get_colormap()
        self.colors = []
        for color in colors:
            self.colors.append(colormap.alloc_color(color, True, True))
        self.colorIndex = {}
        self.connect("expose_event", self.expose)

    def setSquareColor(self,square,color):
        try:
            if self.colorIndex[square] == color:
                return
        except KeyError:
            pass

        if (color == 0):
            try:
                del self.colorIndex[square]
                self.invalidateSquare(square)
            except KeyError:
                pass
        else:
            self.colorIndex[square] = color
            self.invalidateSquare(square)

    def unsetSquareColor(self,square):
        try:
            del self.colorIndex[square]
            invalidateSquare(square)
        except KeyError:
            pass

    def invalidateSquare(self,square):
        if (self.window == None):
            return
        rect = self.get_allocation()
        numAcross =  rect.width / 12
        x = (square % numAcross)*12
        y = (square / numAcross)*12
        rec = gtk.gdk.Rectangle(x, y,12, 12)
        self.window.invalidate_rect(rec,False)

    def setNumSquares(self,numSquares):
        if (self.numSquares != numSquares):
            self.numSquares = numSquares
            self.queue_draw()

    def setColors(self,colors):
        colormap = self.get_colormap()
        self.colors = []
        for color in colors:
            self.colors.append(colormap.alloc_color(color, True, True))
        self.queue_draw()

    def expose(self, widget, event):
        self.context = widget.window.new_gc()
        
        # set a clip region for the expose event
        rec = gtk.gdk.Rectangle(event.area.x, event.area.y,
                                event.area.width, event.area.height)
        self.context.set_clip_rectangle(rec)
        
        self.draw(self.context)
        
        return False
    
    def draw(self, context):
        rect = self.get_allocation()
        plen = self.numSquares

        width =  rect.width
        height = ((plen / (width / 12)) + 1)*12
        width -= 12
        self.set_size_request(width,height)

        x = y = 0
        setColor = False
        context.set_foreground(self.colors[0])
        
	for i in range(0,self.numSquares):
            try:
                color = self.colorIndex[i]
                context.set_foreground(self.colors[color])
                setColor = True
            except KeyError: # no key for this index
                if (setColor):
                    context.set_foreground(self.colors[0])
                    setColor = False
                else:
                    pass

            self.window.draw_rectangle(context,
                                       True,
                                       x,
                                       y,
                                       10,
                                       10)
            x += 12
            if (x > width):
                x = 0
                y += 12


class PiecesTab(Tab):
    def __init__(self):
        Tab.__init__(self)
        glade_tab = gtk.glade.XML(get_resource("pieces_tab.glade"))

        self._name = "Pieces"
        self._child_widget = glade_tab.get_widget("pieces_tab")
        self._tab_label = glade_tab.get_widget("pieces_tab_label")

        self._ms = MultiSquare(0,['#000000','#FF0000','#0000FF'])
        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(self._ms)
        self._child_widget.add(vp)
        self._child_widget.get_parent().show_all()

        self._tid_cache = ""
        self._nump_cache = 0

    def setColors(self,colors):
        self._ms.setColors(colors)

    def update(self):
        # Get the first selected torrent
        selected = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(selected) != 0:
            selected = selected[0]
        else:
            # No torrent is selected in the torrentview
            return

        tor = component.get("TorrentManager").torrents[selected]
        stat = tor.status

        #if (self._tid_cache == selected and
        #    self._nump_cache ==  stat.num_pieces):
        #    return

        self._tid_cache = selected
        self._nump_cache = stat.num_pieces

        plen = len(stat.pieces)
        self._ms.setNumSquares(plen)
        if (plen <= 0):
            return

        peers = tor.handle.get_peer_info()
        curdl = []
        for peer in peers:
            if peer.downloading_piece_index != -1:
                curdl.append(peer.downloading_piece_index)

        curdl = dict.fromkeys(curdl).keys() 
        curdl.sort()
        cdll = len(curdl)
        cdli = 0
        if (cdll == 0):
            cdli = -1

	for i,p in enumerate(stat.pieces):
            if p:
                self._ms.setSquareColor(i,1)
            elif (cdli != -1 and i == curdl[cdli]):
                self._ms.setSquareColor(i,2)
                cdli += 1
                if cdli >= cdll:
                    cdli = -1
            else:
                self._ms.setSquareColor(i,0)
        #



class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade_cfg = gtk.glade.XML(get_resource("config.glade"))
        self._pieces_tab = PiecesTab()
        component.get("TorrentDetails").add_tab(self._pieces_tab)
        client.pieces.get_config().addCallback(self.set_colors)

        component.get("Preferences").add_page("Pieces", self.glade_cfg.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)

    def disable(self):
        component.get("Preferences").remove_page("Pieces")
        component.get("TorrentDetails").remove_tab("Pieces")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for Pieces")
        config = {
            "not_dled_color":self.glade_cfg.get_widget("not_dl_button").get_color().to_string(),
            "dled_color":self.glade_cfg.get_widget("dl_button").get_color().to_string(),
            "dling_color":self.glade_cfg.get_widget("dling_button").get_color().to_string()
        }
        client.pieces.set_config(config)
        client.pieces.get_config().addCallback(self.set_colors)

    def on_show_prefs(self):
        client.pieces.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade_cfg.get_widget("not_dl_button").set_color(gtk.gdk.color_parse(config["not_dled_color"]))
        self.glade_cfg.get_widget("dl_button").set_color(gtk.gdk.color_parse(config["dled_color"]))
        self.glade_cfg.get_widget("dling_button").set_color(gtk.gdk.color_parse(config["dling_color"]))

    def set_colors(self, config):
        self._pieces_tab.setColors([
            config["not_dled_color"],
            config["dled_color"],
            config["dling_color"]])
