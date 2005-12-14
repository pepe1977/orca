# Orca
#
# Copyright 2005 Sun Microsystems Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import orca.atspi as atspi
import orca.debug as debug
import orca.default as default
import orca.rolenames as rolenames
import orca.settings as settings
import orca.speech as speech

from orca.orca_i18n import _

class SpeechGenerator(speechgenerator.SpeechGenerator):
    """Overrides getSpeechContext to handle Mozilla's unique
    hiearchical representation, such as menus duplicating themselves
    in the hierarchy.
    """

    def getSpeechContext(self, obj, stopAncestor=None):
        """Get the speech that describes the names and role of
        the container hierarchy of the object, stopping at and
        not including the stopAncestor.

        Arguments:
        - obj: the object
        - stopAncestor: the anscestor to stop at and not include (None
          means include all ancestors)

        Returns a list of utterances to be spoken.
        """

        utterances = []

        if not obj:
            return utterances

        if obj is stopAncestor:
            return utterances

        # We try to omit fillers and panels without names, and we
        # also omit table cells and menus that duplicate themselves
        # in the hierarchy.
        #
        parent = obj.parent
        if parent \
            and (obj.role == rolenames.ROLE_TABLE_CELL) \
            and (parent.role == rolenames.ROLE_TABLE_CELL):
            parent = parent.parent

        while parent and (parent.parent != parent):
            if parent == stopAncestor:
                break
            if (parent.role != rolenames.ROLE_FILLER) \
                and (parent.role != rolenames.ROLE_SPLIT_PANE) \
                and (parent.role != rolenames.ROLE_UNKNOWN):
                if len(parent.label) > 0:
                    utterances.append(parent.label + " " \
                                      + getSpeechForRoleName(parent))
                elif parent.role != rolenames.ROLE_PANEL:
                    utterances.append(getSpeechForRoleName(parent))

            parent = parent.parent

        utterances.reverse()

        return utterances

class Script(default.Script):
    """The script for Firefox.

    NOTE: THIS IS UNDER DEVELOPMENT AND DOES NOT PROVIDE ANY COMPELLING
    ACCESS TO FIREFOX AT THIS POINT.
    """
    
    def __init__(self, app):
        print "Mozilla.__init__"
        default.Script.__init__(self, app)
        self.listeners["object:link-selected"] = self.onLinkSelected
        self.__textComponentOfInterest = None
        self.__linkOfInterest = None
        
    def getSpeechGenerator(self):
        """Returns the speech generator for this script.
        """
        return SpeechGenerator()

    # This function is called whenever an object within Mozilla receives
    # focus
    #
    def onFocus(self, event):
        print "Mozilla.onFocus:", event.type, event.source.toString()

        # We're going to ignore focus events on the frame.  They
        # are often intermingled with menu activity, wreaking havoc
        # on the context.
        #
        self.__textComponentOfInterest = None
        if event.source.role == rolenames.ROLE_FRAME:
            return
        default.Script.onFocus(self, event)

    # This function is called when a hyperlink is selected - This happens
    # when a link is navigated to using tab/shift-tab
    #
    def onLinkSelected(self, event):
        print "Mozilla.onLinkSelected:"
        debug.printObjectEvent(debug.LEVEL_OFF, event, event.source.toString())

        self.__textComponentOfInterest = event.source
        
        txt = event.source.text
        if txt is None:
            speech.speak(_("link"), self.voices[settings.HYPERLINK_VOICE])
        else:
            text = txt.getText(0, -1)
            speech.speak(text, self.voices[settings.HYPERLINK_VOICE])

    def onCaretMoved(self, event):
        print "Mozilla.onCaretMoved:", event.type, event.source.toString()
        self.__textComponentOfInterest = event.source
        self._presentTextAtNewCaretPosition(event)

    def onStateChanged(self, event):
        print "Mozilla.onStateChanged:", event.type, event.source.toString()
        default.Script.onStateChanged(self, event)

    def locusOfFocusChanged(self, event, oldLocusOfFocus, newLocusOfFocus):
        """Called when the visual object with focus changes.

        Arguments:
        - event: if not None, the Event that caused the change
        - oldLocusOfFocus: Accessible that is the old locus of focus
        - newLocusOfFocus: Accessible that is the new locus of focus
        """
        # Don't bother speaking all the information about the HTML
        # container - it's duplicated all over the place.  So, we
        # just speak the role.
        #
        if newLocusOfFocus \
           and newLocusOfFocus.role == rolenames.ROLE_HTML_CONTAINER:
            # We always automatically go back to focus tracking mode when
            # the focus changes.
            #
            if self.flatReviewContext:
                self.toggleFlatReviewMode()
            self.updateBraille(newLocusOfFocus)
            speech.speak(rolenames.getSpeechForRoleName(newLocusOfFocus))
        else:
            default.Script.locusOfFocusChanged(self,
                                               event,
                                               oldLocusOfFocus,
                                               newLocusOfFocus)
