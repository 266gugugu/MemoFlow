# build.py
# -*- coding: utf-8 -*-
"""
MemoFlow 打包脚本
使用 PyInstaller 将应用打包为 Windows 可执行文件
"""
import os
import sys
import shutil
import subprocess

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ 错误: 需要 Python 3.10+，当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_main_file():
    """检查主文件是否存在"""
    if not os.path.exists('main.py'):
        print("❌ 错误: 找不到 main.py 文件")
        return False
    print("✓ 找到 main.py")
    return True

def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        version = PyInstaller.__version__
        print(f"✓ PyInstaller 已安装，版本: {version}")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        return False

def install_pyinstaller():
    """安装 PyInstaller"""
    print("正在安装 PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("PyInstaller 安装完成！")

def clean_build_dirs():
    """清理之前的构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理 .spec 文件（可选）
    spec_file = 'MemoFlow.spec'
    if os.path.exists(spec_file):
        print(f"清理文件: {spec_file}")
        os.remove(spec_file)

def build_app(debug=False):
    """构建应用"""
    print("\n开始打包 MemoFlow...")
    print("=" * 50)
    
    # PyInstaller 命令参数
    cmd = [
        'pyinstaller',
        '--name=MemoFlow',
        '--onefile',  # 打包为单个可执行文件
        '--windowed',  # 不显示控制台窗口
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--collect-all=PyQt6',  # 收集所有 PyQt6 相关文件
        '--noconfirm',  # 覆盖输出目录而不询问
    ]
    
    # 调试模式：显示详细输出
    if debug:
        cmd.append('--debug=all')
        cmd.append('--log-level=DEBUG')
        print("🔍 调试模式已启用")
    
    # 添加图标（如果存在）
    if os.path.exists('icon.ico'):
        cmd.append('--icon=icon.ico')
        print("✓ 检测到图标文件: icon.ico")
    else:
        print("ℹ 未找到 icon.ico，将使用默认图标")
    
    # 添加数据文件（如果存在）
    data_files = []
    if os.path.exists('settings.json'):
        cmd.append('--add-data=settings.json;.')
        data_files.append('settings.json')
    if os.path.exists('memos.json'):
        cmd.append('--add-data=memos.json;.')
        data_files.append('memos.json')
    
    if data_files:
        print(f"✓ 将包含数据文件: {', '.join(data_files)}")
    
    cmd.append('main.py')
    
    # 显示完整命令（调试用）
    if debug:
        print("\n执行的命令:")
        print(" ".join(cmd))
        print()
    
    try:
        print("\n正在执行 PyInstaller，请稍候...")
        
        # 在 Windows 上处理编码问题
        # 设置环境变量确保使用 UTF-8 编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        if debug:
            # 调试模式：捕获输出以便显示详细信息
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace',  # 遇到编码错误时替换而不是崩溃
                env=env
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        else:
            # 非调试模式：不捕获输出，直接显示到控制台
            # 这样避免编码问题，同时用户可以看到实时进度
            # 设置环境变量确保子进程使用 UTF-8
            result = subprocess.run(cmd, check=True, env=env)
        
        print("\n" + "=" * 50)
        print("✅ 打包成功！")
        exe_path = os.path.abspath('dist/MemoFlow.exe')
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"可执行文件位置: {exe_path}")
            print(f"文件大小: {file_size:.2f} MB")
        else:
            print("⚠ 警告: 未找到生成的可执行文件")
        
        print("\n提示：")
        print("- 首次运行可能需要几秒钟来解压文件")
        print("- 建议将 MemoFlow.exe 放在单独的文件夹中，因为它会在同目录下创建 settings.json 和 memos.json")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败!")
        print(f"错误代码: {e.returncode}")
        if hasattr(e, 'stdout') and e.stdout:
            try:
                print(f"输出:\n{e.stdout}")
            except:
                print("输出: (无法显示，可能包含特殊字符)")
        if hasattr(e, 'stderr') and e.stderr:
            try:
                print(f"错误信息:\n{e.stderr}")
            except:
                print("错误信息: (无法显示，可能包含特殊字符)")
        print("\n💡 提示: 使用 --debug 参数查看详细错误信息")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """主函数"""
    print("MemoFlow 打包工具")
    print("=" * 50)
    
    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查主文件
    if not check_main_file():
        sys.exit(1)
    
    # 检查是否启用调试模式
    debug = '--debug' in sys.argv or '-d' in sys.argv
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        print("\n未检测到 PyInstaller，需要先安装")
        response = input("是否现在安装？(y/n): ").strip().lower()
        if response == 'y':
            install_pyinstaller()
        else:
            print("请先安装 PyInstaller: pip install pyinstaller")
            sys.exit(1)
    
    # 询问是否清理
    if '--no-clean' not in sys.argv:
        response = input("\n是否清理之前的构建文件？(y/n，默认y): ").strip().lower()
        if response != 'n':
            clean_build_dirs()
    
    # 开始构建
    build_app(debug=debug)

if __name__ == "__main__":
    main()

