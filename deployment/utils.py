import zipfile
import os

def archive_function(zip_dir, func_name):
    """Archives a given function, and returns the """

    archive_loc = os.path.join('./', zip_dir, func_name + '.zip')
    function_zip = zipfile.ZipFile(archive_loc, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('venv/lib/python2.7/site-packages'):
        for file in files:
            file_path = os.path.join(root, file)
            function_zip.write(file_path)
    function_zip.write(os.path.join('lambda_handlers', func_name + '.py'), func_name + '.py')
    function_zip.close()

    return open(archive_loc)