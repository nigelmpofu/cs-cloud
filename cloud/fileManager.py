import os
import mimetypes

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.encoding import smart_str
from wsgiref.util import FileWrapper


def file_size_formatted(file_size):
	"""
	Format file sizes for a humans beings.
	http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
	"""
	for data_unit in ['bytes', 'KB', 'MB', 'GB']:
		if file_size < 1024.0 and file_size > -1024.0:
			return "%3.1f %s" % (file_size, data_unit)
		file_size /= 1024.0
	return "%3.1f %s" % (file_size, 'TB')


class FileManager(object):
	current_user = None
	user_directory = None
	user_storage = None
	def __init__(self, user=None):
		self.current_user = user
		if self.current_user != None:
			self.user_directory = settings.MEDIA_ROOT + "/" + self.current_user.user_id
			# For security, limit access to user directory only
			self.user_storage = FileSystemStorage(location=self.user_directory)
		else:
			# Handle none logged in user
			user_storage = None
		self.update_path(None)


	def update_path(self, path):
		if path is None or len(path) == 0:
			self.path = ''
			self.abspath = self.user_directory
		else:
			self.path = self.clean_path(path)
			self.abspath = os.path.join(self.user_directory, self.path)			
		self.location = self.abspath
		self.url = os.path.join(settings.MEDIA_URL, self.path)


	def clean_path(self, path):
		# replace backslash with slash
		path = path.replace('\\', '/')
		# remove leading and trailing slashes
		path = '/'.join([i for i in path.split('/') if i])

		return path


	def get_breadcrumbs(self):
		breadcrumbs = [{
			'label': 'Filemanager',
			'path': '',
		}]

		parts = [e for e in self.path.split('/') if e]

		path = ''
		for part in parts:
			path = os.path.join(path, part)
			breadcrumbs.append({
				'label': part,
				'path': path,
			})

		return breadcrumbs

	def patch_context_data(self, context):
		context.update({
			'path': self.path,
			'breadcrumbs': self.get_breadcrumbs(),
		})

	def file_details(self):
		filename = self.path.rsplit('/', 1)[-1]
		return {
			'directory': os.path.dirname(self.path),
			'filepath': self.path,
			'filename': filename,
			'filesize': file_size_formatted(STORAGE.size(self.location)),
			'filedate': self.user_storage.get_modified_time(self.location),
			'fileurl': self.url,
		}


	def directory_list(self):
		listing = []

		directories, files = self.user_storage.listdir(self.location)

		def _helper(name, filetype):
			return {
				'filepath': os.path.join(self.path, name),
				'filetype': filetype,
				'filename': name,
				'filedate': self.user_storage.get_modified_time(os.path.join(self.path, name)),
				'filesize': file_size_formatted(self.user_storage.size(os.path.join(self.path, name))),
			}

		for directoryname in directories:
			listing.append(_helper(directoryname, 'directory'))

		mimetypes.init()
		for filename in files:
			guessed_mime = mimetypes.guess_type(filename)[0]
			if(guessed_mime == None):
				file_mime = "unknown"
			else:
				file_mime = str(guessed_mime)
			listing.append(_helper(filename, file_mime))

		return listing


	def upload_file(self, filedata):
		filename = STORAGE.get_valid_name(filedata.name)
		filepath = os.path.join(self.path, filename)
		signals.filemanager_pre_upload.send(sender=self.__class__, filename=filename, path=self.path, filepath=filepath)
		self.user_storage.save(filepath, filedata)
		signals.filemanager_post_upload.send(sender=self.__class__, filename=filename, path=self.path, filepath=filepath)
		return filename

	def download_file(self, filename):
		download_path = ''
		try:
			download_path = os.path.join(self.user_directory, filename)
		except Exception:
			return HttpResponseNotFound("File not found")
		file_wrapper = FileWrapper(open(download_path,'rb'))
		file_mimetype = mimetypes.guess_type(download_path)[0]
		response = HttpResponse(file_wrapper, content_type=file_mimetype)
		response['X-Sendfile'] = download_path
		response['Content-Length'] = self.user_storage.size(download_path)
		response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(filename)
		return response
		
		

	def create_directory(self, dir_name):
		"""
		Create directory by creating temp file in the directory
		FileStorageAPI will create the directory while saving the 
		empty temp file then delete the temp file leaving behind
		the empty new directory
		"""
		if os.path.exists(self.user_storage.path(dir_name)):
			# Directory already exists
			return False
		else:
			user_path = self.user_storage.get_valid_name(dir_name)
			temp_file = os.path.join(user_path, '.tmp')
			print(os.path.exists(self.user_storage.path(dir_name)))
			self.user_storage.save(temp_file, ContentFile(''))
			self.user_storage.delete(temp_file)
			return True
