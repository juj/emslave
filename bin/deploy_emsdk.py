#!/usr/bin/python

import sys, os, shutil, glob, subprocess, time, platform, optparse, stat, re, tempfile

WINDOWS = False
LINUX = False
OSX = False
if os.name == 'nt': WINDOWS = True
if platform.system() == 'Linux': LINUX = True
if platform.mac_ver()[0] != '': OSX = True
BAT = '.bat' if WINDOWS else ''

# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
  if os.path.exists(path):
    return
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise

def which(program, hint_paths=[]):
  def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

  fpath, fname = os.path.split(program)
  if fpath:
    if is_exe(program):
      return program
  else:
    for path in os.environ["PATH"].split(os.pathsep):
      path = path.strip('"')
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file

      if WINDOWS and not '.' in fname:
        if is_exe(exe_file + '.exe'): return exe_file + '.exe'
        if is_exe(exe_file + '.cmd'): return exe_file + '.cmd'
        if is_exe(exe_file + '.bat'): return exe_file + '.bat'

  if hint_paths:
    for path in hint_paths:
      if os.path.isfile(os.path.join(path, program)): return os.path.join(path, program)
      if WINDOWS and not '.' in program:
        if os.path.isfile(os.path.join(path, program + '.exe')): return os.path.join(path, program + '.exe')
        if os.path.isfile(os.path.join(path, program + '.com')): return os.path.join(path, program + '.com')
        if os.path.isfile(os.path.join(path, program + '.bat')): return os.path.join(path, program + '.bat')

  return None

def run(cmd, cwd='.'):
  cwd = os.path.abspath(cwd)
  prev_cwd = os.getcwd()
  print str(cmd) + ' in directory ' + cwd
  try:
    os.chdir(cwd)
    return subprocess.check_call(cmd)
  finally:
    os.chdir(prev_cwd)

def git_pull_emsdk(emsdk_dir):
  git = which('git')
  run([git, 'checkout', '--', 'emscripten-tags.txt', 'binaryen-tags.txt'], cwd=emsdk_dir)
  run([git, 'pull'], cwd=emsdk_dir)

def add_zip_suffix(path):
  if WINDOWS: return path + '.zip'
  else: return path + '.tar.gz'

def zip_up_directory(directory, output_file, exclude_patterns=[]):
  if WINDOWS:
    exclude_args = []
    for p in exclude_patterns: exclude_args += ['-x!' + p]
    cmd = [which('7z', ['C:/Program Files/7-Zip']), 'a', output_file, os.path.join(directory, '*'), '-mx9'] + exclude_args # mx9=Ultra compression
  else:
    exclude_args = []
    for p in exclude_patterns: exclude_args += ["--exclude=" + p]
    # Specially important is the 'h' parameter to retain symlinks, otherwise the Clang files will blow up to half a gig.
    cmd = ['tar', 'cvhzf', output_file] + exclude_args + [os.path.basename(directory)]
  print str(cmd)
  env = os.environ.copy()
  env['GZIP'] = '-9' # http://superuser.com/questions/514260/how-to-obtain-maximum-compression-with-tar-gz
  proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(directory))
  proc.communicate()
  if proc.returncode != 0:
    raise Exception('Compression step failed!')

def url_join(u, f):
  if u.endswith('/'): return u + f
  else: return u + '/' + f

def upload_to_s3(filename, out_s3_addr):
  cmd = ['aws', 's3', 'cp', filename, out_s3_addr]
  print 'Uploading ' + filename + ' to ' + out_s3_addr + '...'
  print str(cmd)
  subprocess.check_call(cmd)
  print 'Done.'

def main():
  usage_str = 'Usage: deploy_emsdk.py '
  parser = optparse.OptionParser(usage=usage_str)

  parser.add_option('--emsdk_dir', dest='emsdk_dir', default='', help='Root path of Emscripten SDK.')
  parser.add_option('--deploy_s3', dest='deploy_s3', action='store_true', default=False, help='If true, deploys Emsdk packages to S3. If false, only creates local zip/tar.gz files')
  parser.add_option('--delete_temp_files', dest='delete_temp_files', action='store_true', default=False, help='If true, all generated local files are deleted after done.')

  (options, args) = parser.parse_args(sys.argv)

  if not options.emsdk_dir:
    print >> sys.stderr, 'Please specify --emsdk_dir /path/to/emsdk'
    sys.exit(1)

  # Update to latest
  git_pull_emsdk(options.emsdk_dir)

  # Create temp directory to stage to.
  stage_root_dir = tempfile.mkdtemp('_emsdk')
  try:
    stage_dir = os.path.join(stage_root_dir, 'emsdk-portable')
    mkdir_p(stage_dir)
    print 'Staging to "' + stage_dir + '"'

    dirs = []
    files = [
        'binaryen-tags.txt',
        'emcmdprompt.bat',
        'emscripten-tags.txt',
        'emsdk',
        'emsdk.bat',
        'emsdk_env.bat',
        'emsdk_env.sh',
        'emsdk_manifest.json',
        'README.md'
      ]
    emsdk_packages = []

    if WINDOWS:
      emsdk_packages += ['python-2.7.5.3-64bit']
      dirs += ['bin', 'python']

    if len(emsdk_packages) > 0:
      print 'Installing ' + str(emsdk_packages)
      run([os.path.join(options.emsdk_dir, 'emsdk' + BAT), 'install'] + emsdk_packages, cwd=options.emsdk_dir)

    for d in dirs:
      print 'Deploying directory "' + d + '"...'
      shutil.copytree(os.path.join(options.emsdk_dir, d), os.path.join(stage_dir, d))

    for f in files:
      print 'Deploying file "' + f + '"...'
      src = os.path.join(options.emsdk_dir, f)
      dst = os.path.join(stage_dir, f)
      shutil.copyfile(src, dst)
      if not WINDOWS: # On Windows the file read only bits from DLLs in Program Files are copied, which is not desirable.
        shutil.copymode(src, dst)

    # Zip up
    zip_filename_without_directory = add_zip_suffix('emsdk-portable')
    zip_filename = os.path.join(stage_root_dir, zip_filename_without_directory)
    print 'Zipping up "' + zip_filename + '"'
    zip_up_directory(stage_dir, zip_filename)
    print zip_filename + ': ' + str(os.path.getsize(zip_filename)) + ' bytes.'

    # Upload to S3
    if options.deploy_s3:
      s3_emscripten_deployment_url = 's3://mozilla-games/emscripten/releases/' + zip_filename_without_directory
      upload_to_s3(zip_filename, s3_emscripten_deployment_url)

      if WINDOWS: update_zip_name = 'emsdk_windows_update.zip'
      elif OSX: update_zip_name = 'emsdk_osx_update.tar.gz'
      elif LINUX: update_zip_name = 'emsdk_unix_update.tar.gz'
      else: raise Exception('Unknown OS')

      s3_emscripten_deployment_url = 's3://mozilla-games/emscripten/packages/' + update_zip_name
      upload_to_s3(zip_filename, s3_emscripten_deployment_url)

  except Exception, e:
    print >> sys.stderr, str(e)
  finally:
    if options.delete_temp_files:
      print 'Deleting temporary directory "' + stage_root_dir + '"'
      shutil.rmtree(stage_root_dir)

if __name__ == '__main__':
  sys.exit(main())
