---
type: module
status: done
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - module
  - skill/vba
reward_xp: 50
---

# ModTools (Модуль)

## Назначение

Модуль

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
// Какие типы считаем VBA-кодом
const TYPES = ['module', 'form', 'class'];

// Проект текущего модуля (ссылка)
const current = dv.current();
const currentProject = current.project;

if (!currentProject) {
  dv.paragraph('У текущего модуля не заполнено поле project — нечего сканировать.');
  return;
}

// Фильтруем только те страницы, у которых такой же project
// p.project может быть ссылкой или массивом ссылок, поэтому используем dv.func.contains
const allPages = dv.pages()
  .where(p => TYPES.includes(p.type))
  .where(p => p.project && dv.func.contains(p.project, currentProject));

// === Функция: вытащить все VBA-блоки ```vba из файла ===
async function getVbaBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];

  const blocks = [];
  let inBlock = false;
  let currentBlock = [];

  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!inBlock && trimmed.startsWith('```vba')) {
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

// Регэксп объявления процедур / функций (как в твоём шаблоне)
const reProcDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

// Индекс: имя процедуры → список мест, где она объявлена
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

// === Анализируем текущий модуль: кто кого вызывает ===

const currentBlocks = await getVbaBlocks(current.file.path);

// Вызовы: Foo(...), Call Bar(...)
const reCall = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g;

const rows = [];

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentProc = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // пропускаем комментарии
    if (trimmed.startsWith("'")) continue;

    // новая процедура / функция
    const declMatch = line.match(reProcDecl);
    if (declMatch) {
      currentProc = declMatch[3];
      continue;
    }

    if (!currentProc) continue;

    // ищем вызовы
    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        // если не хочешь самовызовы — можно фильтрануть
        if (t.modulePath === current.file.path && calledName === currentProc) continue;

        rows.push([
          current.file.link,   // Откуда (модуль)
          currentProc,         // Какая процедура
          t.moduleLink,        // Куда (модуль)
          calledName           // Что вызывает
        ]);
      }
    }
  }
}

if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/форм/классов в рамках этого проекта не найдено.');
} else {
  dv.table(
    ['Откуда (модуль)', 'Процедура', 'Куда (модуль)', 'Что вызывает'],
    rows
  );
}
```

# Функции и процедуры
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

const re = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

const rows = [];

for (const block of vbaBlocks) {
  const lines = block.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(re);
    if (!m) continue;

    const scopeRaw = m[1];               // Public / Private / undefined
    const kindRaw = m[2];                // Sub / Function
    const name = m[3];

    const kind = kindRaw.toLowerCase() === "sub" ? "Процедура" : "Функция";
    const scope = scopeRaw
      ? scopeRaw                       // "Public" или "Private"
      : "По умолчанию (Public)";       // ничего не указано → Public[web:369][web:375]

    let desc = "";
    if (i + 1 < lines.length) {
      const next = lines[i + 1].trim();
      const mDesc = next.match(/^'\s*@desc:\s*(.+)$/i);
      if (mDesc) desc = mDesc[1];
    }

    rows.push([name, kind, scope, desc]);
  }
}

if (rows.length === 0) {
  dv.paragraph("Процедуры и функции в коде не найдены.");
} else {
  dv.table(["Имя", "Тип", "Область", "Описание"], rows);
}
```
# Код
```vba
Option Explicit

' Функция изменения значений констант
' Для числовых констант
'       ChangeConstantInModSettings "MAX_COUNT", 100
' Для строковых констант
'       ChangeConstantInModSettings "DEFAULT_NAME", "Новое значение"
' Для дат
'       ChangeConstantInModSettings "START_DATE", #12/31/2023#
' Для булевых значений
'       ChangeConstantInModSettings "ENABLE_FEATURE", True
Sub ChangeConstantInModSettings(constantName As String, newValue As Variant)
    ' @desc: Изменение значений констант
    On Error GoTo ErrorHandler
    ' Получаем доступ к VBProject через CreateObject
    Dim vbProj As Object
    Set vbProj = ThisWorkbook.VBProject
    
    Dim vbComp As Object
    Dim codeMod As Object
    Dim i As Long
    Dim lineText As String
    Dim Found As Boolean
    Dim constLine As Long
    Dim constType As String
    Dim oldValue As String
    
    ' Ищем модуль ModSettings
    For Each vbComp In vbProj.VBComponents
        If vbComp.name = "ModSettings" Then
            Set codeMod = vbComp.CodeModule
            
            ' Ищем константу в коде модуля
            For i = 1 To codeMod.CountOfLines
                lineText = codeMod.lines(i, 1)
                
                ' Проверяем, является ли строка объявлением константы
                If InStr(1, lineText, "Const " & constantName & " ", vbTextCompare) > 0 Then
                    constLine = i
                    
                    ' Определяем тип константы
                    If InStr(lineText, " As ") > 0 Then
                        constType = Split(Split(lineText, " As ")(1), " ")(0)
                        constType = Replace(constType, "=", "")
                        constType = Trim(constType)
                    Else
                        constType = "Variant"
                    End If
                    
                    ' Извлекаем текущее значение
                    oldValue = Split(Split(lineText, "=")(1), "'")(0)
                    oldValue = Trim(oldValue)
                    
                    ' Форматируем новое значение в зависимости от типа
                    Dim formattedValue As String
                    Select Case LCase(constType)
                        Case "string", "str"
                            formattedValue = """" & CStr(newValue) & """"
                        Case "integer", "long", "byte", "boolean"
                            formattedValue = CStr(newValue)
                        Case "single", "double", "currency", "decimal"
                            formattedValue = Replace(CStr(newValue), ",", ".")
'                        Case "date"
'                            formattedValue = "#" & Format(newValue, "yyyy-mm-dd hh:mm:ss") & "#"
                        Case Else
                            formattedValue = CStr(newValue)
                    End Select
                    
                    ' Заменяем строку с константой
                    Dim newLine As String
                    newLine = Left(lineText, InStr(lineText, "=")) & " " & formattedValue
                    
                    ' Сохраняем комментарий, если он есть
                    If InStr(lineText, "'") > InStr(lineText, "=") Then
                        newLine = newLine & " " & Mid(lineText, InStr(lineText, "'"))
                    End If
                    
                    codeMod.ReplaceLine constLine, newLine
                    Found = True
                    Exit For
                End If
            Next i
            
            Exit For
        End If
    Next vbComp
    
ErrorHandler:
    ShowError "ChangeConstantInModSettings", Err.Number, Err.description
End Sub

Public Function Q(ByVal s As String) As String
	' @desc: Обёртка текста в запрос
    Q = "'" & Replace$(NzStr(s), "'", "''") & "'"
End Function

Public Function NzStr(ByVal v As Variant, Optional ByVal defaultValue As String = "") As String
	' @desc: Ф
    If IsNull(v) Or IsEmpty(v) Then
        NzStr = defaultValue
    Else
        NzStr = CStr(v)
    End If
End Function

Public Function NzLng(ByVal v As Variant, Optional ByVal defaultValue As Long = 0) As Long
    If IsNull(v) Or IsEmpty(v) Or v = "" Then
        NzLng = defaultValue
    Else
        NzLng = CLng(v)
    End If
End Function

Public Function NzDate(ByVal v As Variant, Optional ByVal def As Date = 0) As Date
    If IsNull(v) Or IsEmpty(v) Or v = "" Then
        NzDate = def
    Else
        NzDate = CDate(v)
    End If
End Function

Public Function NzBool(ByVal v As Variant, Optional ByVal defaultValue As Boolean = False) As Boolean
    If IsNull(v) Or IsEmpty(v) Or v = "" Then
        NzBool = defaultValue
    Else
        NzBool = CBool(v)
    End If
End Function

Public Function BoolToText(ByVal b As Boolean) As String
    If b Then BoolToText = "True" Else BoolToText = "False"
End Function

Public Function QuoteSql(ByVal s As Variant) As String
    If IsNull(s) Or IsEmpty(s) Then
        QuoteSql = "NULL"
    Else
        Dim txt As String
        txt = CStr(s)
        txt = Replace(txt, "'", "''")
        QuoteSql = "'" & txt & "'"
    End If
End Function

Public Function IsMissingOrNull(ByVal v As Variant) As Boolean
    If IsMissing(v) Then
        IsMissingOrNull = True
    ElseIf IsNull(v) Then
        IsMissingOrNull = True
    ElseIf VarType(v) = vbString And vbArray = "" Then
        IsMissingOrNull = True
    Else
        IsMissingOrNull = False
    End If
End Function

Public Function Transpose2D(ByVal src As Variant) As Variant
    Dim r1 As Long, r2 As Long
    Dim c1 As Long, c2 As Long
    Dim r As Long, c As Long
    Dim dst As Variant
    
    If Not IsArray(src) Then
        Transpose2D = src
        Exit Function
    End If
    
    r1 = LBound(src, 1)
    r2 = UBound(src, 1)
    c1 = LBound(src, 2)
    c2 = UBound(src, 2)
    
    ReDim dst(c1 To c2, r1 To r2)
    
    For r = r1 To r2
        For c = c1 To c2
            dst(c, r) = src(r, c)
        Next c
    Next r
    Transpose2D = dst
End Function

Public Function BoolToSql(ByVal v As Boolean) As String
    If v Then
        BoolToSql = "True"
    Else
        BoolToSql = "False"
    End If
End Function

Public Sub ShowError(ByVal ProcName As String, _
                     Optional ByVal ErrNum As Long = 0, _
                     Optional ByVal ErrDesc As String = "", _
                     Optional ByVal ExtraInfo As String = "")
                     
    Dim s As String
    
    If ErrNum = 0 Then ErrNum = Err.Number
    If LenB(ErrDesc) = 0 Then ErrDesc = Err.description
    
    s = "Ошибка в процедуре: " & ProcName & vbCrLf & _
        "Код ошибки: " & CStr(ErrNum) & vbCrLf & _
        "Описание: " & ErrDesc
    
    If LenB(ExtraInfo) > 0 Then
        s = s & vbCrLf & vbCrLf & "Дополнительно: " & vbCrLf & ExtraInfo
    End If
    s = s & vbCrLf & "Пожалуйста пометьте и передайте разработчику!"
    
    MsgBox s, vbCritical, "Ошибка!"
End Sub

Public Sub ShowWarning(ByVal MsgText As String, Optional ByVal Title As String = "Предупреждение")
    MsgBox MsgText, vbExclamation, Title
End Sub

Public Sub ShowInfo(ByVal MsgText As String, Optional ByVal Title As String = "Информация")
    MsgBox MsgText, vbInformation, Title
End Sub

' ==============================================
' DB helpers
' ==============================================
Public Function GetDbPath() As String
    If SRV_LOC = False Then
        GetDbPath = LOCAL_BASE
    Else
        GetDbPath = SERVER_BASE
    End If
End Function

Public Function OpenCurrentDb() As DAO.Database
    Set OpenCurrentDb = DBEngine.Workspaces(0).OpenDatabase(GetDbPath())
End Function

Public Function OpenWorkspace() As DAO.Workspace
    Set OpenWorkspace = DBEngine.Workspaces(0)
End Function

```

## Черновые заметки

