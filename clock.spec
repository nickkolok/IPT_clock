# -*- mode: python -*-

block_cipher = None


a = Analysis(['clock.py'],
             pathex=['/Users/Alberto/Documents/IPT/IPT clock'],
             binaries=[],
             datas=[( 'states.csv', '.'), ('img1.png', '.'), ('img2.png', '.')],
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
          name='clock',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
