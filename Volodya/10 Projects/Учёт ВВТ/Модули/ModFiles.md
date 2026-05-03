---
type: module
status: planned
done_date:
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - module
  - skill/vba
reward_xp: 50
---
# Модуль
## Назначение
- Кратко, за что отвечает модуль, какие задачи решает.
## Важные решения
- Почему выбрана такая архитектура.
- Комментарии по производительности/ограничениям.

## Задачи по модулю

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Взаимосвязи (исходящие вызовы)

```dataviewjs
const TYPES = ['module', 'form', 'class'];

const current = dv.current();
const currentProject = current.project;

if (!currentProject) {
  dv.paragraph('У текущего модуля не заполнено поле project — нечего сканировать.');
  return;
}

const allPages = dv.pages()
  .where(p => TYPES.includes(p.type))
  .where(p => p.project && dv.func.contains(p.project, currentProject))
  .array();

// Диагностика — сохраняем, но не показываем
const debugModulesCount = allPages.length;

async function getVbaBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];

  const blocks = [];
  let inBlock = false;
  let currentBlock = [];

  for (const line of text.split('\n')) {
    const trimmed = line.trim();

    if (!inBlock && trimmed.toLowerCase().startsWith('```vba')) {
      inBlock = true;
      currentBlock = [];
      continue;
    }

    if (inBlock && trimmed.startsWith('```')) {
      inBlock = false;
      blocks.push(currentBlock.join('\n'));
      currentBlock = [];
      continue;
    }

    if (inBlock) currentBlock.push(line);
  }

  return blocks;
}

const reProcDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

const procIndex = {};

for (const page of allPages) {
  const vbaBlocks = await getVbaBlocks(page.file.path);

  for (const block of vbaBlocks) {
    const lines = block.split('\n');

    for (const line of lines) {
      const m = line.match(reProcDecl);
      if (!m) continue;

      const name = m[3];

      if (!procIndex[name]) procIndex[name] = [];
      procIndex[name].push({
        modulePath: page.file.path,
        moduleLink: page.file.link,
        moduleType: page.type
      });
    }
  }
}

// Диагностика — сохраняем, но не показываем
const debugProcNames = Object.keys(procIndex);
const debugProcCount = debugProcNames.length;

const currentBlocks = await getVbaBlocks(current.file.path);

// Вызовы: Foo(...), Call Bar(...)
const reCall = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g;

const callMap = new Map();

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentProc = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith("'")) continue;

    const declMatch = line.match(reProcDecl);
    if (declMatch) {
      currentProc = declMatch[3];
      continue;
    }

    if (!currentProc) continue;

    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        if (t.modulePath === current.file.path && calledName === currentProc) continue;

        const key = `${currentProc}||${t.modulePath}`;
        if (!callMap.has(key)) {
          callMap.set(key, {
            fromProc: currentProc,
            toModuleLink: t.moduleLink,
            calledNames: new Set()
          });
        }

        callMap.get(key).calledNames.add(calledName);
      }
    }
  }
}

const rows = [];

for (const entry of callMap.values()) {
  const calledList = Array.from(entry.calledNames).sort().join(", ");
  rows.push([
    entry.fromProc,
    entry.toModuleLink,
    calledList
  ]);
}

if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/форм/классов в рамках этого проекта не найдено.');
} else {
  dv.table(
    ['Процедура', 'Куда (модуль)', 'Что вызывает'],
    rows
  );
}
```

## Функции и процедуры
```dataviewjs
const page = dv.current();
const text = await dv.io.load(page.file.path);

const vbaBlocks = [];
let inBlock = false;
let current = [];

for (const line of text.split("\n")) {
  if (line.trim().startsWith("```vba")) {
    inBlock = true;
    current = [];
    continue;
  }

  if (inBlock && line.trim().startsWith("```")) {
    inBlock = false;
    vbaBlocks.push(current.join("\n"));
    current = [];
    continue;
  }

  if (inBlock) current.push(line);
}

const reDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;
const reReturnType = /\)\s*As\s+([A-Za-z0-9_\.]+)/i;
const reTag = /^'\s*@([a-zA-Z0-9_]+):\s*(.+)$/i;

const rows = [];

for (const block of vbaBlocks) {
  const lines = block.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(reDecl);
    if (!m) continue;

    const scopeRaw = m[1];
    const kindRaw = m[2];
    const name = m[3];

    const kindLower = String(kindRaw ?? "").toLowerCase();
    const kind = kindLower === "sub" ? "Процедура" : "Функция";
    const scope = scopeRaw ? String(scopeRaw) : "По умолчанию (Public)";

    let j = i;
    while (j < lines.length - 1 && lines[j].trim().endsWith("_")) {
      j++;
    }

    const signatureLines = lines.slice(i, j + 1);
    const signatureText = signatureLines.join(" ");
    const mReturn = signatureText.match(reReturnType);
    const returnType = kind === "Функция" && mReturn ? String(mReturn[1]) : "";

    const tags = {
      desc: "",
      role: "",
      todo: ""
    };

    let k = j + 1;

    while (k < lines.length) {
      const cur = lines[k].trim();

      if (cur === "") {
        k++;
        continue;
      }

      const tagMatch = cur.match(reTag);
      if (!tagMatch) break;

      const tagName = String(tagMatch[1] ?? "").toLowerCase();
      const tagValue = String(tagMatch[2] ?? "").trim();

      if (Object.prototype.hasOwnProperty.call(tags, tagName)) {
        tags[tagName] = tagValue;
      }

      k++;
    }

    rows.push([
      name,
      kind,
      scope,
      returnType,
      tags.desc,
      tags.role,
      tags.todo
    ]);
  }
}

if (rows.length === 0) {
  dv.paragraph("Процедуры и функции в коде не найдены.");
} else {
  dv.table(
    ["Имя", "Тип", "Область", "Возврат", "Описание", "Роль", "TODO"],
    rows
  );
}
```

## Код
```vba
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**

Option Explicit

#If VBA7 Then
    Private Declare PtrSafe Function OpenProcess Lib "kernel32" ( _
        ByVal dwDesiredAccess As Long, _
        ByVal bInheritHandle As Long, _
        ByVal dwProcessId As Long) As LongPtr
    
    Private Declare PtrSafe Function WaitForSingleObject Lib "kernel32" ( _
        ByVal hHandle As LongPtr, _
        ByVal dwMilliseconds As Long) As Long
    
    Private Declare PtrSafe Function CloseHandle Lib "kernel32" ( _
        ByVal hObject As LongPtr) As Long
#Else
    Private Declare Function OpenProcess Lib "kernel32" ( _
        ByVal dwDesiredAccess As Long, _
        ByVal bInheritHandle As Long, _
        ByVal dwProcessId As Long) As Long
    
    Private Declare Function WaitForSingleObject Lib "kernel32" ( _
        ByVal hHandle As Long, _
        ByVal dwMilliseconds As Long) As Long
    
    Private Declare Function CloseHandle Lib "kernel32" ( _
        ByVal hObject As Long) As Long
#End If

Private Const SYNCHRONIZE As Long = &H100000
Private Const INFINITE As Long = &HFFFFFFFF

Private Function ShellAndWait(ByVal CmdLine As String) As Long
    Dim pid As Long
    Dim hProc As LongPtr
    Dim res As Long

    pid = Shell(CmdLine, vbHide)
    If pid = 0 Then Exit Function
    
    hProc = OpenProcess(SYNCHRONIZE, 0, pid)
    If hProc <> 0 Then
        res = WaitForSingleObject(hProc, INFINITE)
        Call CloseHandle(hProc)
    End If
    
    ShellAndWait = res
End Function

' Открытие другого excel файла
Public Sub OpenAnotherExcelFile(filePath As String, fileName As String)
    On Error GoTo ErrorHandler
    Dim AnotherWorkbook As Workbook
    Dim wb As Workbook
    Dim Found As Boolean
    
    For Each wb In ThisWorkbook.Parent.Workbooks
        If wb.name = fileName Then
            Set AnotherWorkbook = wb
            Found = True
            Exit For
        End If
    Next wb
    
    ' Если книга уже открыта, используем существующую
    If Found = True Then
    Else
        ' Открытие другого файла Excel
        Set AnotherWorkbook = Workbooks.Open(filePath)
    End If
    Exit Sub
ErrorHandler:
    ShowError "OpenAnotherExcelFile", Err.Number, Err.description
End Sub

' Создание дерева папок
Public Sub EnsureFolderTreeExists(ByVal DocPath As String, ByVal Path As String)
    Dim fso As Object
    Dim parts() As String
    Dim curPath As String
    Dim i As Long

    Set fso = CreateObject("Scripting.FileSystemObject")
    
    parts = Split(Path, "\")
    curPath = DocPath
    
    For i = 0 To UBound(parts)
        curPath = curPath & "\" & parts(i)
        If Not fso.FolderExists(curPath) Then
            fso.CreateFolder curPath
        End If
    Next i
End Sub


' Получаем путь к 7Zip
Public Function Get7ZipPath() As String
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    ' 64-bit
    If fso.FileExists("C:\Program Files\7-Zip\7z.exe") Then
        Get7ZipPath = "C:\Program Files\7-Zip\7z.exe"
        Exit Function
    End If
    
    ' 32-bit
    If fso.FileExists("C:\Program Files (x86)\7-Zip\7z.exe") Then
        Get7ZipPath = "C:\Program Files (x86)\7-Zip\7z.exe"
        Exit Function
    End If
    
    Get7ZipPath = vbNullString
End Function


' Выбор сканов
Function SelectScanFiles() As Collection
    Dim fd As FileDialog
    Dim i As Long
    Dim col As New Collection
    
    Set fd = Application.FileDialog(msoFileDialogFilePicker)
    
    With fd
        .Title = "Выберите файлы сканов"
        .AllowMultiSelect = True
        .Filters.Clear
        .Filters.Add "Изображения и PDF", "*.pdf;*.jpg;*.jpeg;*.png;*.tif;*.tiff"
        .Filters.Add "Все файлы", "*.*"
        
        If .Show <> 0 Then
            For i = 1 To .SelectedItems.Count
                col.Add .SelectedItems(i)
            Next i
        End If
    End With
    
    Set SelectScanFiles = col
End Function

' Архивирование коллекции файлов
Public Sub ZipFilesWith7Zip(ByVal ZipPath As String, ByVal Files As Collection)
    Dim sevenZip As String
    Dim fso As Object
    Dim i As Long
    Dim filePath As String
    Dim cmd As String
    Dim args As String

    If Files Is Nothing Or Files.Count = 0 Then Exit Sub

    sevenZip = Get7ZipPath()
    If sevenZip = "" Then
        ShowWarning "7-Zip не найден.", vbExclamation
        Exit Sub
    End If

    Set fso = CreateObject("Scripting.FileSystemObject")

    ' удаляем старый архив
    If fso.FileExists(ZipPath) Then fso.DeleteFile ZipPath, True
    ZipPath = fso.GetAbsolutePathName(ZipPath)

    ' собираем список файлов в одну строку аргументов
    For i = 1 To Files.Count
        filePath = CStr(Files(i))
        If fso.FileExists(filePath) Then
            args = args & " """ & filePath & """"
        End If
    Next i

    If Len(args) = 0 Then Exit Sub

    ' "C:\Program Files\7-Zip\7z.exe" a -tzip "zipPath" "file1" "file2" ... -mx5
    cmd = """" & sevenZip & """ a -tzip """ & ZipPath & """" & args & " -mx5"
'    Debug.Print "CMD:", cmd

    ShellAndWait cmd
End Sub

' Итоговая процедура архивирования сканов
Public Function ArchiveScansWith7Zip( _
    ByVal ProductFolderName As String, _
    ByVal ArchiveName As String) As String

    Dim DOC_ROOT As String
    
    If SRV_LOC = False Then
        DOC_ROOT = LOCAL_DOC
    Else
        DOC_ROOT = SERVER_DOC
    End If
    
    Dim Files As Collection
    Dim productFolder As String
    Dim ZipPath As String
    Dim fso As Object
    Dim i As Long
    Dim filePath As String

    Set Files = SelectScanFiles()
    If Files Is Nothing Or Files.Count = 0 Then Exit Function

    Set fso = CreateObject("Scripting.FileSystemObject")

    productFolder = DOC_ROOT & ProductFolderName
    EnsureFolderTreeExists DOC_ROOT, ProductFolderName


    ZipPath = productFolder & "\" & ArchiveName & ".zip"

    ZipFilesWith7Zip ZipPath, Files

    ' проверяем, что архив создан и не пустой
    If Not fso.FileExists(ZipPath) Then
        ShowWarning "Архив не создан: " & ZipPath, vbExclamation
        Exit Function
    End If
    If fso.GetFile(ZipPath).Size = 0 Then
        ShowWarning "Архив пустой: " & ZipPath, vbExclamation
        Exit Function
    End If

    ' удаляем исходные файлы
    For i = 1 To Files.Count
        filePath = CStr(Files(i))
        If fso.FileExists(filePath) Then
            fso.DeleteFile filePath, True
        End If
    Next i
End Function

Sub TestArchive()
    ArchiveScansWith7Zip "INV_12345", "Паспорт_2026-04-12"
End Sub
```

## Черновые заметки

