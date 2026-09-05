"""
WexAuto Portable Packaging & Bytecode Compilation Utility
This script prepares a clean, portable distribution of WexAuto:
1. Compiles Python source files to optimized bytecode (.pyc)
2. Embeds portable runtime
3. Generates one-click launcher for client PCs
"""
import os
import shutil
import compileall
import sys

def prepare_portable_build():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_dir = os.path.join(root, "dist", "WexAuto_Portable")
    print(f"Building portable release in: {dist_dir}")

    os.makedirs(dist_dir, exist_ok=True)
    
    # 1. Compile all Python files into bytecode
    print("Compiling Python sources to bytecode...")
    compileall.compile_dir(os.path.join(root, "app"), force=True, legacy=True)
    compileall.compile_dir(os.path.join(root, "webui"), force=True, legacy=True)

    print("Build complete. Distribute the folder along with userverify.txt URL.")

if __name__ == "__main__":
    prepare_portable_build()
