# -*- mode: python -*-

block_cipher = None


a = Analysis(['Velociraptor.py'],
             pathex=['/Users/loic/code/bike'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Velociraptor',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='velociraptor.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Velociraptor')
app = BUNDLE(coll,
             name='Velociraptor.app',
             icon='velociraptor.icns',
             bundle_identifier=None)
