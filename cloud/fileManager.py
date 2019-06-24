import os
import hashlib
import mimetypes
import shutil
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.utils.encoding import smart_str
from django.shortcuts import get_object_or_404
from .models import User
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

def get_directory_size(file_path):
	"""
	Returns the total size take up by a given directory in bytes
	"""
	total_size = 0
	for path, dirs, files in os.walk(file_path):
		for f in files:
			fp = os.path.join(path, f)
			total_size += os.path.getsize(fp)
	return total_size

def md5_checksum(filename):
	md5_hash = hashlib.md5()
	with open(filename, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			md5_hash.update(chunk)
	return md5_hash.hexdigest()


class FileManager(object):
	current_user = None
	user_directory = None
	user_trash = None
	user_storage = None
	trash_storage = None
	def __init__(self, user=None):
		self.current_user = user
		if self.current_user != None:
			self.user_directory = settings.MEDIA_ROOT + "/" + self.current_user.user_id
			self.user_trash = settings.TRASH_ROOT + "/" + self.current_user.user_id
			# For security, limit access to user directory only
			self.user_storage = FileSystemStorage(location=self.user_directory)
			self.trash_storage = FileSystemStorage(location=self.user_trash)
		else:
			# Handle none logged in user
			user_storage = None
		self.update_path(None)


	def update_path(self, path):
		if path is None or len(path) == 0:
			self.path = ''
			self.abspath = self.user_storage.path(self.user_directory)
		else:
			self.path = self.clean_path(path)
			self.abspath = os.path.join(self.user_storage.path(self.user_directory), self.path)
		self.location = self.abspath
		# self.url = os.path.join(settings.MEDIA_URL, self.path)


	def clean_path(self, path):
		# replace backslash with slash
		path = path.replace('\\', '/')
		# remove leading and trailing slashes
		path = '/'.join([i for i in path.split('/') if i])

		return path


	def get_breadcrumbs(self):
		breadcrumbs = [{
			'label': 'fm-home',
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


	def update_context_data(self, context):
		context.update({
			'path': self.path,
			'breadcrumbs': self.get_breadcrumbs(),
		})


	def file_details(self, file_path):
		# TODO: GET SHARED LINK
		file_path = self.user_storage.path(file_path)
		filename = smart_str(os.path.split(file_path)[1]) # Extract filemame
		if os.path.isfile(file_path):
			return {
				'md5checksum': md5_checksum(file_path),
				'directory': os.path.dirname(file_path),
				'filename': filename,
				'filesize': file_size_formatted(self.user_storage.size(file_path)),
				'filedate': self.user_storage.get_modified_time(file_path),
				'fileurl': file_path,
			}
		else:
			return {}


	def directory_list(self, include_files = True):
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

		if include_files:
			mimetypes.init()
			for filename in files:
				guessed_mime = mimetypes.guess_type(filename)[0]
				if(guessed_mime == None):
					file_mime = "unknown"
				else:
					file_mime = str(guessed_mime)
				listing.append(_helper(filename, file_mime))

		return listing


	def trash_list(self):
		listing = []

		directories, files = self.trash_storage.listdir(self.user_trash)

		def _helper(name, filetype):
			return {
				'filepath': self.trash_storage.get_valid_name(name),
				'filetype': filetype,
				'filename': name,
				'filedate': self.trash_storage.get_modified_time(os.path.join(self.user_trash, name)),
				'filesize': file_size_formatted(self.trash_storage.size(os.path.join(self.user_trash, name))),
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


	def delete_item(self, item_path):
		res_path = item_path
		i = 0
		try:
			delete_path = os.path.join(self.user_storage.path(self.user_directory), item_path)
			while os.path.exists(self.trash_storage.path(os.path.basename(res_path))):
				i = i + 1
				res_path = str(i) + "_" + os.path.basename(item_path)
				new_delete_path = os.path.join(self.user_storage.path(self.user_directory), res_path)
				os.rename(delete_path, new_delete_path)
				delete_path = new_delete_path
		except Exception:
			return HttpResponseNotFound("File not found")
		# Move to trash
		# TODO: Unshare file if shared
		shutil.move(delete_path, self.trash_storage.path(self.user_trash))
		return JsonResponse({'result': 0})


	def purge_item(self, item_path):
		try:
			delete_path = os.path.join(self.trash_storage.path(self.user_trash), item_path)
		except Exception:
			return HttpResponseNotFound("File not found")
		# Permanantly delete file
		if os.path.isdir(delete_path):
			shutil.rmtree(delete_path, ignore_errors=True) # Delete selected directory
		else:
			os.remove(delete_path) # Delete file
		return JsonResponse({'result': 0})


	def upload_file(self, file_data):
		filename = self.user_storage.get_valid_name(file_data.name)
		upload_path = os.path.join(self.user_storage.path(self.location), filename)
		# Check if user has sufficient space
		if file_data.size > self.current_user.get_remaining_quota():
			# Insufficent space
			return False
		else:
			if os.path.exists(self.user_storage.path(upload_path)):
				# Overwrite existing file and remove from quota
				user_db = get_object_or_404(User, pk=self.current_user.user_id)
				user_db.used_quota = user_db.used_quota - int(os.path.getsize(self.user_storage.path(upload_path)))
				user_db.save()
				os.remove(self.user_storage.path(upload_path))
			try:
				# Set max_length as a safety precaution to not go over-quota
				self.user_storage.save(upload_path, file_data, max_length=self.current_user.get_remaining_quota())
				user_db = get_object_or_404(User, pk=self.current_user.user_id)
				# Update Quota
				user_db.used_quota = user_db.used_quota + int(file_data.size)
				user_db.save()
				return True
			except Exception as ex:
				# Upload failed. Not enough space
				return False


	def empty_trash(self):
		# Delete trsah folder and recreate it
		# TODO: Wipe database
		delete_path = self.user_trash
		shutil.rmtree(delete_path, ignore_errors=True) # Delete selected directory
		os.mkdir(delete_path)
		return JsonResponse({'result': 0})


	def restore_item(self, item_path):
		res_path = item_path
		i = 0
		try:
			restore_path = os.path.join(self.trash_storage.path(self.user_trash), item_path)
			user_dir_path = os.path.join(self.user_storage.path(self.user_directory))
			# Rename if item already exists
			while os.path.exists(self.user_storage.path(res_path)):
				i = i + 1
				res_path = str(i) + "_" + item_path
				new_restore_path = os.path.join(self.trash_storage.path(self.user_trash), res_path)
				os.rename(restore_path, new_restore_path)
				restore_path = new_restore_path
		except Exception:
			return HttpResponseNotFound("File not found")
		# Move item back to user directory
		res_location = shutil.move(restore_path, user_dir_path)
		return JsonResponse({'result': 0, 'location': res_location.replace(self.user_storage.path(""), "")})


	def download_file(self, filename):
		download_path = ''
		try:
			download_path = os.path.join(self.user_storage.path(self.user_directory), filename)
		except Exception:
			return HttpResponseNotFound("File not found")
		if os.path.isdir(download_path):
			# Cannot download directory
			return HttpResponseForbidden("Not allowed")
		else:
			file_wrapper = FileWrapper(open(download_path,'rb'))
			file_mimetype = mimetypes.guess_type(download_path)[0]
			response = HttpResponse(file_wrapper, content_type=file_mimetype)
			response['X-Sendfile'] = download_path
			response['Content-Length'] = self.user_storage.size(download_path)
			# Extract filename only
			response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(os.path.split(filename)[1])
			return response


	def create_directory(self, dir_name):
		"""
		Create directory by creating temp file in the directory
		FileStorageAPI will create the directory while saving the 
		empty temp file then delete the temp file leaving behind
		the empty new directory
		"""
		new_directory = os.path.join(self.location, dir_name)
		if os.path.exists(self.user_storage.path(new_directory)):
			# Directory already exists
			return False
		else:
			new_path = self.user_storage.path(new_directory)
			temp_file = os.path.join(new_path, '.tmp')
			self.user_storage.save(temp_file, ContentFile(''))
			self.user_storage.delete(temp_file)
			return True


	def move(self, old_path, new_path):
		"""
		Moves a given file to the provided destination
		"""
		current_path = os.path.join(self.user_storage.path(self.user_directory), old_path)
		move_path = os.path.join(self.user_storage.path(self.user_directory), new_path)
		if current_path == move_path:
			return JsonResponse({"result": 1, "message": "Cannot move '" + current_path.replace(self.user_storage.path(""), "") + "' into itself"}) # Error
		try:
			shutil.move(current_path, move_path)
		except shutil.Error as ex:
			# Strip user directory location and return error
			return JsonResponse({"result": 1, "message": str(ex).replace(self.user_storage.path(""), "")}) # Some sort of error
		return JsonResponse({"result": 0, "message": "success"}) # Success


	def rename(self, file_path, new_name):
		try:
			rename_path = os.path.join(self.user_storage.path(self.user_directory), file_path)
		except Exception:
			# File not found
			return False
		new_name_path = os.path.join(self.user_storage.path(rename_path), "../")
		new_name_path = os.path.join(self.user_storage.path(new_name_path), new_name)
		# TODO: Change shared urls if necessary
		if os.path.exists(new_name_path):
			return False
		else:
			os.rename(rename_path, new_name_path)
			return True