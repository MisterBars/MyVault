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
' @desc: Управление простыми справочниками (CRUD) + часть сложных (ответственные, локации)
' @role: Data Access / Dictionaries
' @todo: При необходимости расширить поля для ResponsiblePersons/Locations

Option Explicit

'==================================================
' ModDictionaries v2
' Простые справочники:
' - Manufacturers
' - Categories
' - ExploitationTypes
' - ProductStatuses
' - DocumentTypes
'
' Справочники со сложной структурой (ядро):
' - ResponsiblePersons (пока только ID+FullName для общего UI)
' - Locations (пока только ID+LocationName для общего UI)
'
' Требует:
' - ModTools: NzStr, NzLng, Q, ShowError, ShowWarning, ShowInfo, OpenCurrentDb, OpenWorkspace
' - ModAudit: WriteAuditEvent
' - ModSession: g_CurrentUserID
'==================================================

Public Enum SimpleDictionaryKind
    sdkManufacturers = 1
    sdkCategories = 2
    sdkExploitationTypes = 3
    sdkProductStatuses = 4
    sdkDocumentTypes = 5
    sdkResponsiblePersons = 6
    sdkLocations = 7
End Enum

Public Type SimpleDictionaryItem
    ID As Long
    Name As String
End Type

'==================================================
' Public API: простые справочники
'==================================================

Public Function GetAllManufacturers() As Variant
' @desc: Возвращает все записи справочника производителей в виде массива ID+Name.
' @role: Query
' @todo: --
    GetAllManufacturers = GetAllSimpleDictionaryItems(sdkManufacturers)
End Function

Public Function GetAllCategories() As Variant
' @desc: Возвращает все записи справочника категорий в виде массива ID+Name.
' @role: Query
' @todo: --
    GetAllCategories = GetAllSimpleDictionaryItems(sdkCategories)
End Function

Public Function GetAllExploitationTypes() As Variant
' @desc: Возвращает все записи справочника типов эксплуатации в виде массива ID+Name.
' @role: Query
' @todo: --
    GetAllExploitationTypes = GetAllSimpleDictionaryItems(sdkExploitationTypes)
End Function

Public Function GetAllProductStatuses() As Variant
' @desc: Возвращает все записи справочника статусов изделий в виде массива ID+Name.
' @role: Query
' @todo: --
    GetAllProductStatuses = GetAllSimpleDictionaryItems(sdkProductStatuses)
End Function

Public Function GetAllDocumentTypes() As Variant
' @desc: Возвращает все записи справочника типов документов в виде массива ID+Name.
' @role: Query
' @todo: --
    GetAllDocumentTypes = GetAllSimpleDictionaryItems(sdkDocumentTypes)
End Function

Public Function GetManufacturerById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: Загружает одного производителя по ID в типизированную структуру.
' @role: Query
' @todo: --
    GetManufacturerById = GetSimpleDictionaryItemById(sdkManufacturers, itemId)
End Function

Public Function GetCategoryById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: Загружает одну категорию по ID в типизированную структуру.
' @role: Query
' @todo: --
    GetCategoryById = GetSimpleDictionaryItemById(sdkCategories, itemId)
End Function

Public Function GetExploitationTypeById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: Загружает один тип эксплуатации по ID в типизированную структуру.
' @role: Query
' @todo: --
    GetExploitationTypeById = GetSimpleDictionaryItemById(sdkExploitationTypes, itemId)
End Function

Public Function GetProductStatusById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: Загружает один статус изделия по ID в типизированную структуру.
' @role: Query
' @todo: --
    GetProductStatusById = GetSimpleDictionaryItemById(sdkProductStatuses, itemId)
End Function

Public Function GetDocumentTypeById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: Загружает один тип документа по ID в типизированную структуру.
' @role: Query
' @todo: --
    GetDocumentTypeById = GetSimpleDictionaryItemById(sdkDocumentTypes, itemId)
End Function

Public Function CreateManufacturer(ByVal itemName As String) As Long
' @desc: Создаёт нового производителя и возвращает его ID.
' @role: Sync
' @todo: --
    CreateManufacturer = CreateSimpleDictionaryItem(sdkManufacturers, itemName)
End Function

Public Function CreateCategory(ByVal itemName As String) As Long
' @desc: Создаёт новую категорию и возвращает её ID.
' @role: Sync
' @todo: --
    CreateCategory = CreateSimpleDictionaryItem(sdkCategories, itemName)
End Function

Public Function CreateExploitationType(ByVal itemName As String) As Long
' @desc: Создаёт новый тип эксплуатации и возвращает его ID.
' @role: Sync
' @todo: --
    CreateExploitationType = CreateSimpleDictionaryItem(sdkExploitationTypes, itemName)
End Function

Public Function CreateProductStatus(ByVal itemName As String) As Long
' @desc: Создаёт новый статус изделия и возвращает его ID.
' @role: Sync
' @todo: --
    CreateProductStatus = CreateSimpleDictionaryItem(sdkProductStatuses, itemName)
End Function

Public Function CreateDocumentType(ByVal itemName As String) As Long
' @desc: Создаёт новый тип документа и возвращает его ID.
' @role: Sync
' @todo: --
    CreateDocumentType = CreateSimpleDictionaryItem(sdkDocumentTypes, itemName)
End Function

Public Function UpdateManufacturer(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: Обновляет имя производителя по ID.
' @role: Sync
' @todo: --
    UpdateManufacturer = UpdateSimpleDictionaryItem(sdkManufacturers, itemId, itemName)
End Function

Public Function UpdateCategory(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: Обновляет имя категории по ID.
' @role: Sync
' @todo: --
    UpdateCategory = UpdateSimpleDictionaryItem(sdkCategories, itemId, itemName)
End Function

Public Function UpdateExploitationType(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: Обновляет имя типа эксплуатации по ID.
' @role: Sync
' @todo: --
    UpdateExploitationType = UpdateSimpleDictionaryItem(sdkExploitationTypes, itemId, itemName)
End Function

Public Function UpdateProductStatus(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: Обновляет имя статуса изделия по ID.
' @role: Sync
' @todo: --
    UpdateProductStatus = UpdateSimpleDictionaryItem(sdkProductStatuses, itemId, itemName)
End Function

Public Function UpdateDocumentType(ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: Обновляет имя типа документа по ID.
' @role: Sync
' @todo: --
    UpdateDocumentType = UpdateSimpleDictionaryItem(sdkDocumentTypes, itemId, itemName)
End Function

Public Function DeleteManufacturer(ByVal itemId As Long) As Boolean
' @desc: Удаляет производителя по ID с учётом ограничений.
' @role: Sync
' @todo: --
    DeleteManufacturer = DeleteSimpleDictionaryItem(sdkManufacturers, itemId)
End Function

Public Function DeleteCategory(ByVal itemId As Long) As Boolean
' @desc: Удаляет категорию по ID с учётом ограничений.
' @role: Sync
' @todo: --
    DeleteCategory = DeleteSimpleDictionaryItem(sdkCategories, itemId)
End Function

Public Function DeleteExploitationType(ByVal itemId As Long) As Boolean
' @desc: Удаляет тип эксплуатации по ID с учётом ограничений.
' @role: Sync
' @todo: --
    DeleteExploitationType = DeleteSimpleDictionaryItem(sdkExploitationTypes, itemId)
End Function

Public Function DeleteProductStatus(ByVal itemId As Long) As Boolean
' @desc: Удаляет статус изделия по ID с учётом ограничений.
' @role: Sync
' @todo: --
    DeleteProductStatus = DeleteSimpleDictionaryItem(sdkProductStatuses, itemId)
End Function

Public Function DeleteDocumentType(ByVal itemId As Long) As Boolean
' @desc: Удаляет тип документа по ID с учётом ограничений.
' @role: Sync
' @todo: --
    DeleteDocumentType = DeleteSimpleDictionaryItem(sdkDocumentTypes, itemId)
End Function

'==================================================
' Public API: ResponsiblePersons / Locations (как простые словари Name)
'==================================================

Public Function GetAllResponsiblePersons() As Variant
' @desc: Возвращает всех ответственных лиц как ID+FullName (IsActive=True).
' @role: Query
' @todo: При необходимости добавить фильтрацию/сортировку по должности.
    GetAllResponsiblePersons = GetAllSimpleDictionaryItems(sdkResponsiblePersons)
End Function

Public Function GetAllLocations() As Variant
' @desc: Возвращает все локации как ID+LocationName.
' @role: Query
' @todo: Позже возможно ограничить по IsActive/иерархии.
    GetAllLocations = GetAllSimpleDictionaryItems(sdkLocations)
End Function

Public Function GetResponsiblePersonById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: Возвращает ответственное лицо по ID (ID+FullName).
' @role: Query
' @todo: При необходимости расширить до отдельного типа с полями телефонов.
    GetResponsiblePersonById = GetSimpleDictionaryItemById(sdkResponsiblePersons, itemId)
End Function

Public Function GetLocationById(ByVal itemId As Long) As SimpleDictionaryItem
' @desc: Возвращает локацию по ID (ID+LocationName).
' @role: Query
' @todo: При необходимости расширить до отдельного типа с кодом/иерархией.
    GetLocationById = GetSimpleDictionaryItemById(sdkLocations, itemId)
End Function

Public Function CreateResponsiblePerson(ByVal fullName As String) As Long
' @desc: Создаёт ответственное лицо (только FullName) и возвращает ID.
' @role: Sync
' @todo: Позже добавить заполнение должности/телефонов отдельным UI.
    CreateResponsiblePerson = CreateSimpleDictionaryItem(sdkResponsiblePersons, fullName)
End Function

Public Function CreateLocation(ByVal locationName As String) As Long
' @desc: Создаёт локацию (только LocationName) и возвращает ID.
' @role: Sync
' @todo: Позже добавить ParentLocationID/RespPersonID в отдельном модуле.
    CreateLocation = CreateSimpleDictionaryItem(sdkLocations, locationName)
End Function

Public Function UpdateResponsiblePerson(ByVal itemId As Long, ByVal fullName As String) As Boolean
' @desc: Обновляет имя ответственного лица (FullName) по ID.
' @role: Sync
' @todo: --
    UpdateResponsiblePerson = UpdateSimpleDictionaryItem(sdkResponsiblePersons, itemId, fullName)
End Function

Public Function UpdateLocation(ByVal itemId As Long, ByVal locationName As String) As Boolean
' @desc: Обновляет название локации (LocationName) по ID.
' @role: Sync
' @todo: --
    UpdateLocation = UpdateSimpleDictionaryItem(sdkLocations, itemId, locationName)
End Function

Public Function DeleteResponsiblePerson(ByVal itemId As Long) As Boolean
' @desc: Удаляет ответственное лицо по ID.
' @role: Sync
' @todo: Проверить, нет ли ссылок из Products/Locations/других таблиц.
    DeleteResponsiblePerson = DeleteSimpleDictionaryItem(sdkResponsiblePersons, itemId)
End Function

Public Function DeleteLocation(ByVal itemId As Long) As Boolean
' @desc: Удаляет локацию по ID.
' @role: Sync
' @todo: Проверить, нет ли ссылок из Products/InventoryOrders/InventoryItems.
    DeleteLocation = DeleteSimpleDictionaryItem(sdkLocations, itemId)
End Function

'==================================================
' Core generic logic
'==================================================

Private Function GetAllSimpleDictionaryItems(ByVal dictKind As SimpleDictionaryKind) As Variant
' @desc: Возвращает массив ID+Name для заданного справочника.
' @role: Query
' @todo: При необходимости добавить фильтрацию по IsActive.
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    Dim data() As Variant
    Dim rowCount As Long
    Dim i As Long
    
    sql = "SELECT " & GetIdFieldName(dictKind) & ", " & GetNameFieldName(dictKind) & _
          " FROM " & GetTableName(dictKind)
    
    ' Специальный фильтр для Active-строк, если нужно
    If dictKind = sdkResponsiblePersons Then
        sql = sql & " WHERE IsActive=True"
    End If
    
    sql = sql & " ORDER BY " & GetNameFieldName(dictKind) & ";"
    
    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    
    If rs.EOF Then
        GetAllSimpleDictionaryItems = Empty
        GoTo CleanExit
    End If
    
    rs.MoveLast
    rowCount = rs.RecordCount
    rs.MoveFirst
    
    ReDim data(0 To rowCount - 1, 0 To 1)
    
    i = 0
    Do While Not rs.EOF
        data(i, 0) = NzLng(rs.Fields(0).Value)
        data(i, 1) = NzStr(rs.Fields(1).Value)
        i = i + 1
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
' @desc: Возвращает SimpleDictionaryItem по ID из указанного справочника.
' @role: Query
' @todo: --
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
    
    If Not rs.EOF Then
        result.ID = NzLng(rs.Fields(0).Value)
        result.Name = NzStr(rs.Fields(1).Value)
    Else
        result.ID = 0
        result.Name = vbNullString
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
' @desc: Создаёт запись в таблице справочника в транзакции и пишет аудит.
' @role: Sync
' @todo: При необходимости расширить для сложных таблиц с несколькими полями.
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
    
    Set rsId = db.OpenRecordset("SELECT @@IDENTITY AS NewID", dbOpenSnapshot)
    If Not rsId.EOF Then
        newId = NzLng(rsId.Fields("NewID").Value)
    End If
    rsId.Close
    Set rsId = Nothing
    
    WriteAuditEvent db, GetTableName(dictKind), newId, GetNameFieldName(dictKind), _
                    vbNullString, normName, "INSERT", "DictionaryCreate", g_CurrentUserID, Null
    ws.CommitTrans
    CreateSimpleDictionaryItem = newId
    GoTo CleanExit
    
RollBackExit:
    On Error Resume Next
    ws.Rollback
    CreateSimpleDictionaryItem = 0
    GoTo CleanExit
CleanExit:
    On Error Resume Next
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    On Error Resume Next
    If Not ws Is Nothing Then ws.Rollback
    ShowError "CreateSimpleDictionaryItem", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; Значение: " & normName
    CreateSimpleDictionaryItem = 0
    Resume CleanExit
End Function

Private Function UpdateSimpleDictionaryItem(ByVal dictKind As SimpleDictionaryKind, ByVal itemId As Long, ByVal itemName As String) As Boolean
' @desc: Обновляет имя записи справочника в транзакции с проверками и аудитом.
' @role: Sync
' @todo: При необходимости добавить проверку записи на изменения по другим полям.
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim ws As DAO.Workspace
    Dim sql As String
    Dim normName As String
    Dim oldName As String
    
    normName = Trim$(itemName)
    If itemId <= 0 Then
        ShowWarning "Некорректный ID записи."
        GoTo CleanExit
    End If
    
    If Not ValidateSimpleDictionaryName(dictKind, normName) Then GoTo CleanExit
    
    Set ws = OpenWorkspace()
    Set db = OpenCurrentDb()
    
    ws.BeginTrans
    
    If Not ExistsSimpleDictionaryById(dictKind, itemId) Then
        ShowWarning "Редактируемая запись не найдена."
        GoTo RollBackExit
    End If
    
    oldName = NzStr(GetSimpleDictionaryItemById(dictKind, itemId).Name)
    
    If LenB(oldName) = 0 Then
        ShowWarning "Не удалось получить текущее значение записи."
        GoTo RollBackExit
    End If
    
    If ExistsSimpleDictionaryName(dictKind, normName, itemId) Then
        ShowWarning "Другая запись с именем """ & normName & """ уже существует."
        GoTo RollBackExit
    End If
    
    sql = "UPDATE " & GetTableName(dictKind) & _
          " SET " & GetNameFieldName(dictKind) & "=" & Q(normName) & _
          " WHERE " & GetIdFieldName(dictKind) & "=" & itemId & ";"
    
    db.Execute sql, dbFailOnError
    
    If StrComp(oldName, normName, vbTextCompare) <> 0 Then
        WriteAuditEvent db, GetTableName(dictKind), itemId, GetNameFieldName(dictKind), _
                        oldName, normName, "UPDATE", "DictionaryUpdate", g_CurrentUserID, Null
    End If
    
    ws.CommitTrans
    UpdateSimpleDictionaryItem = True
    GoTo CleanExit
    
RollBackExit:
    On Error Resume Next
    ws.Rollback
    UpdateSimpleDictionaryItem = False
    GoTo CleanExit
CleanExit:
    On Error Resume Next
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    On Error Resume Next
    If Not ws Is Nothing Then ws.Rollback
    ShowError "UpdateSimpleDictionaryItem", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; ID=" & itemId & "; Значение: " & normName
    UpdateSimpleDictionaryItem = False
    Resume CleanExit
End Function

Private Function DeleteSimpleDictionaryItem(ByVal dictKind As SimpleDictionaryKind, ByVal itemId As Long) As Boolean
' @desc: Удаляет запись справочника в транзакции, обрабатывая FK-ошибки и аудит.
' @role: Sync
' @todo: Для сложных сущностей можно позже заменить на soft-delete.
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim ws As DAO.Workspace
    Dim sql As String
    Dim itemName As String
    
    If itemId <= 0 Then
        ShowWarning "Некорректный ID записи."
        GoTo CleanExit
    End If
    
    itemName = NzStr(GetSimpleDictionaryItemById(dictKind, itemId).Name)
    
    If LenB(itemName) = 0 Then
        ShowWarning "Запись не найдена."
        GoTo CleanExit
    End If
    
    Set ws = OpenWorkspace()
    Set db = OpenCurrentDb()
    
    ws.BeginTrans
    
    sql = "DELETE FROM " & GetTableName(dictKind) & _
          " WHERE " & GetIdFieldName(dictKind) & "=" & itemId & ";"
    
    db.Execute sql, dbFailOnError
    
    WriteAuditEvent db, GetTableName(dictKind), itemId, GetNameFieldName(dictKind), _
                    itemName, vbNullString, "DELETE", "DictionaryDelete", g_CurrentUserID, Null
    
    ws.CommitTrans
    DeleteSimpleDictionaryItem = True
    GoTo CleanExit
    
EH_DeleteFK:
    On Error Resume Next
    If Not ws Is Nothing Then ws.Rollback
    ShowWarning "Нельзя удалить запись """ & itemName & """, так как она используется в других данных."
    DeleteSimpleDictionaryItem = False
    GoTo CleanExit
CleanExit:
    On Error Resume Next
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    If Err.Number = 3200 Or Err.Number = 3211 Or Err.Number = 3397 Then
        Resume EH_DeleteFK
    End If
    On Error Resume Next
    If Not ws Is Nothing Then ws.Rollback
    ShowError "DeleteSimpleDictionaryItem", Err.Number, Err.description, _
              "Таблица: " & GetTableName(dictKind) & "; ID=" & itemId
    DeleteSimpleDictionaryItem = False
    Resume CleanExit
End Function

'==================================================
' Validation / Exists
'==================================================

Private Function ValidateSimpleDictionaryName(ByVal dictKind As SimpleDictionaryKind, ByVal itemName As String) As Boolean
' @desc: Проверяет непустое и не слишком длинное имя для записи справочника.
' @role: Validation
' @todo: При необходимости добавить специфические ограничения по справочникам.
    itemName = Trim$(itemName)
    
    If LenB(itemName) = 0 Then
        ShowWarning "Наименование не может быть пустым."
        ValidateSimpleDictionaryName = False
        Exit Function
    End If
    
    If Len(itemName) > 255 Then
        ShowWarning "Наименование слишком длинное."
        ValidateSimpleDictionaryName = False
        Exit Function
    End If
    
    ValidateSimpleDictionaryName = True
End Function

Private Function ExistsSimpleDictionaryById(ByVal dictKind As SimpleDictionaryKind, ByVal itemId As Long) As Boolean
' @desc: Проверяет, существует ли запись с данным ID в таблице справочника.
' @role: Validation
' @todo: ---
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    
    sql = "SELECT " & GetIdFieldName(dictKind) & _
          " FROM " & GetTableName(dictKind) & _
          " WHERE " & GetIdFieldName(dictKind) & "=" & itemId & ";"
    
    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    ExistsSimpleDictionaryById = Not rs.EOF
    
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
' @desc: Проверяет, есть ли запись с таким именем, исключая указанный ID.
' @role: Validation
' @todo: При необходимости добавить коллацию или обрезку по длине.
    On Error GoTo EH
    
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sql As String
    Dim normName As String
    
    normName = Trim$(itemName)
    
    sql = "SELECT " & GetIdFieldName(dictKind) & _
          " FROM " & GetTableName(dictKind) & _
          " WHERE UCase(" & GetNameFieldName(dictKind) & ")=UCase(" & Q(normName) & ")"
    
    If excludeId > 0 Then
        sql = sql & " AND " & GetIdFieldName(dictKind) & "<>" & excludeId
    End If
    
    sql = sql & ";"
    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    ExistsSimpleDictionaryName = Not rs.EOF
    
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
' @desc: Возвращает имя таблицы Access для указанного вида справочника.
' @role: Mapper
' @todo: При необходимости вынести в конфиг.
    Select Case dictKind
        Case sdkManufacturers:      GetTableName = "Manufacturers"
        Case sdkCategories:         GetTableName = "Categories"
        Case sdkExploitationTypes:  GetTableName = "ExploitationTypes"
        Case sdkProductStatuses:    GetTableName = "ProductStatuses"
        Case sdkDocumentTypes:      GetTableName = "DocumentTypes"
        Case sdkResponsiblePersons: GetTableName = "ResponsiblePersons"
        Case sdkLocations:          GetTableName = "Locations"
        Case Else
            Err.Raise vbObjectError + 1, "GetTableName", "Неизвестный тип справочника: " & dictKind
    End Select
End Function

Private Function GetIdFieldName(ByVal dictKind As SimpleDictionaryKind) As String
' @desc: Возвращает имя поля ID для заданного справочника.
' @role: Mapper
' @todo: При необходимости расширить для сложных сущностей.
    Select Case dictKind
        Case sdkManufacturers:      GetIdFieldName = "ManufacturerID"
        Case sdkCategories:         GetIdFieldName = "CategoryID"
        Case sdkExploitationTypes:  GetIdFieldName = "ExploitationTypeID"
        Case sdkProductStatuses:    GetIdFieldName = "StatusID"
        Case sdkDocumentTypes:      GetIdFieldName = "DocumentTypeID"
        Case sdkResponsiblePersons: GetIdFieldName = "PersonID"
        Case sdkLocations:          GetIdFieldName = "LocationID"
        Case Else
            Err.Raise vbObjectError + 2, "GetIdFieldName", "Неизвестный тип справочника: " & dictKind
    End Select
End Function

Private Function GetNameFieldName(ByVal dictKind As SimpleDictionaryKind) As String
' @desc: Возвращает имя поля названия для заданного справочника.
' @role: Mapper
' @todo: При необходимости добавить Caption поле вместо Name.
    Select Case dictKind
        Case sdkManufacturers:      GetNameFieldName = "ShortName"
        Case sdkCategories:         GetNameFieldName = "CategoryName"
        Case sdkExploitationTypes:  GetNameFieldName = "TypeName"
        Case sdkProductStatuses:    GetNameFieldName = "StatusName"
        Case sdkDocumentTypes:      GetNameFieldName = "TypeName"
        Case sdkResponsiblePersons: GetNameFieldName = "FullName"
        Case sdkLocations:          GetNameFieldName = "LocationName"
        Case Else
            Err.Raise vbObjectError + 3, "GetNameFieldName", "Неизвестный тип справочника: " & dictKind
    End Select
End Function

```

## Черновые заметки

