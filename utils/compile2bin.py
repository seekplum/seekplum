import os
import subprocess

current_folder = os.path.dirname(os.path.abspath(__file__))
os_python = "/usr/bin/python"
compiler = os.path.join(current_folder, "pkgpy.py")


def compile2bin(file_list):
    for file_path in file_list:
        bin_file = os.path.splitext(file_path)[0]
        cmd = "%s %s %s %s" % (os_python, compiler, file_path, bin_file)
        print(cmd)
        subprocess.call(cmd, shell=True)
        os.remove("%s.c" % bin_file)
        # os.remove("%s.py" % bin_file)
        os.remove("%s.pyc" % bin_file)


def main():
    file_list = ["test_prn.py"]
    compile2bin(file_list)


if __name__ == "__main__":
    main()
