# -*- mode: python -*-

block_cipher = None


a = Analysis(['aligned_tile_viewer.py'],
             pathex=['C:\\TiaoShiJian\\Sean\\py_workspace\\python_playground\\aligned_tile_viewer\\aligned_tile_viewer'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='aligned_tile_viewer',
          debug=False,
          strip=False,
          upx=True,
          console=False )
