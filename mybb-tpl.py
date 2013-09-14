# Sublime Plugin: Mybb Template Editor
# Author: Mihai Ionut Vilcu (ionutvmi@gmail.com)
# Aug 2013
# Because sublime is awesome !!! 
 
import sublime, sublime_plugin, subprocess, os, sys
 
class MybbTplLoadCommand(sublime_plugin.TextCommand):
	 
	def run(self, edit):
		self.settings = sublime.load_settings("mybb-tpl.sublime-settings")
		self.show_panel() # we prompt the user for tpl set
 
 
	def load_tpls(self, path):
		px = self.settings.get('table_prefix')
		sid = self.settings.get('tpl_set')
 
		# select all tpl names
		files = self.run_query("SELECT `title` FROM `"+px+"templates` WHERE `sid`='"+ sid +"' OR `sid` = '-2' ORDER BY sid DESC, title ASC")
		files.pop(0) # rempve the first element
 
		# select all templates
		templates = self.run_query("SELECT `template` FROM `"+px+"templates` WHERE `sid`='"+ sid +"' OR `sid` = '-2' ORDER BY sid DESC, title ASC")
		templates.pop(0) # rempve the first element
		 
		tmp = []
		# for each template we make a file and write the template text inside
		for idx,val in enumerate(files):
			if val not in tmp:
				tmp.append(val)
				f = open(path+"/"+val+".mybbtpl", 'wb+')
				f.write(bytes(templates[idx], "UTF-8"))
				f.close()
 
		# clean some stuff
		del files, templates, tmp
 
		self.openInNewWindow(path)
		 
 
	def create_folder(self, folder_name):
		# we build the mybb-tpl folder
		if sublime.platform() == "windows":
			path = os.path.expanduser("~\\My Documents\\" + folder_name)
		else:
			path = os.path.expanduser("~/Documents/" + folder_name)     
		 
		if not os.path.exists(path):
			os.makedirs(path)
 
		self.load_tpls(path) # we download the tpls from db
 
	def show_panel(self):
		prefix = self.settings.get('table_prefix')
		titles = self.run_query("SELECT `title` FROM `"+prefix+"templatesets`")

		if self.settings.get('passwd') != '':
			titles.pop(0) # remove the warning
			
		titles.pop(0) # remove the first row
 
		self.view.window().show_quick_panel(titles, self.setTplSet)
 
	def setTplSet(self, p):
		if p < 0:
			return False;
 
		prefix = self.settings.get('table_prefix')
		 
		tplSets = self.run_query("SELECT `sid` FROM `"+prefix+"templatesets`")
		tplSets.pop(0) # remove the first row
 
		self.settings.set('tpl_set', tplSets[p])
		sublime.save_settings("mybb-tpl.sublime-settings")      
 
		#grab the folder name
		self.view.window().show_input_panel("Folder name:", "mybbTpl", self.create_folder, None, None)
 
	def run_query(self, query):
		if query is None:
			return False
		self.settings = sublime.load_settings("mybb-tpl.sublime-settings")
		mysql = self.settings.get('mysql_executable', 'mysql')
		host = self.settings.get('host', "localhost")
		dbname = self.settings.get('dbname')
		user = self.settings.get('user')
		passwd = self.settings.get('passwd')
		# if password is empty we don't include it
		if passwd == '': 
			conarray = [mysql, '-u', user, '-h', host, dbname, "-e %s" % query]
		else:
			conarray = [mysql, '-u', user, '-p%s' % passwd, '-h', host, dbname, "-e %s" % query]
		conarray = [x for x in conarray if x is not None]
		process = subprocess.Popen(conarray, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		stdout = [x.decode('unicode_escape').rstrip() for x in process.stdout.readlines()]
		return stdout
 
	def openInNewWindow(self, path):
		subprocess.Popen([sublime.executable_path(), '.'], cwd=path, shell=True)
 
 
 
#check for updating the existing tpls and update them if they are edited
 
class MybbTplUpdate(sublime_plugin.EventListener):
	def on_post_save(self, view):
		self.settings = sublime.load_settings("mybb-tpl.sublime-settings")
		path = view.file_name()
		fileName = os.path.basename(path)
		ext = os.path.splitext(fileName)[1]
		if(ext == '.mybbtpl'):
			name = os.path.splitext(fileName)[0]
			self.updateTpl(name, view)
 
 
	def updateTpl(self, name, view):
		sid = self.settings.get('tpl_set')
		prefix = self.settings.get('table_prefix')
		ver = self.settings.get('mybb_version')
		m = MybbTplLoadCommand
 
		# get the content of this file
		content = self.addslashes(view.substr(sublime.Region(0, view.size())))
 
		# we check if this template exists for the current set
		check = m.run_query(m,"SELECT `tid` FROM `"+prefix+"templates` WHERE `title` = '"+name+"' AND `sid` = '"+sid+"'")
		if check == []:
			result = m.run_query(m,"INSERT INTO `"+prefix+"templates` SET `title` = '"+name+"', `template`= '"+content+"', `sid` = '"+sid+"', `version`='"+ver+"'")
		else:
			result = m.run_query(m,"UPDATE `"+prefix+"templates` SET `template`= '"+content+"' WHERE `title` = '"+name+"' AND `sid` = '"+sid+"'")
 
		if check == []:
			sublime.status_message("Template updated successfully !")
 
 
	def addslashes(self, s):
		l = ["\\", '"', "'", "\0", ]
		for i in l:
			if i in s:
				s = s.replace(i, '\\'+i)
		return s