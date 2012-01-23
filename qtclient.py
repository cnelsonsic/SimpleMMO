#!/usr/bin/python

# System imports
import functools
import datetime
from pprint import pformat

# PySide imports
import sys
from PySide.QtCore import *
from PySide.QtGui import *

# Project imports
import idealclient as client
from settings import *

DEBUG = __debug__

class LoginForm(QDialog):
    def __init__(self, parent=None):
        super(LoginForm, self).__init__(parent)
        self.setWindowTitle("Login")

        self.status_icon = QIcon.fromTheme("user-offline")
        self.setWindowIcon(self.status_icon)

        self.server_status = QLabel()
        self.server_status.setAlignment(Qt.AlignCenter)
        self.server_status.setPixmap(self.status_icon.pixmap(64))

        self.username = QLineEdit("Username")

        self.password = QLineEdit("Password")
        self.password.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Getting server status...")
        self.login_button.setEnabled(False)
        self.login_button.clicked.connect(self.login)
        self.login_button.setIcon(self.status_icon)

        self.ping_timer = QTimer(self)
        self.connect(self.ping_timer, SIGNAL("timeout()"), self.is_server_up)
        self.ping_timer.start(1000)

        layout = QVBoxLayout()
        for w in (self.server_status, self.username, self.password, self.login_button):
            layout.addWidget(w)
        self.setLayout(layout)

    def is_server_up(self):
        '''Tests to see if the authentication server is up.'''
        from requests.exceptions import ConnectionError
        try:
            if client.ping_authserver():
                self.login_button.setEnabled(True)
                self.login_button.setText("Login!")
                self.status_icon = QIcon.fromTheme("user-online")
        except(ConnectionError):
            # We can only wait until the server comes back up.
            self.login_button.setEnabled(False)
            self.login_button.setText("Server is offline. :(")
            self.status_icon = QIcon.fromTheme("user-offline")
        self.setWindowIcon(self.status_icon)
        self.server_status.setPixmap(self.status_icon.pixmap(64))
        self.login_button.setIcon(self.status_icon)

    def login(self):
        login_result = client.login(self.username.text(), self.password.text())
        if login_result is True:
            # We logged in, so show the character select dialog
            global charselect
            charselect = CharacterSelect()
            charselect.show()
            # Once its shown, mark this dialog as accepted (And by extension, close it.)
            self.accept()


class CharacterSelect(QDialog):
    def __init__(self, parent=None):
        super(CharacterSelect, self).__init__(parent)
        self.setWindowTitle("Select A Character")

        # Character Portrait
        # Character Sprite
        # Name
        # Current zone
        # Money
        self.charbuttons = {}
        for char in client.get_characters():
            button = QPushButton()
            button.setText(char)
            button.setIcon(QIcon.fromTheme('applications-games'))
            func = functools.partial(self.select_character, char=char)
            button.clicked.connect(func)
            self.charbuttons[char] = button

        layout = QVBoxLayout()
        for w in self.charbuttons.values():
            layout.addWidget(w)
        self.setLayout(layout)

    def select_character(self, char):
        print "Selected %s" % char

        zone = client.get_zone(charname=char)
        print "Player is in the %s zone." % zone

        currentzone = client.get_zoneserver(zone)
        print "Connecting to zoneserver: %s" % currentzone

        # Initialize the world viewer
        global worldviewer
        worldviewer = WorldViewer(charname=char, currentzone=currentzone)
        global worldviewerdebug
        worldviewerdebug = WorldViewerDebug(worldviewer)
        worldviewerdebug.show()
        worldviewer.show()

        # We're all done here.
        self.accept()


class WorldViewerDebug(QDialog):
    def __init__(self, worldviewer, parent=None):
        super(WorldViewerDebug, self).__init__(parent)

        self.setWindowTitle("World Viewer Debug")
        pos = QApplication.instance().desktop().availableGeometry()
        self.move(pos.width()/2, 0)

        self.worldviewer = worldviewer

        self.objects = QTextEdit("<pre>Loading...</pre>")
        self.objects.setReadOnly(True)

        layout = QVBoxLayout()
        for w in (self.objects,):
            layout.addWidget(w)
        self.setLayout(layout)

        self.obj_update_timer = QTimer(self)
        self.connect(self.obj_update_timer, SIGNAL("timeout()"), self.update)
        self.obj_update_timer.start(CLIENT_UPDATE_FREQ)

    def sizeHint(self):
        desktop = QApplication.instance().desktop()
        geom = desktop.availableGeometry()
        return QSize(geom.width()/2, geom.height())

    def show(self):
        '''This is overridden to not allow this to be shown when running in 
        non-debug mode'''
        super(WorldViewerDebug, self).show()
        if not DEBUG:
            self.hide()

    def update(self):
        self.objects.setText(pformat(self.worldviewer.world_objects))


class WorldViewer(QWidget):
    def __init__(self, charname='', currentzone='', parent=None):
        super(WorldViewer, self).__init__(parent)

        self.setWindowTitle("World Viewer")
        if not DEBUG:
            self.setWindowState(Qt.WindowMaximized)
        self.move(0,0)
        self.grabKeyboard()
        self.keyspressed = set()

        self.currentzone = currentzone
        self.charname = charname

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

#         pb = QPushButton("Push!")
#         stylesheet = '''
#                         QPushButton {
#                             border: 2px solid #8f8f91;
#                             border-radius: 6px;
#                             background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
#                                                             stop: 0 #f6f7fa, stop: 1 #dadbde);
#                             min-width: 80px;
#                         }
# 
#                         QPushButton:pressed {
#                             background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
#                                                             stop: 0 #dadbde, stop: 1 #f6f7fa);
#                         }
# 
#                         QPushButton:flat {
#                             border: none; /* no border for a flat push button */
#                         }
#                         QPushButton:default {
#                             border-color: navy; /* make the default button prominent */
#                         }
#         '''
#         pb.setStyleSheet(stylesheet)
#         self.scene.addWidget(pb)

        layout = QVBoxLayout()
        for w in (self.view, ):
            layout.addWidget(w)
        self.setLayout(layout)

        self.loading = self.scene.addText("Loading...")
        self.loading.setHtml("<h1>Loading...</h1>")

        self.last_update = datetime.datetime.now()
        self.world_objects = {}
        self.world_object_widgets = {}
        self._update_objects(client.get_all_objects(self.currentzone))
        print self.world_objects

        # Set character status to online.
        client.set_status(self.currentzone, self.charname)

        self.loading.hide()

        # Set a repeating callback on a timer to get object updates
        self.obj_update_timer = QTimer(self)
        self.connect(self.obj_update_timer, SIGNAL("timeout()"), self.update_objects)
        self.obj_update_timer.start(CLIENT_UPDATE_FREQ)

        # Set a repeating callback on a timer to send movement packets.
        self.movement_timer = QTimer(self)
        self.connect(self.movement_timer, SIGNAL("timeout()"), self.send_movement)
        self.movement_timer.start(CLIENT_UPDATE_FREQ)

    def sizeHint(self):
        desktop = QApplication.instance().desktop()
        geom = desktop.availableGeometry()
        return QSize(geom.width()/2, geom.height()/2)

    def keyPressEvent(self, event):
        '''Qt's key handling is wierd. If a key gets "stuck", just press and release it again.'''

        # Ignore autorepeat events.
        if event.isAutoRepeat():
            event.ignore()
            return

        # Add all other events to our set of pressed keys.
        self.keyspressed.add(event.key())
        event.accept()

    def keyReleaseEvent(self, event):
        # Ignore autorepeat events.
        if event.isAutoRepeat():
            event.ignore()
            return

        # Remove all other events from our set of pressed keys.
        self.keyspressed.discard(event.key())
        event.accept()

    def send_movement(self):
        '''Send movement calls to the zone/movement server.'''
        x = 0
        y = 0

        def _in_set(x, *args):
            for a in args:
                if int(a) in x:
                    return True
            return False

        if _in_set(self.keyspressed, Qt.Key_Left, Qt.Key_A):
            x -= 1
        if _in_set(self.keyspressed, Qt.Key_Right, Qt.Key_D):
            x += 1
        if _in_set(self.keyspressed, Qt.Key_Up, Qt.Key_W):
            y += 1
        if _in_set(self.keyspressed, Qt.Key_Down, Qt.Key_S):
            y -= 1

        client.send_movement(self.currentzone, self.charname, x, y, 0)
        print x, y

    def _update_objects(self, objectslist):
        print "Updated %d objects." % len(objectslist)
        for obj in objectslist:
            obj_id = obj['_id']['$oid']
            self.world_objects.update({obj_id: obj})
            if obj_id not in self.world_object_widgets:
                # Create a new widget, add it to the view and to world_object_widgets
                objwidget = WorldObject(obj)
                self.world_object_widgets.update({obj_id: objwidget})
                self.scene.addItem(objwidget)
            else:
                # Find any differences between the objects, and adjust them on the WorldObject
                self.world_object_widgets[obj_id].setOffset(int(obj['loc']['x']), int(obj['loc']['y']))
                print "Updated widget."

    def update_objects(self):
        '''Gets an upated list of objects from the zone and stores them locally.'''
        new_objects = client.get_objects_since(self.last_update, self.currentzone)
        self._update_objects(new_objects)
        self.last_update = datetime.datetime.now()


class WorldViewerObject(QGraphicsWidget):
    '''The base class for all objects displayed in the WorldViewer.'''
    pass

class WorldObject(QGraphicsPixmapItem):
    '''The class for in-world objects. Barrels, players, monsters, etc.'''
    def __init__(self, obj):
        super(WorldObject, self).__init__()

        objloc = obj.get('loc', {'x':0, 'y':0})
        self.setPos(int(objloc['x']), int(objloc['y']))
        self.setPixmap(QIcon.fromTheme('user-online').pixmap(32))

# Create a Qt application
app = QApplication(sys.argv)

# Show form for logging in
login_form = LoginForm()
login_form.show()

# Show list of characters, and maybe a graphics view of them.
charselect = None

# Create a QGraphicsScene and View and show it.
worldviewerdebug = None
worldviewer = None

# Enter Qt application main loop
app.exec_()
sys.exit()

