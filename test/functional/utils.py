import subprocess
import datetime
import os
import stat
import inspect

def create_file(path, size):
    fout = open(path, 'w')
    fout.write(os.urandom(size))
    fout.close()
        
        
def create_random_suffix():
    return datetime.datetime.now().strftime("%y%m%d_%H%M%S")

def remove_file(path):
    os.remove(path)
    
def run_command(cmd, args):
    script_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    cmd = script_path + '/../../src/' + cmd
    p = subprocess.Popen([cmd] +  args.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = p.communicate()
    
    return (p.returncode, out, err)

def num_entries(directory):
    return len([name for name in os.listdir(directory)])

def get_permissions(file):
    return oct(os.stat(file)[stat.ST_MODE])[-3:]
