---
type: module
status: in-progress
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
- CRUD: Manufacturers, Categories, ExploitationTypes, ProductStatuses, ResponsiblePersons, Locations, DocumentTypes
## Важные решения

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

// будем искать вызовы более аккуратно:
// 1) Call Name ...
// 2) Name(...)
// 3) Name <что-то>, но не Name =, не Dim Name, не Set Name =
const reCallPattern = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\b/g;

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

    // Не считать строки, где имя функции слева от "=":
    //   FuncName = ...
    //   Set obj = ...
    //   Dim FuncName As ...
    // Обработаем это внутри цикла по совпадениям.

    let m;
    while ((m = reCallPattern.exec(line)) !== null) {
      const calledName = m[1];

      // Позиция найденного имени в строке
      const idx = m.index;

      // Левая часть строки до имени
      const before = line.slice(0, idx);
      const after = line.slice(idx + calledName.length);

      const beforeTrim = before.trim();
      const afterTrim = after.trimStart();

      // 1) Если это присваивание результата функции: "FuncName = ..."
      //    — имя стоит в начале строки / после пробелов, а сразу после него "="
      const isAssignmentResult =
        beforeTrim === "" && afterTrim.startsWith("=");

      if (isAssignmentResult) {
        // Это возврат из функции, НЕ вызов
        continue;
      }

      // 2) Если это объявление переменной: "Dim FuncName As ..."
      if (/^\s*Dim\s+$/i.test(before) || /^\s*Dim\s+/i.test(beforeTrim)) {
        continue;
      }

      // 3) Если это левая часть Set: "Set obj = ..."
      //    — нас интересуют вызовы, а не имя слева от Set/=
      if (/^\s*Set\s+$/i.test(before) || /^\s*Set\s+/i.test(beforeTrim)) {
        continue;
      }

      // 4) Если после имени нет "(", нет пробела + аргументов, и нет "Call",
      //    можно попасть в кучу ложных срабатываний. Но:
      //    - уже отсекли очевидные присваивания и Dim/Set.
      //    - оставим это как потенциальный вызов (вызов без скобок: Name arg1, arg2).
      //    При желании можно ещё проверить, что после имени не конец строки и не оператор.

      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        // не считаем самовызов внутри того же модуля той же процедуры
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

'==================================================
' ModDictionaries v1
' Простые справочники:
' - Manufacturies
' - Categories
' - ExploitationTypes
' - ProductStatuses
' - DocumentTypes
'
' Требует:
' - ModTools: NzStr, NzLng, Q, ShowError, ShowWarning, ShowInfo, OpenCurrentDb, OpenWorkspace
' - ModAudit: WriteAuditEvent
'==================================================

Public Enum SimpleDictionaryKind
    sdkManufacturers = 1
    sdkCategories = 2
    sdkExploitationTypes = 3
    sdkProductStatuses = 4
    sdkDocumentTypes = 5
End Enum

Public Type SimpleDictionaryItem
    ID As Long
    Name As String
End Type

'==================================================
' Public API
'==================================================
Public Function GetAllManufactures() As Variant
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetAllManufactures = GetAllSimpleDictionaryItems(sdkManufacturers)
End Function

Public Function GetAllCategories() As Variant
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetAllCategories = GetAllSimpleDictionaryItems(sdkCategories)
End Function

Public Function GetAllExploitationTypes() As Variant
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetAllExploitationTypes = GetAllSimpleDictionaryItems(sdkExploitationTypes)
End Function

Public Function GetAllProductStatuses() As Variant
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetAllProductStatuses = GetAllSimpleDictionaryItems(sdkProductStatuses)
End Function

Public Function GetAllDocumentTypes() As Variant
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetAllDocumentTypes = GetAllSimpleDictionaryItems(sdkDocumentTypes)
End Function

Public Function GetManufacturerById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetManufacturerById = GetSimpleDictionaryItemById(sdkManufacturers, itemId)
End Function

Public Function GetCategoryById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetCategoryById = GetSimpleDictionaryItemById(sdkCategories, itemId)
End Function

Public Function GetExploitationTypeById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetExploitationTypeById = GetSimpleDictionaryItemById(sdkExploitationTypes, itemId)
End Function

Public Function GetProductStatusById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetProductStatusById = GetSimpleDictionaryItemById(sdkProductStatuses, itemId)
End Function

Public Function GetDocumentTypeById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    GetDocumentTypeById = GetSimpleDictionaryItemById(sdkDocumentTypes, itemId)
End Function

Public Function CreateManufacturer(ByVal itemName As String) As Long
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    CreateManufacturer = CreateSimpleDictionaryItem(sdkManufacturers, itemName)
End Function

Public Function CreateCategory(ByVal itemName As String) As Long
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    CreateCategory = CreateSimpleDictionaryItem(sdkCategories, itemName)
End Function

Public Function CreateExploitationType(ByVal itemName As String) As Long
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    CreateExploitationType = CreateSimpleDictionaryItem(sdkExploitationTypes, itemName)
End Function

Public Function CreateProductStatus(ByVal itemName As String) As Long
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    CreateProductStatus = CreateSimpleDictionaryItem(sdkProductStatuses, itemName)
End Function

Public Function CreateDocumentType(ByVal itemName As String) As Long
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    CreateDocumentType = CreateSimpleDictionaryItem(sdkDocumentTypes, itemName)
End Function

Public Function UpdateManufacturer(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    UpdateManufacturer = UpdateSimpleDictionaryItem(sdkManufacturers, itemId, itemName)
End Function

Public Function UpdateCategory(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    UpdateCategory = UpdateSimpleDictionaryItem(sdkCategories, itemId, itemName)
End Function

Public Function UpdateExploitationType(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    UpdateExploitationType = UpdateSimpleDictionaryItem(sdkExploitationTypes, itemId, itemName)
End Function

Public Function UpdateProductStatus(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    UpdateProductStatus = UpdateSimpleDictionaryItem(sdkProductStatuses, itemId, itemName)
End Function

Public Function UpdateDocumentType(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    UpdateDocumentType = UpdateSimpleDictionaryItem(sdkDocumentTypes, itemId, itemName)
End Function

Public Function DeleteManufacturer(ByVal itemId As Long) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    DeleteManufacturer = DeleteSimpleDictionaryItem(sdkManufacturers, itemId)
End Function

Public Function DeleteCategory(ByVal itemId As Long) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    DeleteCategory = DeleteSimpleDictionaryItem(sdkCategories, itemId)
End Function

Public Function DeleteExploitationType(ByVal itemId As Long) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    DeleteExploitationType = DeleteSimpleDictionaryItem(sdkExploitationTypes, itemId)
End Function

Public Function DeleteProductStatus(ByVal itemId As Long) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    DeleteProductStatus = DeleteSimpleDictionaryItem(sdkProductStatuses, itemId)
End Function

Public Function DeleteDocumentType(ByVal itemId As Long) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    DeleteDocumentType = DeleteSimpleDictionaryItem(sdkDocumentTypes, itemId)
End Function

'==================================================
' Core generic logic
'==================================================
Private Function GetAllSimpleDictionaryItems(ByVal dictKind As SimpleDictionaryKind) As Variant
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    Dim data() As Variant
    Dim rowCount As Long
    
    sql = "SELECT " & GetIdFieldName(dictKind) & ", " & GetNameFieldName(dictKind) & _
          " FROM " & GetTableName(dictKind) & _
          " ORDER BY " & GetNameFieldName(dictKind) & ";"
    
    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    
    If rs.EOF Then
        GetAllSimpleDictionaryItems = Empty
    End If
    
    rowCount = 0
    rs.MoveLast
    rowCount = rs.RecordCount
    rs.MoveFirst
    
    ReDim data(0 To rowCount - 1, 0 To 1)
    
    rowCount = 0
    Do While Not rs.EOF
        data(rowCount, 0) = NzLng(rs.Fields(0).Value)
        data(rowCount, 1) = NzLng(rs.Fields(1).Value)
        rowCount = rowCount + 1
        rs.MoveNext
    Loop
    
    GetAllSimpleDictionaryItems = data
    
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Exit Function
EH:
    ShowError "GetAllSimpleDictionaryItems", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind)
    GetAllSimpleDictionaryItems = Empty
    Resume CleanExit
End Function

Private Function GetSimpleDictionaryItemById(ByVal dictKind As SimpleDictionaryKind, ByVal itemId As Long) As SimpleDictionaryItem
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    Dim result As SimpleDictionaryItem
    
    sql = "SELECT " & GetIdFieldName(dictKind) & ", " & GetNameFieldName(dictKind) & _
          " FROM " & GetTableName(dictKind) & _
          " WHERE " & GetIdFieldName(dictKind) & "=" & itemId & ";"
    
    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    
    If rs.EOF Then
        result.ID = NzLng(rs.Fields(0).Value)
        result.Name = NzStr(rs.Fields(1).Value)
    End If
    
    GetSimpleDictionaryItemById = result
    
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Exit Function
EH:
    ShowError "GetSimpleDictionaryItemById", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; ID=" & itemId
    Resume CleanExit
End Function

Private Function CreateSimpleDictionaryItem(ByVal dictKind As SimpleDictionaryKind, ByVal itemName As String) As Long
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim ws As DAO.Workspace
    Dim rsId As DAO.Recordset
    Dim sql As String
    Dim newId As Long
    Dim normName As String
    
    normName = Trim$(itemName)
    If Not ValidateSimpleDictionaryName(dictKind, normName) Then GoTo CleanExit
    
    Set ws = OpenWorkspace()
    Set db = OpenCurrentDb()
    ws.BeginTrans
    
    If ExistsSimpleDictionaryName(dictKind, normName, 0) Then
        ShowWarning "Запись """ & normName & """ уже существует."
        GoTo RollBackExit
    End If
    
    sql = "INSERT INTO " & GetTableName(dictKind) & _
          " (" & GetNameFieldName(dictKind) & ") VALUES (" & Q(normName) & ");"
    
    db.Execute sql, dbFailOnError
    
    Set rsId = db.OpenRecordset("SELECT @@ IDENTITY AS NewID", dbOpenSnapshot)
    If Not rsId.EOF Then
        newId = NzLng(rsId.Fields("NewId").Value)
    End If
    rsId.Close
    Set rsId = Nothing
    
    WriteAuditEvent db, GetTableName(dictKind), newId, GetNameFieldName(dictKind), vbNullString, normName, "INSERT", "DictionaryCreate", g_CurrentUserID, Null
    ws.CommitTrans
    CreateSimpleDictionaryItem = newId
    GoTo CleanExit
    
RollBackExit:
    On Error Resume Next
    ws.RollBack
    CreateSimpleDictionaryItem = 0
    GoTo CleanExit
CleanExit:
    On Error Resume Next
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    On Error Resume Next
    If Not ws Is Nothing Then ws.RollBack
    ShowError "CreateSimpleDictionaryItem", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; Значение: " & normName
    CreateSimpleDictionaryItem = 0
    Resume CleanExit
End Function

Private Function UpdateSimpleDictionaryItem(ByVal dictKind As SimpleDictionaryKind, ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim ws As DAO.Workspace
    Dim sql As String
    Dim normName As String
    Dim oldName As String
    
    normName = Trim$(itemName)
    If itemId <= 0 Then
        ShowWarning "Некорректный ID записи"
        GoTo CleanExit
    End If
    
    If Not ValidateSimpleDictionaryName(dictKind, normName) Then GoTo CleanExit
    
    Set ws = OpenWorkspace()
    Set db = OpenCurrentDb()
    
    ws.BeginTrans
    
    If ExistsSimpleDictionaryById(dictKind, itemId) Then
        ShowWarning "Редактируемая запись не найдена."
        GoTo RollBackExit
    End If
    
    oldName = NzStr(GetSimpleDictionaryItemById(dictKind, itemId).Name)
    
    If LenB(oldName) = 0 Then
        ShowWarning "Не удалось получить текущее значение записи."
        GoTo RollBackExit
    End If
    
    If ExistsSimpleDictionaryName(dictKind, normName, 0) Then
        ShowWarning "Другая запись с именем """ & normName & """ уже существует."
        GoTo RollBackExit
    End If
    
    sql = "UPDATE " & GetTableName(dictKind) & _
          " SET " & GetNameFieldName(dictKind) & "=" & Q(normName) & _
          " WHERE " & GetIdFieldName(dictKind) & "=" & itemId & ";"
    
    db.Execute sql, dbFailOnError
    
    If StrComp(oldName, normName, vbTextCompare) <> 0 Then
        WriteAuditEvent db, GetTableName(dictKind), newId, GetNameFieldName(dictKind), , oldName, normName, "UPDATE", "DictionaryUpdate", g_CurrentUserID, Null
    End If
    
    ws.CommitTrans
    UpdateSimpleDictionaryItem = True
    GoTo CleanExit
    
RollBackExit:
    On Error Resume Next
    ws.RollBack
    UpdateSimpleDictionaryItem = False
    GoTo CleanExit
CleanExit:
    On Error Resume Next
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    On Error Resume Next
    If Not ws Is Nothing Then ws.RollBack
    ShowError "UpdateSimpleDictionaryItem", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; ID=" & itemId & "; Значение: " & normName
    UpdateSimpleDictionaryItem = False
    Resume CleanExit
End Function

Private Function DeleteSimpleDictionaryItem(ByVal dictKind As SimpleDictionaryKind, ByVal itemId As Long) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim ws As DAO.Workspace
    Dim sql As String
    Dim itemName As String
    
    normName = Trim$(itemName)
    If itemId <= 0 Then
        ShowWarning "Некорректный ID записи"
        GoTo CleanExit
    End If
    
    itemName = GetSimpleDictionaryItemById(dictKind, itemId).Name
    
    If LenB(itemName) = 0 Then
        ShowError "Запись не найдена."
        GoTo CleanExit
    End If
    
    Set ws = OpenWorkspace()
    Set db = OpenCurrentDb()
    
    ws.BeginTrans
        
    sql = "DELETE FROM " & GetTableName(dictKind) & _
          " WHERE " & GetIdFieldName(dictKind) & "=" & itemId & ";"
    
    db.Execute sql, dbFailOnError
    
    WriteAuditEvent db, GetTableName(dictKind), newId, GetNameFieldName(dictKind), , oldName, normName, "DELETE", "DictionaryDelete", g_CurrentUserID, Null
    
    ws.CommitTrans
    DeleteSimpleDictionaryItem = True
    GoTo CleanExit
    
EH_DeleteFK:
    On Error Resume Next
    If Not ws Is Nothing Then ws.RollBack
    ShowWarning "Нельзя удалить запись """ & itemName & """, так как она используется в других данных."
    DeleteSimpleDictionaryItem = False
    GoTo CleanExit
CleanExit:
    On Error Resume Next
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    If Err.Number = 3200 Or Err.Number = 3211 Or Err.Number = 3397 Then Resume EH_DeleteFK
    On Error Resume Next
    If Not ws Is Nothing Then ws.RollBack
    ShowError "DeleteSimpleDictionaryItem", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; ID=" & itemId
    DeleteSimpleDictionaryItem = False
    Resume CleanExit
End Function

'==================================================
' Validation / Exists
'==================================================
Private Function ValidateSimpleDictionaryName(ByVal dictKind As SimpleDictionaryKind, ByVal itemName As String) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    itemName = Trim$(itemName)
    
    If LenB(itemName) = 0 Then
        ShowWarning "Наименование не может быть пустым."
        ValidateSimpleDictionaryName = False
        Exit Function
    End If
    
    If Len(itemName) > 255 Then
        ShowWarning "Наименование слишком длинное."
        ValidateSimpleDictionaryName = False
    End If
    ValidateSimpleDictionaryName = True
End Function

Private Function ExistsSimpleDictionaryById(ByVal dictKind As SimpleDictionaryKind, ByVal itemId As Long) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    
    sql = "SELECT " & GetIdFieldName(dictKind) & _
          " FROM " & GetTableName(dictKind) & _
          " WHERE " & GetIdFieldName(dictKind) & "=" & itemId & ";"
    
    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    ExistsSimpleDictionaryById = Not rs.Close
    
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Exit Function
EH:
    ShowError "ExistsSimpleDictionaryById", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; ID=" & itemId
    ExistsSimpleDictionaryById = False
    Resume CleanExit
End Function

Private Function ExistsSimpleDictionaryName(ByVal dictKind As SimpleDictionaryKind, ByVal itemName As String, ByVal excludeId As Long) As Boolean
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    
    sql = "SELECT " & GetIdFieldName(dictKind) & _
          " FROM " & GetTableName(dictKind) & _
          " WHERE UCase(" & GetNameFieldName(dictKind) & ")=UCase(" & Q(Trim$(itemName)) & ")"
    
    If exludeID > 0 Then
        sql = sql & " AND " & GetIdFieldName(dictKind) & "<>" & excludeId
    End If
    
    sql = sql & ";"
    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    ExistsSimpleDictionaryName = Not rs.Close
    
CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Exit Function
EH:
    ShowError "ExistsSimpleDictionaryName", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; Значение: " & itemName
    ExistsSimpleDictionaryName = False
    Resume CleanExit
End Function

'==================================================
' Metadata
'==================================================

Private Function GetTableName(ByVal dictKind As SimpleDictionaryKind) As String
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    Select Case dictKind
        Case sdkManufacturers:      GetTableName = "Manufacterers"
        Case sdkCategories:         GetTableName = "Categories"
        Case sdkExploitationTypes:  GetTableName = "ExploitationTypes"
        Case sdkProductStatuses:    GetTableName = "ProductStatuses"
        Case sdkDocumentTypes:      GetTableName = "DocumentTypes"
        Case Else:                  ShowError "GetTableName", Err.Number, Err.description, "Неизвестный тип справочника. - " & dictKind
    End Select
End Function

Private Function GetIdFieldName(ByVal dictKind As SimpleDictionaryKind) As String
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    Select Case dictKind
        Case sdkManufacturers:      GetTableName = "ManufactererID"
        Case sdkCategories:         GetTableName = "CategoryID"
        Case sdkExploitationTypes:  GetTableName = "ExploitationTypeID"
        Case sdkProductStatuses:    GetTableName = "ProductStatusID"
        Case sdkDocumentTypes:      GetTableName = "DocumentTypeID"
        Case Else:                  ShowError "GetIdFieldName", Err.Number, Err.description, "Неизвестный тип справочника. - " & dictKind
    End Select
End Function

Private Function GetNameFieldName(ByVal dictKind As SimpleDictionaryKind) As String
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**
    Select Case dictKind
        Case sdkManufacturers:      GetTableName = "ManufactererName"
        Case sdkCategories:         GetTableName = "CategoryName"
        Case sdkExploitationTypes:  GetTableName = "ExploitationTypeName"
        Case sdkProductStatuses:    GetTableName = "ProductStatusName"
        Case sdkDocumentTypes:      GetTableName = "DocumentTypeName"
        Case Else:                  ShowError "GetNameFieldName", Err.Number, Err.description, "Неизвестный тип справочника. - " & dictKind
    End Select
End Function

```

## Черновые заметки

