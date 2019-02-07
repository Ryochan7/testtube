import os

from django.core.files.storage import FileSystemStorage
from django.core.files.move import file_move_safe
from django.core.files.base import File, ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

class FileMoveSystemStorage(FileSystemStorage):
  def _save(self, name, content):
    #if isinstance(content, ContentFile) or isinstance(content, InMemoryUploadedFile):
    print("IN MOVER")
    print(type(content))
    print("INNER")
    print(type(content.file))
    print("START FILE CHECK")
    if not isinstance(content.file, File):
      return super()._save(name, content)

    full_path = self.path(name)

    # Create any intermediate directories that do not exist.
    directory = os.path.dirname(full_path)
    if not os.path.exists(directory):
        try:
            if self.directory_permissions_mode is not None:
                # os.makedirs applies the global umask, so we reset it,
                # for consistency with file_permissions_mode behavior.
                old_umask = os.umask(0)
                try:
                    os.makedirs(directory, self.directory_permissions_mode)
                finally:
                    os.umask(old_umask)
            else:
                os.makedirs(directory)
        except FileNotFoundError:
            # There's a race between os.path.exists() and os.makedirs().
            # If os.makedirs() fails with FileNotFoundError, the directory
            # was created concurrently.
            pass

    if not os.path.isdir(directory):
        raise IOError("%s exists and is not a directory." % directory)

    print("")
    print("MADE IT HERE")
    print("")
    # There's a potential race condition between get_available_name and
    # saving the file; it's possible that two threads might return the
    # same name, at which point all sorts of fun happens. So we need to
    # try to create the file, but if it already exists we have to go back
    # to get_available_name() and try again.
    while True:
      try:
        # This file has a file path that we can move.
        if hasattr(content, 'temporary_file_path'):
            file_move_safe(content.temporary_file_path(), full_path)

        else:
          input_file_path = content.file.name
          # Close input file before moving
          content.close()
          os.rename(input_file_path, full_path)
      except FileExistsError:
        # A new name is needed if the file exists.
        name = self.get_available_name(name)
        full_path = self.path(name)
      else:
        break

    if self.file_permissions_mode is not None:
      os.chmod(full_path, self.file_permissions_mode)

    # Store filenames with forward slashes, even on Windows.
    return name.replace('\\', '/')

