#!/usr/bin/python

import sys, os, shutil, glob, subprocess, time, platform, optparse, stat

WINDOWS = False
LINUX = False
OSX = False
if os.name == 'nt': WINDOWS = True
if platform.system() == 'Linux': LINUX = True
if platform.mac_ver()[0] != '': OSX = True

def exe_suffix(path):
  if WINDOWS: return path + '.exe'
  else: return path

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

# Copies all files from src to dst, but ignores ones with specific suffixes and file basenames
def blacklisted_copy_all_files_in_dir(srcdir, ignore_suffixes, ignore_basenames, dstdir, strip_debugging_symbols_on_executables=False):
  for f in os.listdir(srcdir):
    basename, ext = os.path.splitext(f)
    if ext.startswith('.'): ext = ext[1:]
    if ext in ignore_suffixes: continue
    if basename in ignore_basenames: continue

    fn = os.path.join(srcdir, f)
    if os.path.islink(fn):
      linkto = os.readlink(fn)
      print 'Creating link ' + os.path.join(dstdir, f) + ' -> ' + linkto
      os.symlink(linkto, os.path.join(dstdir, f))
    elif os.path.isfile(fn):
      dst_file = os.path.join(dstdir, f)
      shutil.copyfile(fn, dst_file)
      if not WINDOWS: # On Windows the file read only bits from DLLs in Program Files are copied, which is not desirable.
        shutil.copymode(fn, dst_file)
      if not WINDOWS and strip_debugging_symbols_on_executables and (stat.S_IXUSR & os.stat(dst_file)[stat.ST_MODE]):
        print 'Stripping debug info from file ' + dst_file
        try:
          subprocess.check_call(['strip', dst_file])
        except:
          pass

def copy_all_files_in_dir(srcdir, dstdir):
  blacklisted_copy_all_files_in_dir(srcdir, [], [], dstdir)

def upload_to_s3(filename, out_s3_addr):
  cmd = ['aws', 's3', 'cp', filename, out_s3_addr]
  print 'Uploading ' + filename + ' to ' + out_s3_addr + '...'
  print str(cmd)
  subprocess.check_call(cmd)
  print 'Done.'

def deploy_emscripten_llvm_clang(llvm_source_dir, llvm_build_dir, emscripten_source_dir, optimizer_build_dir, binaryen_build_dir, output_dir, cmake_config_to_deploy, s3_deployment_url, deploy_x64, options):
  # Verify that versions match.
  llvm_version = open(os.path.join(llvm_source_dir, 'emscripten-version.txt'), 'r').read().strip()
  print 'LLVM version: ' + llvm_version
  clang_version = open(os.path.join(llvm_source_dir, 'tools', 'clang', 'emscripten-version.txt'), 'r').read().strip()
  print 'Clang version: ' + clang_version
  emscripten_version = open(os.path.join(emscripten_source_dir, 'emscripten-version.txt'), 'r').read().strip()
  print 'Emscripten version: ' + emscripten_version
  if llvm_version != clang_version or llvm_version != emscripten_version or clang_version != emscripten_version:
    print >> sys.stderr, 'Repository version mismatch!'
    sys.exit(1)

  if os.path.isdir(output_dir) and len(os.listdir(output_dir)) > 0:
    print >> sys.stderr, 'Output directory "' + output_dir + '" exists and is not empty!'
    sys.exit(1)
  mkdir_p(output_dir)

  shutil.copyfile(os.path.join(llvm_source_dir, 'emscripten-version.txt'), os.path.join(output_dir, 'emscripten-version.txt'))
  ignored_suffixes = ['ilk', 'pdb']
  ignored_basenames = ['arcmt-test', 'bugpoint', 'c-arcmt-test', 'c-index-text', 'llvm-tblgen', 'clang-tblgen']
  # The LLVM build output binaries directory varies depending on if a CMake multigenerator was used (VS2015 or Xcode IDEs), or if a CMake single-generator was used (Unix Makefiles)
  # Try both forms.
  llvm_binary_dir = os.path.join(llvm_build_dir, cmake_config_to_deploy, 'bin')
  if not os.path.isfile(os.path.join(llvm_binary_dir, exe_suffix('clang'))):
    llvm_binary_dir = os.path.join(llvm_build_dir, 'bin')

  blacklisted_copy_all_files_in_dir(llvm_binary_dir, ignored_suffixes, ignored_basenames, output_dir, strip_debugging_symbols_on_executables=True)

  # VS2015 runtime:
  if WINDOWS:
    # Nb. hardcoded to look in default install locations. TODO: make more flexible if needed.
    if deploy_x64:
      copy_all_files_in_dir('C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\x64\\Microsoft.VC140.CRT', output_dir)
      copy_all_files_in_dir('C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x64', output_dir)
    else:
      copy_all_files_in_dir('C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\x86\\Microsoft.VC140.CRT', output_dir)
      copy_all_files_in_dir('C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x86', output_dir)

  # Emscripten Optimizer
  emscripten_optimizer_binary_dir = os.path.join(optimizer_build_dir, cmake_config_to_deploy)
  if not os.path.isfile(os.path.join(emscripten_optimizer_binary_dir, exe_suffix('optimizer'))):
    emscripten_optimizer_binary_dir = os.path.join(optimizer_build_dir)

  blacklisted_copy_all_files_in_dir(emscripten_optimizer_binary_dir, ignored_suffixes, [], output_dir)

  # Binaryen
  print "TODO: Deploy Binaryen"

  # Print git commit versions from each repository
  git = which('git')
  open(os.path.join(output_dir, 'emscripten-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=emscripten_source_dir).communicate()[0])
  open(os.path.join(output_dir, 'llvm-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=llvm_source_dir).communicate()[0])
  open(os.path.join(output_dir, 'clang-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=os.path.join(llvm_source_dir, 'tools', 'clang')).communicate()[0])

  # Zip up
  zip_filename = output_dir
  if zip_filename.endswith('\\') or zip_filename.endswith('/'): zip_filename = zip_filename[:-1]
  canonical_zip_filename = os.path.join(os.path.dirname(zip_filename), 'emscripten-llvm-latest')
  if WINDOWS:
    zip_filename += '.zip'
    canonical_zip_filename += '.zip'
  else:
    zip_filename += '.tar.gz'
    canonical_zip_filename += '.tar.gz'

  print 'Zipping up "' + zip_filename + '"'
  if os.path.isfile(zip_filename): os.remove(zip_filename)
  if os.path.isfile(canonical_zip_filename): os.remove(canonical_zip_filename)

  if WINDOWS:
    cmd = [which('7z', ['C:/Program Files/7-Zip']), 'a', zip_filename, os.path.join(output_dir, '*')]
  else:
    # Specially important is the 'h' parameter to retain symlinks, otherwise the Clang files will blow up to half a gig.
    cmd = ['tar', 'cvhzf', zip_filename, output_dir]
  print str(cmd)
  env = os.environ.copy()
  env['GZIP'] = '-9' # http://superuser.com/questions/514260/how-to-obtain-maximum-compression-with-tar-gz
  proc = Popen(cmd, env=env)
  proc.communicate()
  if proc.returncode != 0:
    raise Exception('Compression step failed!')

  shutil.copyfile(zip_filename, canonical_zip_filename)

  def url_join(u, f):
    if u.endswith('/'): return u + f
    else: return u + '/' + f

  if s3_deployment_url:
    zip_url = url_join(s3_deployment_url, os.path.basename(zip_filename))
    upload_to_s3(zip_filename, zip_url)

    # Link the latest uploaded file under the canonical name as well:
    upload_to_s3(zip_url, url_join(s3_deployment_url, os.path.basename(canonical_zip_filename)))

    if options.delete_uploaded_files:
      print 'Deleting temporary directory "' + output_dir + '"'
      shutil.rmtree(output_dir)
      print 'Deleting temporary file "' + zip_filename + '"'
      os.remove(zip_filename)
      print 'Deleting temporary file "' + canonical_zip_filename + '"'
      os.remove(canonical_zip_filename)

  print 'Done. Emscripten LLVM deployed to "' + output_dir + '".'

def main():
  usage_str = 'Usage: deploy_emscripten_llvm.py '
  parser = optparse.OptionParser(usage=usage_str)

  parser.add_option('--emsdk_dir', dest='emsdk_dir', default='', help='Root path of Emscripten SDK.')
  parser.add_option('--deploy_32bit', dest='deploy_32bit', action='store_true', default=False, help='If true, deploys a 32-bit build instead of the default 64-bit.')
  parser.add_option('--cmake_config', dest='cmake_config', default='', help='Specifies the CMake build configuration type to deploy (Debug, Release, RelWithDebInfo or MinSizeRel)')
  parser.add_option('--delete_uploaded_files', dest='delete_uploaded_files', action='store_true', default=False, help='If true, all generated local files are deleted after successful upload.')

  (options, args) = parser.parse_args(sys.argv)

  if not options.emsdk_dir:
    print >> sys.stderr, 'Please specify --emsdk_dir /path/to/emsdk'
    sys.exit(1)
  options.emsdk_dir = os.path.abspath(options.emsdk_dir)
  print 'Path to emsdk: ' + options.emsdk_dir
  if not os.path.isfile(os.path.join(options.emsdk_dir, 'emsdk')):
    print >> sys.stderr, '--emsdk_dir "' + options.emsdk_dir + '" does not point to a correct emsdk root directory (expected it to contain the file "emsdk")'
    sys.exit(1)

  if not options.cmake_config:
    print >> sys.stderr, 'Please specfiy --cmake_config Debug|Release|RelWithDebInfo|MinSizeRel'
    sys.exit(1)

  llvm_source_dir = os.path.join(options.emsdk_dir, 'clang', 'fastcomp', 'src')
  llvm_build_dirname = 'build_incoming'
  optimizer_build_dirname = 'incoming'

  if WINDOWS: s3_subdirectory = 'win'
  elif LINUX: s3_subdirectory = 'linux'
  elif OSX: s3_subdirectory = 'osx'
  if WINDOWS:
    llvm_build_dirname += '_vs2015'
    optimizer_build_dirname += '_vs2015'
  if options.deploy_32bit:
    llvm_build_dirname += '_32'
    optimizer_build_dirname += '_32bit'
    s3_subdirectory += '_32bit'
  else:
    llvm_build_dirname += '_64'
    optimizer_build_dirname += '_64bit'
    s3_subdirectory += '_64bit'
  optimizer_build_dirname += '_optimizer'

  llvm_build_dir = os.path.join(options.emsdk_dir, 'clang', 'fastcomp', llvm_build_dirname)
  emscripten_source_dir = os.path.join(options.emsdk_dir, 'emscripten', 'incoming')
  optimizer_build_dir = os.path.join(options.emsdk_dir, 'emscripten', optimizer_build_dirname)
  binaryen_build_dir = ''
  llvm_version = open(os.path.join(llvm_source_dir, 'emscripten-version.txt'), 'r').read().strip()
  if llvm_version.startswith('"'): llvm_version = llvm_version[1:]
  if llvm_version.endswith('"'): llvm_version = llvm_version[:-1]

  # Compute the time of the most recent git changes to timestamp the generated build
  git = which('git')
  emscripten_git_time = int(subprocess.Popen([git, 'log', '-n1', '--format=format:%at'], stdout=subprocess.PIPE, cwd=emscripten_source_dir).communicate()[0])
  llvm_git_time = int(subprocess.Popen([git, 'log', '-n1', '--format=format:%at'], stdout=subprocess.PIPE, cwd=llvm_source_dir).communicate()[0])
  clang_git_time = int(subprocess.Popen([git, 'log', '-n1', '--format=format:%at'], stdout=subprocess.PIPE, cwd=os.path.join(llvm_source_dir, 'tools', 'clang')).communicate()[0])
  newest_time = max(emscripten_git_time, llvm_git_time, clang_git_time)

  output_dir = os.path.join(options.emsdk_dir, 'clang', 'fastcomp', "emscripten-llvm-e" + llvm_version + '-' + time.strftime("%Y_%m_%d_%H_%M", time.gmtime(newest_time)))
  if os.path.isdir(output_dir):
    shutil.rmtree(output_dir) # Output directory is generated via a timestamp - it shouldn't exist.

  s3_deployment_url = 's3://mozilla-games/emscripten/packages/llvm/nightly/' + s3_subdirectory

  deploy_emscripten_llvm_clang(llvm_source_dir, llvm_build_dir, emscripten_source_dir, optimizer_build_dir, binaryen_build_dir, output_dir, options.cmake_config, s3_deployment_url, not options.deploy_32bit, options)

  return 0

if __name__ == '__main__':
  sys.exit(main())
