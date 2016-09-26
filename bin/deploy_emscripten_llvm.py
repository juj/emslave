import sys, os, shutil, glob, subprocess, time, platform

WINDOWS = False
LINUX = False
OSX = False
if os.name == 'nt': WINDOWS = True
if platform.system() == 'Linux': LINUX = True
if platform.mac_ver()[0] != '': OSX = True

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
def blacklisted_copy_all_files_in_dir(srcdir, ignore_suffixes, ignore_basenames, dstdir):
  for f in os.listdir(srcdir):
    basename, ext = os.path.splitext(f)
    if ext.startswith('.'): ext = ext[1:]
    if ext in ignore_suffixes: continue
    if basename in ignore_basenames: continue

    fn = os.path.join(srcdir, f)
    if os.path.isfile(fn):
      shutil.copyfile(fn, os.path.join(dstdir, f))

def copy_all_files_in_dir(srcdir, dstdir):
  blacklisted_copy_all_files_in_dir(srcdir, [], [], dstdir)

def upload_to_s3(filename, out_s3_addr):
  cmd = ['aws', 's3', 'cp', filename, out_s3_addr]
  print 'Uploading ' + filename + ' to ' + out_s3_addr + '...'
  subprocess.call(cmd)
  print 'Done.'

def deploy_emscripten_llvm_clang(llvm_source_dir, llvm_build_dir, emscripten_source_dir, optimizer_build_dir, binaryen_build_dir, output_dir, cmake_config_to_deploy, s3_deployment_url, deploy_x64):
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
  blacklisted_copy_all_files_in_dir(os.path.join(llvm_build_dir, cmake_config_to_deploy, 'bin'), ignored_suffixes, ignored_basenames, output_dir)

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
  blacklisted_copy_all_files_in_dir(os.path.join(optimizer_build_dir, cmake_config_to_deploy), ignored_suffixes, [], output_dir)

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
    print str(cmd)
    subprocess.call(cmd)
  else:
    print 'TODO: Zip up'

  shutil.copyfile(zip_filename, canonical_zip_filename)

  if s3_deployment_url:
    upload_to_s3(zip_filename, s3_deployment_url)
    upload_to_s3(canonical_zip_filename, s3_deployment_url)

  print 'Done. Emscripten LLVM deployed to "' + output_dir + '".'

deploy_x64 = True
emsdk_dir = 'C:/code/emsdk'
llvm_source_dir = os.path.join(emsdk_dir, 'clang', 'fastcomp', 'src')
llvm_build_dirname = 'build_incoming'
optimizer_build_dirname = 'incoming'

if WINDOWS: s3_subdirectory = 'win'
elif LINUX: s3_subdirectory = 'linux'
elif OSX: s3_subdirectory = 'osx'
if WINDOWS:
  llvm_build_dirname += '_vs2015'
  optimizer_build_dirname += '_vs2015'
if deploy_x64:
  llvm_build_dirname += '_64'
  optimizer_build_dirname += '_64bit'
  s3_subdirectory += '_64bit'
else:
  llvm_build_dirname += '_32'
  optimizer_build_dirname += '_32bit'
  s3_subdirectory += '_32bit'
optimizer_build_dirname += '_optimizer'

llvm_build_dir = os.path.join(emsdk_dir, 'clang', 'fastcomp', llvm_build_dirname)
emscripten_source_dir = os.path.join(emsdk_dir, 'emscripten', 'incoming')
optimizer_build_dir = os.path.join(emsdk_dir, 'emscripten', optimizer_build_dirname)
binaryen_build_dir = ''
llvm_version = open(os.path.join(llvm_source_dir, 'emscripten-version.txt'), 'r').read().strip()
if llvm_version.startswith('"'): llvm_version = llvm_version[1:]
if llvm_version.endswith('"'): llvm_version = llvm_version[:-1]
output_dir = os.path.join(emsdk_dir, 'clang', 'fastcomp', "emscripten-llvm-e" + llvm_version + '-' + time.strftime("%Y_%m_%d_%H_%M"))

cmake_config_to_deploy = 'RelWithDebInfo'

s3_deployment_url = 'https://s3.amazonaws.com/mozilla-games/emscripten/packages/nightly/' + s3_subdirectory

deploy_emscripten_llvm_clang(llvm_source_dir, llvm_build_dir, emscripten_source_dir, optimizer_build_dir, binaryen_build_dir, output_dir, cmake_config_to_deploy, s3_deployment_url, deploy_x64)
