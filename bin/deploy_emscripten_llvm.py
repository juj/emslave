#!/usr/bin/python

from __future__ import print_function
import sys, os, shutil, glob, subprocess, time, platform, optparse, stat, re

WINDOWS = False
LINUX = False
OSX = False
if os.name == 'nt': WINDOWS = True
if platform.system() == 'Linux': LINUX = True
if platform.mac_ver()[0] != '': OSX = True

cmake_generator_identifiers = ['']
if WINDOWS:
  cmake_generator_identifiers += ['_vs2019', '_vs2017', '_vs2015']

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
def blacklisted_copy_all_files_in_dir(srcdir, ignore_suffixes, ignore_basenames, dstdir, recursive=False, strip_debugging_symbols_on_executables=False):
  if not os.path.isdir(dstdir):
    mkdir_p(dstdir)

  for f in os.listdir(srcdir):
    basename, ext = os.path.splitext(f)
    if ext.startswith('.'): ext = ext[1:]
    if ext in ignore_suffixes: continue
    if basename in ignore_basenames or f in ignore_basenames: continue

    fn = os.path.join(srcdir, f)
    if os.path.islink(fn):
      linkto = os.readlink(fn)
      print('Creating link ' + os.path.join(dstdir, f) + ' -> ' + linkto)
      os.symlink(linkto, os.path.join(dstdir, f))
    elif recursive and os.path.isdir(fn):
      blacklisted_copy_all_files_in_dir(fn, ignore_suffixes, ignore_basenames, os.path.join(dstdir, f), recursive, strip_debugging_symbols_on_executables)
    elif os.path.isfile(fn):
      dst_file = os.path.join(dstdir, f)
      shutil.copyfile(fn, dst_file)
      if not WINDOWS: # On Windows the file read only bits from DLLs in Program Files are copied, which is not desirable.
        shutil.copymode(fn, dst_file)
      if not WINDOWS and strip_debugging_symbols_on_executables and (stat.S_IXUSR & os.stat(dst_file)[stat.ST_MODE]):
        print('Stripping debug info from file ' + dst_file)
        try:
          subprocess.check_call(['strip', dst_file])
        except:
          pass

def copy_all_files_in_dir(srcdir, dstdir):
  blacklisted_copy_all_files_in_dir(srcdir, [], [], dstdir)

def upload_to_s3(filename, out_s3_addr, options):
  if options.upload_s3:
    cmd = ['aws', 's3', 'cp', filename, out_s3_addr]
    print('Uploading ' + filename + ' to ' + out_s3_addr + '...')
    print(str(cmd))
    subprocess.check_call(cmd)
    print('Done.')

def add_zip_suffix(path, options):
  if options.compress_7zip:
    return path + '.7z'
  if options.compress_zip:
    return path + '.zip'

  if WINDOWS: return path + '.zip'
  else: return path + '.tar.gz'

# zip_root_directory: if True, then the generated zip file will have a root directory under which all the contents of the directory
# will reside. If False, no zip root directory will be generated.
def zip_up_directory(directory, output_file, zip_root_directory, exclude_patterns=[]):
  if WINDOWS or output_file.endswith('.zip') or output_file.endswith('.7z'):
    exclude_args = []
    for p in exclude_patterns: exclude_args += ['-x!' + p]
    zip_hint = ['C:/Program Files/7-Zip'] if WINDOWS else []
    zip_exe = which('7z', zip_hint)
    zip_contents = directory if zip_root_directory else os.path.join(directory, '*')
    cmd = [zip_exe, 'a', output_file, zip_contents, '-mx9'] + exclude_args # mx9=Ultra compression
  else:
    exclude_args = []
    for p in exclude_patterns: exclude_args += ["--exclude=" + p]
    # Specially important is the 'h' parameter to retain symlinks, otherwise the Clang files will blow up to half a gig.
    cmd = ['tar', 'cvhzf', output_file] + exclude_args + [os.path.basename(directory)]
  print(str(cmd))
  env = os.environ.copy()
  env['GZIP'] = '-9' # http://superuser.com/questions/514260/how-to-obtain-maximum-compression-with-tar-gz
  proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(directory))
  proc.communicate()
  if proc.returncode != 0:
    raise Exception('Compression step failed!')

def url_join(u, f):
  if u.endswith('/'): return u + f
  else: return u + '/' + f

tags_updated = False
def update_emsdk_tags(emsdk_dir, force=False):
  global tags_updated
  if tags_updated and not force: return
  run(['python', '-u', os.path.join(emsdk_dir, 'emsdk'), 'update-tags'])
  tags_updated = True

def list_files_in_s3_directory(directory):
  if not directory.endswith('/'): directory += '/'
  cmd = ['aws', 's3', 'ls', directory]
  print(str(cmd))
  files = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
  r = re.compile('\d+-\d+-\d+\s+\d+:\d+:\d+\s+\d+\s+(.*)')

  file_list = []
  for f in files.split('\n'):
    m = r.match(f.strip())
    if m:
      file_list += [m.group(1).strip()]
  return file_list

def create_directory_index(url, options):
  if options.upload_s3:
    files = list_files_in_s3_directory(url)
    files = list(filter(lambda x: x.endswith('.tar.gz') or x.endswith('.zip'), files))

    # Sort the files on descending timestamps. This is possible without a specical predicate, because the files in the directory have exactly same format with descending fixed space fields Y -> M -> D -> H -> Min.
    files.sort(reverse=True)

    open('index.txt', 'w').write('\n'.join(files))
    upload_to_s3('index.txt', url_join(url, 'index.txt'), options)

def deploy_emscripten_llvm_clang(llvm_source_dir, llvm_build_dir, emscripten_source_dir, optimizer_build_dir, binaryen_build_dir, output_dir, cmake_config_to_deploy, s3_llvm_deployment_url, deploy_x64, options):
  build_bitness = '64' if deploy_x64 else '32'

  # Verify that versions match.
  llvm_version = open(os.path.join(llvm_source_dir, 'emscripten-version.txt'), 'r').read().strip()
  print('LLVM version: ' + llvm_version)
  clang_version = open(os.path.join(llvm_source_dir, 'tools', 'clang', 'emscripten-version.txt'), 'r').read().strip()
  print('Clang version: ' + clang_version)
  emscripten_version = open(os.path.join(emscripten_source_dir, 'emscripten-version.txt'), 'r').read().strip()
  print('Emscripten version: ' + emscripten_version)
  if llvm_version != clang_version or llvm_version != emscripten_version or clang_version != emscripten_version:
    print('Repository version mismatch!')
    sys.exit(1)

  if os.path.isdir(output_dir) and len(os.listdir(output_dir)) > 0:
    print('Output directory "' + output_dir + '" exists and is not empty!')
    sys.exit(1)
#  bin_dir = os.path.join(output_dir, 'bin')
  bin_dir = output_dir#os.path.join(output_dir, 'bin')
  mkdir_p(bin_dir)

  shutil.copyfile(os.path.join(llvm_source_dir, 'emscripten-version.txt'), os.path.join(bin_dir, 'emscripten-version.txt'))
  ignored_suffixes = ['ilk', 'pdb']
  ignored_basenames = ['arcmt-test', 'bugpoint', 'c-arcmt-test', 'c-index-text', 'llvm-tblgen', 'clang-tblgen']
  # The LLVM build output binaries directory varies depending on if a CMake multigenerator was used (VS2015 or Xcode IDEs), or if a CMake single-generator was used (Unix Makefiles)
  # Try both forms.
  llvm_binary_dir = os.path.join(llvm_build_dir, cmake_config_to_deploy, 'bin')
  if not os.path.isfile(os.path.join(llvm_binary_dir, exe_suffix('clang'))):
    llvm_binary_dir = os.path.join(llvm_build_dir, 'bin')

  blacklisted_copy_all_files_in_dir(llvm_binary_dir, ignored_suffixes, ignored_basenames, bin_dir, strip_debugging_symbols_on_executables=True)

#  for d in ['include', 'libexec', 'share']:
#    copy_all_files_in_dir(os.path.join(llvm_binary_dir, d), os.path.join(output_dir, d))

  # VS2015 runtime:
  if WINDOWS:
    # Nb. hardcoded to look in default install locations. TODO: make more flexible if needed.
    if deploy_x64:
      copy_all_files_in_dir('C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\x64\\Microsoft.VC140.CRT', bin_dir)
      copy_all_files_in_dir('C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x64', bin_dir)
    else:
      copy_all_files_in_dir('C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\x86\\Microsoft.VC140.CRT', bin_dir)
      copy_all_files_in_dir('C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x86', bin_dir)

  # Emscripten Optimizer
  emscripten_optimizer_binary_dir = os.path.join(optimizer_build_dir, cmake_config_to_deploy)
  if not os.path.isfile(os.path.join(emscripten_optimizer_binary_dir, exe_suffix('optimizer'))):
    emscripten_optimizer_binary_dir = os.path.join(optimizer_build_dir)

  blacklisted_copy_all_files_in_dir(emscripten_optimizer_binary_dir, ignored_suffixes, [], bin_dir)

  # Find where Binaryen was built to.
  binaryen_src_dir = os.path.join(options.emsdk_dir, 'binaryen', 'master')

  binaryen_binary_dirs = []
  for d in cmake_generator_identifiers:
    binaryen_binary_dirs += [
      os.path.join(options.emsdk_dir, 'binaryen', 'master' + d + '_' + build_bitness + 'bit_binaryen', 'bin') # CMake single&multigenerator builds
    ]
  binaryen_binary_dir = list(filter(lambda x: os.path.isfile(os.path.join(x, exe_suffix('asm2wasm'))), binaryen_binary_dirs))
  if len(binaryen_binary_dir) == 0:
    print('Could not find compiled Binaryen asm2wasm(.exe)!')
    sys.exit(1)
  binaryen_binary_dir = binaryen_binary_dir[0]
  print('Binaryen binary directory: ' + binaryen_binary_dir)

  # Print git commit versions from each repository
  git = which('git')
  open(os.path.join(bin_dir, 'emscripten-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=emscripten_source_dir).communicate()[0].decode('utf-8'))
  open(os.path.join(bin_dir, 'llvm-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=llvm_source_dir).communicate()[0].decode('utf-8'))
  if not options.wasm_backend:
    open(os.path.join(bin_dir, 'clang-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=os.path.join(llvm_source_dir, 'tools', 'clang')).communicate()[0].decode('utf-8'))

  deploy_binaryen(binaryen_src_dir, binaryen_binary_dir, bin_dir)

  # Zip up LLVM
  zip_filename = output_dir
  if zip_filename.endswith('\\') or zip_filename.endswith('/'): zip_filename = zip_filename[:-1]
  zip_filename = add_zip_suffix(zip_filename, options)
  print('Zipping up "' + zip_filename + '"')
  if os.path.isfile(zip_filename): os.remove(zip_filename)
  zip_up_directory(output_dir, zip_filename, options.zip_root_directory)
  print(zip_filename + ': ' + str(os.path.getsize(zip_filename)) + ' bytes.')

  # Upload LLVM
  if s3_llvm_deployment_url:
    zip_url = url_join(s3_llvm_deployment_url, os.path.basename(zip_filename))
    upload_to_s3(zip_filename, zip_url, options)

    # Link the latest uploaded file under the canonical name as well:
    canonical_zip_filename = os.path.join(os.path.dirname(zip_filename), 'emscripten-llvm-latest')
    canonical_zip_filename = add_zip_suffix(canonical_zip_filename, options)
    upload_to_s3(zip_url, url_join(s3_llvm_deployment_url, os.path.basename(canonical_zip_filename)), options)

    if options.delete_uploaded_files:
      print('Deleting temporary directory "' + output_dir + '"')
      shutil.rmtree(output_dir)
      print('Deleting temporary file "' + zip_filename + '"')
      os.remove(zip_filename)

  # Re-create directory index in the uploaded directory.
  create_directory_index(s3_llvm_deployment_url, options)

  print('Done. Emscripten LLVM deployed to "' + output_dir + '".')

def deploy_emscripten_docs(emscripten_output_dir, s3_docs_deployment_url):
  # Make and upload documentation if desired.
  subprocess.Popen(['make', 'text'], cwd=os.path.join(emscripten_output_dir, 'site')).communicate()
  subprocess.Popen(['make', 'html'], cwd=os.path.join(emscripten_output_dir, 'site')).communicate()

  cmd = ['aws', 's3', 'cp', '--recursive', os.path.join(emscripten_output_dir, 'site', 'build', 'text'), url_join(s3_docs_deployment_url, 'text')]
  print(str(cmd))
  subprocess.check_call(cmd)

  cmd = ['aws', 's3', 'cp', '--recursive', os.path.join(emscripten_output_dir, 'site', 'build', 'html'), url_join(s3_docs_deployment_url, 'html')]
  print(str(cmd))
  subprocess.check_call(cmd)

def ver_is_equal_or_newer_than(a, b):
  a = a.split('.')
  b = b.split('.')
  for i in range(max(len(a), len(b))):
    a_ver = int(a[i]) if i < len(a) else 0
    b_ver = int(b[i]) if i < len(b) else 0
    if a_ver > b_ver: return True
    if a_ver < b_ver: return False
  return True

def binaryen_version_needed_by_emscripten(emscripten_ver, binaryen_tags):
  if not '.' in emscripten_ver:
    return 'master'

  newest_binaryen_tag = None
  for t in binaryen_tags:
    if ver_is_equal_or_newer_than(emscripten_ver, t):
      if not newest_binaryen_tag or ver_is_equal_or_newer_than(t, newest_binaryen_tag):
        newest_binaryen_tag = t
  return newest_binaryen_tag

def run(cmd, cwd='.'):
  cwd = os.path.abspath(cwd)
  prev_cwd = os.getcwd()
  print(str(cmd) + ' in directory ' + cwd)
  try:
    os.chdir(cwd)
    return subprocess.check_call(cmd)
  finally:
    os.chdir(prev_cwd)

def load_binaryen_tags(emsdk_dir):
  try:
    return open(os.path.join(emsdk_dir, 'binaryen-tags.txt'), 'r').read().split('\n')
  except:
    return []

def is_emscripten_tag_built(emsdk_dir, tag, build_x86):
  try:
    # Check if we have built this tag locally
    d = os.path.join(emsdk_dir, '.built_tags_' + ('32' if build_x86 else '64'))
    f = os.path.join(d, tag + '.txt')
    if os.path.exists(f): return True

    # Check if the tag is known to exist on Amazon S3
    update_emsdk_tags(emsdk_dir)
    existing_tags_on_s3 = open(os.path.join(emsdk_dir, 'llvm-tags-' + ('32' if build_x86 else '64') + 'bit.txt'), 'r').read()
    if 'emscripten-llvm-e' + tag in existing_tags_on_s3: return True

    return False
  except Exception as e:
    print(str(e))
    return False

def mark_tag_built(emsdk_dir, tag, build_x86):
  d = os.path.join(emsdk_dir, '.built_tags_' + ('32' if build_x86 else '64'))
  mkdir_p(d)
  f = os.path.join(d, tag + '.txt')
  open(f, 'w').write('Success!')

def latest_unbuilt_tag(emsdk_dir, build_x86):
  binaryen_tags = load_binaryen_tags(emsdk_dir)
  for tag in reversed(binaryen_tags):
    if not is_emscripten_tag_built(emsdk_dir, tag, build_x86):
      return tag
  return None

def git_pull_emsdk(emsdk_dir):
  git = which('git')

  # To be able to do a 'git pull', make sure we have no changes to local tree.
  run([git, 'checkout', '--', 'emscripten-tags.txt', 'binaryen-tags.txt'], cwd=emsdk_dir)
  run([git, 'pull'], cwd=emsdk_dir)

  # Need to re-download tags after the git pull is done, since we cleared the list of downloaded tags above.
  update_emsdk_tags(emsdk_dir, force=True)


def uninstall_built_emsdk_tag_or_branch(emsdk_dir, tag_or_branch, build_x86):
  print('Uninstalling in emsdk_dir=' + emsdk_dir + ' tag_or_branch=' + tag_or_branch + ' x86=' + str(build_x86))
  build_bitness = '32' if build_x86 else '64'

  binaryen_tags = load_binaryen_tags(emsdk_dir)
  binaryen_version = binaryen_version_needed_by_emscripten(tag_or_branch, binaryen_tags)

  args = []
  if WINDOWS:
    args = ['--vs2017']

  run(['python', '-u', os.path.join(emsdk_dir, 'emsdk'), 'uninstall', 'clang-tag-e' + tag_or_branch + '-' + build_bitness + 'bit'] + args)
  run(['python', '-u', os.path.join(emsdk_dir, 'emsdk'), 'uninstall', 'emscripten-tag-' + tag_or_branch + '-' + build_bitness + 'bit'] + args)
  run(['python', '-u', os.path.join(emsdk_dir, 'emsdk'), 'uninstall', 'binaryen-tag-' + binaryen_version + '-' + build_bitness + 'bit'] + args)

def deploy_binaryen(binaryen_src_dir, binaryen_binary_dir, output_dir):
  print(binaryen_binary_dir + ' -> ' + output_dir)
  binaryen_output_dir = os.path.join(output_dir, 'binaryen')
  mkdir_p(os.path.join(binaryen_output_dir, 'bin'))
  copy_all_files_in_dir(binaryen_binary_dir, os.path.join(binaryen_output_dir, 'bin'))
  mkdir_p(os.path.join(binaryen_output_dir, 'scripts'))
  copy_all_files_in_dir(os.path.join(binaryen_src_dir, 'scripts'), os.path.join(binaryen_output_dir, 'scripts'))
  mkdir_p(os.path.join(binaryen_output_dir, 'src', 'js'))
  copy_all_files_in_dir(os.path.join(binaryen_src_dir, 'src', 'js'), os.path.join(binaryen_output_dir, 'src', 'js'))

def build_emsdk_tag_or_branch(emsdk_dir, tag_or_branch, cmake_build_type, build_x86):
  git_pull_emsdk(emsdk_dir)
  update_emsdk_tags(emsdk_dir)

  build_bitness = '32' if build_x86 else '64'

  binaryen_tags = load_binaryen_tags(emsdk_dir)
  binaryen_version = binaryen_version_needed_by_emscripten(tag_or_branch, binaryen_tags)

  args = []
  if WINDOWS:
    args = ['--vs2017']

  run(['python', '-u', os.path.join(emsdk_dir, 'emsdk'), 'install', 'sdk-tag-' + tag_or_branch + '-' + build_bitness + 'bit', '--build=' + cmake_build_type] + args)
  run(['python', '-u', os.path.join(emsdk_dir, 'emsdk'), 'install', 'binaryen-tag-' + binaryen_version + '-' + build_bitness + 'bit', '--build=' + cmake_build_type] + args)

def deploy_clang_optimizer_binaryen_tag(emsdk_dir, tag_or_branch, cmake_build_type, build_x86, output_dir, options, s3_llvm_deployment_url):
  build_bitness = '32' if build_x86 else '64'
  binaryen_version = binaryen_version_needed_by_emscripten(tag_or_branch, load_binaryen_tags(emsdk_dir))

  llvm_dir = os.path.join(options.emsdk_dir, 'llvm', 'git') if options.wasm_backend else os.path.join(options.emsdk_dir, 'clang', 'fastcomp')
  if tag_or_branch == 'master':
    llvm_source_dir = os.path.join(llvm_dir, 'src')
  else:
    llvm_source_dir = os.path.join(emsdk_dir, 'clang', 'tag-e' + tag_or_branch, 'src')

  # Find where LLVM/Clang was built to.
  clang_binary_dirs = []
  for d in cmake_generator_identifiers:
    clang_binary_dirs += [
      os.path.join(llvm_dir, 'build_' + tag_or_branch + d + '_' + build_bitness, cmake_build_type, 'bin'), # CMake multigenerator build (Visual Studio, XCode)
      os.path.join(llvm_dir, 'build_' + tag_or_branch + d + '_' + build_bitness, 'bin'), # CMake singlegenerator build (Visual Studio, XCode)
      os.path.join(emsdk_dir, 'clang', 'fastcomp', 'build_' + tag_or_branch + d + '_' + build_bitness, cmake_build_type, 'bin'), # CMake multigenerator build (Visual Studio, XCode)
      os.path.join(emsdk_dir, 'clang', 'fastcomp', 'build_' + tag_or_branch + d + '_' + build_bitness, 'bin'), # CMake singlegenerator build (Visual Studio, XCode)
      os.path.join(emsdk_dir, 'clang', 'tag-e' + tag_or_branch, 'build_tag-e' + tag_or_branch + d + '_' + build_bitness, cmake_build_type, 'bin'), # CMake multigenerator build (Visual Studio, XCode)
      os.path.join(emsdk_dir, 'clang', 'tag-e' + tag_or_branch, 'build_tag-e' + tag_or_branch + d + '_' + build_bitness, 'bin') # CMake singlegenerator build (Makefiles)
    ]
  clang_binary_dir = list(filter(lambda x: os.path.isfile(os.path.join(x, exe_suffix('clang'))), clang_binary_dirs))
  if len(clang_binary_dir) == 0:
    print('Could not find compiled clang(.exe) in any of Clang binary directories:\n' + '\n'.join(clang_binary_dirs))
    sys.exit(1)
  clang_binary_dir = clang_binary_dir[0]
  print('LLVM/Clang binary directory: ' + clang_binary_dir)

  # Find where Emscripten optimizer was built to.
  opt_binary_dirs = []
  for d in cmake_generator_identifiers:
    opt_binary_dirs += [
      os.path.join(emsdk_dir, 'emscripten', tag_or_branch + d + '_' + build_bitness + 'bit_optimizer', cmake_build_type), # CMake multigenerator build (Visual Studio, XCode)
      os.path.join(emsdk_dir, 'emscripten', tag_or_branch + d + '_' + build_bitness + 'bit_optimizer'), # CMake singlegenerator build (Visual Studio, XCode)
      os.path.join(emsdk_dir, 'emscripten', 'tag-' + tag_or_branch + d + '_' + build_bitness + 'bit_optimizer', cmake_build_type), # CMake multigenerator build (Visual Studio, XCode)
      os.path.join(emsdk_dir, 'emscripten', 'tag-' + tag_or_branch + d + '_' + build_bitness + 'bit_optimizer') # CMake singlegenerator build (Makefiles)
    ]
  opt_binary_dir = list(filter(lambda x: os.path.isfile(os.path.join(x, exe_suffix('optimizer'))), opt_binary_dirs))
  if len(opt_binary_dir) == 0:
    print('Could not find compiled optimizer(.exe) in any of directories:\n' + '\n'.join(opt_binary_dirs))
    sys.exit(1)
  opt_binary_dir = opt_binary_dir[0]
  print('Optimizer binary directory: ' + opt_binary_dir)

  print(tag_or_branch)
  if tag_or_branch == 'master':
    binaryen_src_dir = os.path.join(emsdk_dir, 'binaryen', tag_or_branch)
  else:
    binaryen_src_dir = os.path.join(emsdk_dir, 'binaryen', 'tag-' + binaryen_version)

  # Find where Binaryen was built to.
  binaryen_binary_dirs = []
  for d in cmake_generator_identifiers:
    binaryen_binary_dirs += [
      os.path.join(emsdk_dir, 'binaryen', tag_or_branch + d + '_' + build_bitness + 'bit_binaryen', 'bin'), # CMake single&multigenerator builds
      os.path.join(emsdk_dir, 'binaryen', 'tag-' + binaryen_version + d + '_' + build_bitness + 'bit_binaryen', 'bin') # CMake single&multigenerator builds
    ]
  binaryen_binary_dir = list(filter(lambda x: os.path.isfile(os.path.join(x, exe_suffix('asm2wasm'))), binaryen_binary_dirs))
  if len(binaryen_binary_dir) == 0:
    print('Could not find compiled Binaryen asm2wasm(.exe) in any of directories:\n' + '\n'.join(binaryen_binary_dirs))
    sys.exit(1)
  binaryen_binary_dir = binaryen_binary_dir[0]
  print('Binaryen binary directory: ' + binaryen_binary_dir)
  binaryen_output_dir = os.path.join(output_dir, 'binaryen')
  print('Binaryen output directory: ' + binaryen_output_dir)

  # Deploy all tools
  if os.path.isdir(output_dir):
    print('Old output directory ' + output_dir + ' exists, cleaning.')
    shutil.rmtree(output_dir)
  print('Generating ' + output_dir)
  print(clang_binary_dir + ' -> ' + output_dir)
  shutil.copytree(clang_binary_dir, output_dir)

  # Copy LLVM license
  license_path = os.path.join(llvm_source_dir, 'llvm') if options.wasm_backend else llvm_source_dir
  shutil.copyfile(os.path.join(license_path, 'LICENSE.txt'), os.path.join(output_dir, 'LICENSE.txt'))
  print(opt_binary_dir + ' -> ' + output_dir)
  shutil.copy(os.path.join(opt_binary_dir, exe_suffix('optimizer')), os.path.join(output_dir, exe_suffix('optimizer')))

  deploy_binaryen(binaryen_src_dir, binaryen_binary_dir, output_dir)

  if not options.wasm_backend:
    print(os.path.join(llvm_source_dir, 'emscripten-version.txt') + ' -> ' + os.path.join(output_dir, 'emscripten-version.txt'))
    shutil.copyfile(os.path.join(llvm_source_dir, 'emscripten-version.txt'), os.path.join(output_dir, 'emscripten-version.txt'))
    open(os.path.join(binaryen_output_dir, 'binaryen-version.txt'), 'w').write(binaryen_version)

  zip_filename = output_dir
  if zip_filename.endswith('\\') or zip_filename.endswith('/'): zip_filename = zip_filename[:-1]
  zip_filename = add_zip_suffix(zip_filename, options)
  print('Zipping up "' + zip_filename + '"')
  if os.path.isfile(zip_filename): os.remove(zip_filename)
  zip_up_directory(output_dir, zip_filename, options.zip_root_directory)

  print(zip_filename + ': ' + str(os.path.getsize(zip_filename)) + ' bytes.')

  if options.deploy_llvm:
    zip_url = url_join(s3_llvm_deployment_url, os.path.basename(zip_filename))
    upload_to_s3(zip_filename, zip_url, options)
    create_directory_index(s3_llvm_deployment_url, options) # Re-create directory index in the uploaded directory.

def deploy_emscripten(llvm_source_dir, emscripten_source_dir, emscripten_output_dir, s3_emscripten_deployment_url, s3_docs_deployment_url, options):
  if options.git_clean:
    print('Git cleaning Emscripten directory for zipping it up..')
    subprocess.Popen(['git', 'clean', '-xdf'], cwd=emscripten_source_dir)
    time.sleep(3)

  if os.path.isdir(emscripten_output_dir):
    shutil.rmtree(emscripten_output_dir)
  IGNORE_PATTERNS = ('*.pyc','.git')

  closure_filter = ['google-closure-compiler-osx', 'google-closure-compiler-linux'] if WINDOWS else ['google-closure-compiler-windows']

  # Copies all files from src to dst, but ignores ones with specific suffixes and file basenames
  blacklisted_copy_all_files_in_dir(emscripten_source_dir, IGNORE_PATTERNS, ['docs', 'site', 'tests', 'websockify', '.git', '.gitattributes', '.gitignore', '.github'] + closure_filter, emscripten_output_dir, recursive=True)
#  shutil.copytree(emscripten_source_dir, emscripten_output_dir, ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))

  zip_filename = emscripten_output_dir
  if zip_filename.endswith('\\') or zip_filename.endswith('/'): zip_filename = zip_filename[:-1]
  zip_filename = add_zip_suffix(zip_filename, options)
  print('Zipping up "' + zip_filename + '"')
  if os.path.isfile(zip_filename): os.remove(zip_filename)

  zip_up_directory(emscripten_output_dir, zip_filename, options.zip_root_directory, ['.git', 'third_party/lzma.js/', '*.pyc'])

  print(zip_filename + ': ' + str(os.path.getsize(zip_filename)) + ' bytes.')

  # Print git commit versions from each repository
  git = which('git')
  open(os.path.join(emscripten_output_dir, 'emscripten-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=emscripten_source_dir).communicate()[0].decode('utf-8'))
  open(os.path.join(emscripten_output_dir, 'llvm-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=llvm_source_dir).communicate()[0].decode('utf-8'))
  if not options.wasm_backend:
    open(os.path.join(emscripten_output_dir, 'clang-git-commit.txt'), 'w').write(subprocess.Popen([git, 'log', '-n1'], stdout=subprocess.PIPE, cwd=os.path.join(llvm_source_dir, 'tools', 'clang')).communicate()[0].decode('utf-8'))

  if options.make_and_deploy_docs:
    deploy_emscripten_docs(emscripten_output_dir, s3_docs_deployment_url)

  # Upload Emscripten
  if s3_emscripten_deployment_url:
    zip_url = url_join(s3_emscripten_deployment_url, os.path.basename(zip_filename))
    upload_to_s3(zip_filename, zip_url, options)

    # Link the latest uploaded file under the canonical name as well:
    canonical_zip_filename = os.path.join(os.path.dirname(zip_filename), 'emscripten-latest')
    canonical_zip_filename = add_zip_suffix(canonical_zip_filename, options)
    upload_to_s3(zip_url, url_join(s3_emscripten_deployment_url, os.path.basename(canonical_zip_filename)), options)

    if options.delete_uploaded_files:
      print('Deleting temporary directory "' + emscripten_output_dir + '"')
      shutil.rmtree(emscripten_output_dir)
      print('Deleting temporary file "' + zip_filename + '"')
      os.remove(zip_filename)

  # Re-create directory index in the uploaded directory.
  create_directory_index(s3_emscripten_deployment_url, options)

  print('Done. Emscripten deployed to "' + emscripten_output_dir + '".')

def main():
  usage_str = 'Usage: deploy_emscripten_llvm.py '
  parser = optparse.OptionParser(usage=usage_str)

  parser.add_option('--emsdk_dir', dest='emsdk_dir', default='', help='Root path of Emscripten SDK.')
  parser.add_option('--no_emsdk_install', dest='emsdk_install', action='store_false', default=True, help='If specified, skips running a "emsdk install" step. Use this if you have already manually built/installed the desired SDK configuration and do not need to re-do this step.')
  parser.add_option('--build_tag', dest='build_tag', default='', help='If specified, checks out the given tag in all repos and builds that instead of the current repository. Otherwise builds and uploads to Nightly bucket.')
  parser.add_option('--build_branch', dest='build_branch', default='', help='If specified, checks out the given branch in all repos and builds that instead of the current repository. Otherwise builds and uploads to Nightly bucket.')
  parser.add_option('--deploy_32bit', dest='deploy_32bit', action='store_true', default=False, help='If true, deploys a 32-bit build instead of the default 64-bit.')
  parser.add_option('--no_upload_s3', dest='upload_s3', action='store_false', default=True, help='If specified, skips uploading built artifacts to Mozilla S3 bucket.')
  parser.add_option('--git_clean', dest='git_clean', action='store_true', default=False, help='If true, performs a "git clean -xdf" operation on the directory before zipping it up.')
  parser.add_option('--deploy_llvm', dest='deploy_llvm', action='store_true', default=False, help='If true, deploys Emscripten fastcomp LLVM+Clang to S3')
  parser.add_option('--deploy_emscripten', dest='deploy_emscripten', action='store_true', default=False, help='If true, deploys Emscripten to S3')
  parser.add_option('--make_and_deploy_docs', dest='make_and_deploy_docs', action='store_true', default=False, help='If true, Emscripten documentation is built and uploaded to S3 Nightly documentation site as well.')
  parser.add_option('--cmake_config', dest='cmake_config', default='', help='Specifies the CMake build configuration type to deploy (Debug, Release, RelWithDebInfo or MinSizeRel)')
  parser.add_option('--delete_uploaded_files', dest='delete_uploaded_files', action='store_true', default=False, help='If true, all generated local files are deleted after successful upload.')
  parser.add_option('--delete_uploaded_build_dirs', dest='delete_uploaded_build_dirs', action='store_true', default=False, help='If true, the build directories are removed after a successful upload.')
  parser.add_option('--7z', dest='compress_7zip', action='store_true', default=False, help='If true, compresses to .7z instead of .zip or .tar.gz.')
  parser.add_option('--zip', dest='compress_zip', action='store_true', default=False, help='If true, compresses to .zip instead of .tar.gz.')
  parser.add_option('--zip_root_directory', dest='zip_root_directory', action='store_true', default=False, help='If true, the generated .zip/.7z file will have a common root directory under which all the zipped files reside. If false, the files are located in the zip without a common directory.')
  parser.add_option('--wasm_backend', dest='wasm_backend', action='store_true', default=False, help='If true, deploying Wasm backend.')

  (options, args) = parser.parse_args(sys.argv)

  # Are we targeting a Nightly build? (automatically dated zip of current contents)
  nightly = (options.build_tag == '' and options.build_branch == '')

  if not options.emsdk_dir:
    print('Please specify --emsdk_dir /path/to/emsdk')
    sys.exit(1)

  if options.build_tag == 'latest_tag':
    print('Latest unbuilt tag is ' + latest_unbuilt_tag(options.emsdk_dir, options.deploy_32bit))
    git_pull_emsdk(options.emsdk_dir)
    update_emsdk_tags(options.emsdk_dir)
    options.build_tag = latest_unbuilt_tag(options.emsdk_dir, options.deploy_32bit)
    print('Latest unbuilt tag: ' + str(options.build_tag))
    if not options.build_tag:
      print('No unbuilt tags left, quitting.')
      sys.exit(0)
    if not ver_is_equal_or_newer_than(options.build_tag, '1.36.13'):
      print('Skipping building tags older than 1.36.13.')
      sys.exit(0)

  options.emsdk_dir = os.path.abspath(options.emsdk_dir)
  print('Path to emsdk: ' + options.emsdk_dir)
  if not os.path.isfile(os.path.join(options.emsdk_dir, 'emsdk')):
    print('--emsdk_dir "' + options.emsdk_dir + '" does not point to a correct emsdk root directory (expected it to contain the file "emsdk")')
    sys.exit(1)

  if not options.cmake_config:
    print('Please specify --cmake_config Debug|Release|RelWithDebInfo|MinSizeRel')
    sys.exit(1)

  if WINDOWS: s3_subdirectory = 'win'
  elif LINUX: s3_subdirectory = 'linux'
  elif OSX: s3_subdirectory = 'osx'

  build_bitness = '32' if options.deploy_32bit else '64'
  s3_subdirectory += '_' + build_bitness + 'bit'

  # Compute the time of the most recent git changes to timestamp the generated build
  git = which('git')

  llvm_dir = os.path.join(options.emsdk_dir, 'llvm', 'git') if options.wasm_backend else os.path.join(options.emsdk_dir, 'clang', 'fastcomp')
  llvm_source_dir = os.path.join(llvm_dir, 'src')

  emscripten_source_dir = os.path.join(options.emsdk_dir, 'emscripten', options.build_branch)

  if nightly:
    llvm_build_dirname = 'build_incoming'
    optimizer_build_dirname = 'incoming'
    if WINDOWS:
      llvm_build_dirname += '_vs2017'
      optimizer_build_dirname += '_vs2017'

    llvm_build_dirname += '_' + build_bitness
    optimizer_build_dirname += '_' + build_bitness +'bit'
    optimizer_build_dirname += '_optimizer'

    llvm_build_dir = os.path.join(llvm_dir, llvm_build_dirname)
    optimizer_build_dir = os.path.join(options.emsdk_dir, 'emscripten', optimizer_build_dirname)
    binaryen_build_dir = ''

    llvm_version = open(os.path.join(llvm_source_dir, 'emscripten-version.txt'), 'r').read().strip()
    if llvm_version.startswith('"'): llvm_version = llvm_version[1:]
    if llvm_version.endswith('"'): llvm_version = llvm_version[:-1]

    emscripten_git_time = int(subprocess.Popen([git, 'log', '-n1', '--format=format:%at'], stdout=subprocess.PIPE, cwd=emscripten_source_dir).communicate()[0].decode('utf-8'))
    llvm_git_time = int(subprocess.Popen([git, 'log', '-n1', '--format=format:%at'], stdout=subprocess.PIPE, cwd=llvm_source_dir).communicate()[0].decode('utf-8'))
    clang_git_time = int(subprocess.Popen([git, 'log', '-n1', '--format=format:%at'], stdout=subprocess.PIPE, cwd=os.path.join(llvm_source_dir, 'tools', 'clang')).communicate()[0].decode('utf-8'))
    newest_time = max(emscripten_git_time, llvm_git_time, clang_git_time)

    output_dir = os.path.join(llvm_dir, "emscripten-llvm-e" + llvm_version + '-' + time.strftime("%Y_%m_%d_%H_%M", time.gmtime(newest_time)))
    if os.path.isdir(output_dir):
      print('Deleting old output directory ' + output_dir)
      shutil.rmtree(output_dir) # Output directory is generated via a timestamp - it shouldn't exist.

    if options.deploy_llvm:
      s3_llvm_deployment_url = 's3://mozilla-games/emscripten/packages/llvm/nightly/' + s3_subdirectory
      deploy_emscripten_llvm_clang(llvm_source_dir, llvm_build_dir, emscripten_source_dir, optimizer_build_dir, binaryen_build_dir, output_dir, options.cmake_config, s3_llvm_deployment_url, not options.deploy_32bit, options)

    if options.deploy_emscripten:
      emscripten_output_dir = os.path.join(options.emsdk_dir, 'emscripten', "emscripten-nightly-" + llvm_version + '-' + time.strftime("%Y_%m_%d_%H_%M", time.gmtime(newest_time)))

      s3_emscripten_deployment_url = 's3://mozilla-games/emscripten/packages/emscripten/nightly/' + ('win' if WINDOWS else 'linux')
      s3_docs_deployment_url = 's3://mozilla-games/emscripten/docs/incoming/'
      deploy_emscripten(llvm_source_dir, emscripten_source_dir, emscripten_output_dir, s3_emscripten_deployment_url, s3_docs_deployment_url, options)
  else: # Building a tag or a branch
    if options.emsdk_install:
      build_emsdk_tag_or_branch(options.emsdk_dir, options.build_tag if options.build_tag else options.build_branch, options.cmake_config, options.deploy_32bit)

    if options.build_tag:
      llvm_source_dir = os.path.join(options.emsdk_dir, 'clang', 'tag-e' + options.build_tag, 'src')

    if options.wasm_backend:
      llvm_version = 'upstream' # TODO
    else:
      llvm_version = open(os.path.join(llvm_source_dir, 'emscripten-version.txt'), 'r').read().strip()
      if llvm_version.startswith('"'): llvm_version = llvm_version[1:]
      if llvm_version.endswith('"'): llvm_version = llvm_version[:-1]

    output_dir = os.path.join(options.emsdk_dir, 'clang', 'emscripten-llvm-e' + llvm_version)
    if os.path.isdir(output_dir):
      print('Deleting old output directory ' + output_dir)
      shutil.rmtree(output_dir)

    s3_llvm_deployment_url = 's3://mozilla-games/emscripten/packages/llvm/tag/' + s3_subdirectory
    if options.deploy_llvm:
      deploy_clang_optimizer_binaryen_tag(options.emsdk_dir, options.build_tag if options.build_tag else options.build_branch, options.cmake_config, options.deploy_32bit, output_dir, options, s3_llvm_deployment_url)

    mark_tag_built(options.emsdk_dir, options.build_tag if options.build_tag else options.build_branch, options.deploy_32bit)

    if options.deploy_emscripten:
      emscripten_output_dir = os.path.join(options.emsdk_dir, 'emscripten', "emscripten-" + llvm_version)

      s3_emscripten_deployment_url = 's3://mozilla-games/emscripten/packages/emscripten/nightly/' + ('win' if WINDOWS else 'linux')
      s3_docs_deployment_url = 's3://mozilla-games/emscripten/docs/incoming/'
      deploy_emscripten(llvm_source_dir, emscripten_source_dir, emscripten_output_dir, s3_emscripten_deployment_url, s3_docs_deployment_url, options)

    if options.delete_uploaded_build_dirs:
      uninstall_built_emsdk_tag_or_branch(options.emsdk_dir, options.build_tag if options.build_tag else options.build_branch, options.deploy_32bit)

  return 0

if __name__ == '__main__':
  sys.exit(main())
