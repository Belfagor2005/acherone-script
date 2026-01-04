# -*- coding: utf-8 -*-
# !/usr/bin/python

# Import standard library
import codecs
from os import chmod, listdir, makedirs, remove, system as os_system
from os.path import exists, join
from random import choice

# Import third-party libraries
from requests import exceptions, get

# Import Enigma2 API
from enigma import eConsoleAppContainer

# Import project-specific components
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

# Import local modules
from . import _, fps


AGENTS = [
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
	"Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
	"Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edge/87.0.664.75",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"
]
version = 'v.1.2'


CONFIG = {
	"script_url": fps,
	"script_dir": "/usr/script"
}


class OpenScript(Screen):
	skin = """
			<screen name="OpenScript" position="center,center" size="1920,1080" Title="Acherone Script" backgroundColor="transparent" flags="wfNoBorder">
				<widget source="list" render="Listbox" position="56,151" size="838,695" itemHeight="50" scrollbarMode="showOnDemand" transparent="1" zPosition="5" foregroundColor="#00a0a0a0" foregroundColorSelected="#ffffff" backgroundColor="#20000000" backgroundColorSelected="#0b2049">
					<convert type="TemplatedMultiContent">
						{"template": [
							MultiContentEntryText(pos=(0, 0), size=(800, 50), font=0, flags=RT_HALIGN_LEFT, text=1),  # Nome script
							<!-- MultiContentEntryText(pos=(300, 0), size=(500, 50), font=0, flags=RT_HALIGN_RIGHT, text=1),  # Descrizione -->
						],
						"fonts": [gFont("Regular", 34)],
						"itemHeight": 50}
					</convert>
				</widget>

				<widget name="line1" position="134,34" size="776,80" font="Regular;42" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#202020" transparent="0" zPosition="1" />
				<widget name="description" position="42,856" size="877,141" font="Regular; 36" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#202020" transparent="0" zPosition="1" />
				<ePixmap name="" position="32,32" size="83,83" zPosition="3" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Acherone/309.png" transparent="1" alphatest="on" />
				<widget font="Regular; 30" halign="right" position="1401,20" render="Label" size="500,40" source="global.CurrentTime" transparent="1">
					<convert type="ClockToText">Format:%a %d.%m. | %H:%M</convert>
				</widget>
				<eLabel backgroundColor="red" cornerRadius="3" position="34,1064" size="296,6" zPosition="11" />
				<eLabel backgroundColor="green" cornerRadius="3" position="342,1064" size="300,6" zPosition="11" />
				<eLabel backgroundColor="yellow" cornerRadius="3" position="652,1064" size="300,6" zPosition="11" />
				<eLabel backgroundColor="blue" cornerRadius="3" position="962,1064" size="300,6" zPosition="11" />
				<widget name="key_red" render="Label" position="32,1016" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
				<widget name="key_green" render="Label" position="342,1016" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
				<widget name="key_yellow" render="Label" position="652,1016" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
				<widget name="key_blue" render="Label" position="962,1016" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
				<eLabel backgroundColor="#002d3d5b" cornerRadius="20" position="0,0" size="1920,1080" zPosition="-99" />
				<eLabel backgroundColor="#001a2336" cornerRadius="30" position="20,1014" size="1880,60" zPosition="-80" />
				<eLabel name="" position="31,30" size="901,977" zPosition="-90" cornerRadius="18" backgroundColor="#00171a1c" foregroundColor="#00171a1c" />
				<widget source="session.VideoPicture" render="Pig" position="997,100" zPosition="19" size="880,499" backgroundColor="transparent" transparent="0" cornerRadius="14" />
			</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self['line1'] = Label(_('Available Scripts'))
		self['description'] = Label(_('Description:\n'))
		self['key_red'] = Label(_('Close'))
		self['key_green'] = Label(_('Select'))
		self['key_yellow'] = Label(_('Download'))
		self['key_blue'] = Label(_('Remove'))
		self.mlist = []
		self['list'] = List(self.mlist)
		self['list'].onSelectionChanged.append(self.on_move)
		self["actions"] = ActionMap(['OkCancelActions', 'ColorActions'], {
			'ok': self.on_select,
			'green': self.on_select,
			'yellow': self.download,
			'blue': self.sremove,
			'cancel': self.close,
		}, -1)
		self.onShown.append(self.refresh_list)

	def refresh_list(self):
		try:
			if not exists('/usr/script'):
				makedirs('/usr/script', 493)
		except:
			pass

		myscripts = listdir('/usr/script')
		scripts = []
		for fil in myscripts:
			if fil.endswith('.sh'):
				fil2 = fil[:-3]
				myfil = '/usr/script/' + str(fil)
				desc = None
				with codecs.open(myfil, "rb", encoding="latin-1") as f:
					for line in f.readlines():
						line = line.strip()
						if line.startswith('#DESCRIPTION='):
							desc = line[13:]
							break
						elif line.startswith('##DESCRIPTION='):
							desc = line[14:]
							break

				if not desc:
					desc = _("%s") % fil2
				desc = desc.replace('_', ' ').replace('-', ' ').capitalize()
				scripts.append((fil2, desc))

		scripts.sort(key=lambda x: x[0].lower())
		self.mlist = scripts
		self['list'].setList(self.mlist)

	def getScrip(self, url):
		dest = '/tmp/script.tar'
		try:
			headers = {"User-Agent": choice(AGENTS)}
			response = get(url, headers=headers, timeout=10)
			response.raise_for_status()

			with open(dest, 'wb') as f:
				f.write(response.content)

			os_system("rm -rf /usr/script/*")
			os_system("tar -xf %s -C /usr/script/" % dest)
			remove(dest)

			for script in listdir('/usr/script'):
				script_path = join('/usr/script', script)
				if script.endswith('.sh'):
					chmod(script_path, 0o755)

			self.refresh_list()
			self.session.open(MessageBox, _("Download completed successfully!"), MessageBox.TYPE_INFO)

		except exceptions.RequestException as e:
			self.session.open(MessageBox, _("Network error: %s") % str(e), MessageBox.TYPE_ERROR)
		except Exception as e:
			self.session.open(MessageBox, str(e), MessageBox.TYPE_ERROR)

	def sremove(self):
		self.session.openWithCallback(self.xremove, MessageBox, _('Remove all scripts from folder?'), MessageBox.TYPE_YESNO)

	def xremove(self, answer=False):
		if answer:
			command = "rm -rf /usr/script/*"
			os_system(command)
			self.refresh_list()
			self.session.open(MessageBox, _('Scripts successfully removed!'), MessageBox.TYPE_INFO)

	def download(self):
		self.session.openWithCallback(self.callMyMsg, MessageBox, _('Download Script Pack?'), MessageBox.TYPE_YESNO)

	def callMyMsg(self, answer=False):
		if answer:
			self.getScrip(fps)

	def on_move(self):
		mysel = self['list'].getCurrent()
		if mysel:
			mytext = ' ' + mysel[1]
			self['description'].setText(str(mytext))
		else:
			self["description"].setText(_("Script Executor %s") % version)

	def on_select(self):
		if len(self.mlist) > 0:
			self.session.openWithCallback(self.selectsc, MessageBox, _('Execute Script Selected?'), MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, _('Please Download Script!'), MessageBox.TYPE_INFO)

	def get_description(self, script):
		if not exists(script):
			print("File not found:", script)
			return None
		try:
			with open(script, "r") as f:
				for line in f:
					if line.startswith("##DESCRIPTION=") or line.startswith("#DESCRIPTION="):
						return line.replace("##DESCRIPTION=", "").replace("#DESCRIPTION=", "").replace('_', ' ').replace('-', ' ').replace('\\n', ' ').capitalize().strip()
		except Exception as e:
			print("Error opening file:", e)
			return None

	def selectsc(self, answer=False):
		if answer:
			mysel = self['list'].getCurrent()
			if mysel:
				script_path = "/usr/script/" + mysel[0] + ".sh"
				if not exists(script_path):
					self.session.open(MessageBox, _("Script not found!"), MessageBox.TYPE_ERROR)
					return

				self.container = eConsoleAppContainer()
				try:
					self.container.appClosed.append(self.finishExecution)
				except:
					self.container.appClosed_conn = self.container.appClosed.connect(self.finishExecution)
				self.container.execute("sh {}".format(script_path))
				self.log_file = "/tmp/acherone.log"
				open(self.log_file, 'w').close()
				try:
					self.container.dataAvail.append(self.logData)
				except:
					self.container.dataAvail_conn = self.container.dataAvail.connect(self.logData)

	def logData(self, data):
		with open(self.log_file, 'a') as f:
			f.write(data.decode())
			f.flush()

	def finishExecution(self, retval):
		if retval == 0:
			self.session.openWithCallback(
				self.openVi,
				MessageBox,
				_("Execution completed!"),
				MessageBox.TYPE_INFO
			)
		else:
			self.session.openWithCallback(
				self.openVi,
				MessageBox,
				_("Error while running (Code: %d)") % retval,
				MessageBox.TYPE_ERROR
			)

	def openVi(self, callback=None):
		user_log = '/tmp/acherone.log'
		if exists(user_log):
			try:
				from .File_Commander import File_Commander
				self.session.open(File_Commander, user_log)
			except Exception as e:
				print("Error opening File_Commander:", str(e))
				self.session.open(
					MessageBox,
					_("Error opening log viewer: %s") % str(e),
					MessageBox.TYPE_ERROR
				)
		else:
			self.session.open(
				MessageBox,
				_("Log file not found!"),
				MessageBox.TYPE_WARNING
			)


def main(session, **kwargs):
	session.open(OpenScript)


def StartSetup(menuid):
	if menuid == "mainmenu":
		return [("Acherone Script", main, "Acherone Script by Lululla", 44)]
	else:
		return []


def Plugins(**kwargs):
	return [
		PluginDescriptor(name="Acherone Script", description=_("Openscript by Lululla"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
		PluginDescriptor(name="Acherone Script", description=_("Openscript by Lululla"), where=PluginDescriptor.WHERE_MENU, fnc=StartSetup)
	]
