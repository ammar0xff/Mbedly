Unicode True
Name "Mbedly"
!ifndef OUTFILE
  !define OUTFILE "mbedly-app-windows-setup.exe"
!endif
!ifndef VERSION
  !define VERSION "2.0.0"
!endif
OutFile "${OUTFILE}"
InstallDir "$PROGRAMFILES64\Mbedly"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
VIProductVersion "${VERSION}.0"
VIFileVersion "${VERSION}.0"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "Release\*"
  WriteUninstaller "$INSTDIR\uninstall.exe"
  CreateDirectory "$SMPROGRAMS\Mbedly"
  CreateShortcut "$SMPROGRAMS\Mbedly\Mbedly.lnk" "$INSTDIR\mbedly_app.exe"
  CreateShortcut "$DESKTOP\Mbedly.lnk" "$INSTDIR\mbedly_app.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mbedly" "DisplayName" "Mbedly"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mbedly" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mbedly" "Publisher" "Mbedly"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mbedly" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mbedly" "InstallLocation" "$INSTDIR"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Mbedly.lnk"
  RMDir /r "$SMPROGRAMS\Mbedly"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Mbedly"
SectionEnd