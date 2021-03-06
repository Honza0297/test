# Copyright 2019 The GNOME Music Developers
#
# GNOME Music is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# GNOME Music is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with GNOME Music; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# The GNOME Music authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and GNOME Music.  This permission is above and beyond the permissions
# granted by the GPL license by which GNOME Music is covered.  If you
# modify this code, you may extend this exception to your version of the
# code, but you are not obligated to do so.  If you do not wish to do so,
# delete this exception statement from your version.

from gettext import gettext as _
from gi.repository import GObject, Gtk

from gnomemusic.widgets.headerbar import HeaderBar
from gnomemusic.widgets.albumcover import AlbumCover
from gnomemusic.widgets.albumwidget import AlbumWidget


@Gtk.Template(resource_path="/org/gnome/Music/ui/AlbumsView.ui")
class AlbumsView(Gtk.Stack):
    """Gridlike view of all albums

    Album activation switches to AlbumWidget.
    """

    __gtype_name__ = "AlbumsView"

    search_mode_active = GObject.Property(type=bool, default=False)
    selected_items_count = GObject.Property(type=int, default=0, minimum=0)
    selection_mode = GObject.Property(type=bool, default=False)

    _all_albums = Gtk.Template.Child()
    _flowbox = Gtk.Template.Child()

    def __repr__(self):
        return '<AlbumsView>'

    def __init__(self, application, player=None):
        """Initialize AlbumsView

        :param application: The Application object
        """
        super().__init__(transition_type=Gtk.StackTransitionType.CROSSFADE)

        # FIXME: Make these properties.
        self.name = "albums"
        self.title = _("Albums")

        self._window = application.props.window
        self._headerbar = self._window._headerbar

        model = self._window._app.props.coremodel.props.albums_sort
        self._flowbox.bind_model(model, self._create_widget)
        self._flowbox.connect("child-activated", self._on_child_activated)

        self.connect("notify::selection-mode", self._on_selection_mode_changed)

        self.bind_property(
            'selection-mode', self._window, 'selection-mode',
            GObject.BindingFlags.BIDIRECTIONAL)

        self._album_widget = AlbumWidget(application.props.player, self)
        self._album_widget.bind_property(
            "selection-mode", self, "selection-mode",
            GObject.BindingFlags.BIDIRECTIONAL)

        self.add(self._album_widget)

        self.connect(
            "notify::search-mode-active", self._on_search_mode_changed)

        self.show_all()

    def _on_selection_mode_changed(self, widget, data=None):
        if not self.props.selection_mode:
            self.unselect_all()

    def _on_search_mode_changed(self, klass, param):
        if (not self.props.search_mode_active
                and self._headerbar.props.stack.props.visible_child == self
                and self.get_visible_child() == self._album_widget):
            self._set_album_headerbar(self._album_widget.props.album)

    def _create_widget(self, corealbum):
        album_widget = AlbumCover(corealbum)

        self.bind_property(
            "selection-mode", album_widget, "selection-mode",
            GObject.BindingFlags.SYNC_CREATE
            | GObject.BindingFlags.BIDIRECTIONAL)

        # NOTE: Adding SYNC_CREATE here will trigger all the nested
        # models to be created. This will slow down initial start,
        # but will improve initial 'selecte all' speed.
        album_widget.bind_property(
            "selected", corealbum, "selected",
            GObject.BindingFlags.BIDIRECTIONAL)

        return album_widget

    def _back_button_clicked(self, widget, data=None):
        self._headerbar.state = HeaderBar.State.MAIN
        self.props.visible_child = self._all_albums

    def _on_child_activated(self, widget, child, user_data=None):
        corealbum = child.props.corealbum
        if self.props.selection_mode:
            return

        # Update and display the album widget if not in selection mode
        self._album_widget.update(corealbum)

        self._set_album_headerbar(corealbum)
        self.set_visible_child(self._album_widget)

    def _set_album_headerbar(self, corealbum):
        self._headerbar.props.state = HeaderBar.State.CHILD
        self._headerbar.props.title = corealbum.props.title
        self._headerbar.props.subtitle = corealbum.props.artist

    def _toggle_all_selection(self, selected):
        """
        Selects or unselects all items without sending the notify::active
        signal for performance purposes.
        """
        with self._window._app.props.coreselection.freeze_notify():
            for child in self._flowbox.get_children():
                child.props.selected = selected
                child.props.corealbum.props.selected = selected

    def select_all(self):
        self._toggle_all_selection(True)

    def unselect_all(self):
        self._toggle_all_selection(False)
