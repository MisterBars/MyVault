---
type: module
status: done
done_date: 2026-02-05
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - module
  - skill/vba
reward_xp: 50
---
# Модуль

## Назначение

Кратко, за что отвечает модуль, какие задачи решает.

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

Public Type NomenclatureTypeInfo
    nomenclatureTypeID As Long
    typeName As String
    typeCode As String
    description As String
    isActive As Boolean
End Type

Private Const TBL_NOM_TYPES As String = "NomenclatureTypes"
Private Const TBL_NOMS As String = "Nomenclatures"

Private Const FLD_ID As String = "NomenclatureTypeID"
Private Const FLD_NAME As String = "TypeName"
Private Const FLD_CODE As String = "TypeCode"
Private Const FLD_DESC As String = "Description"
Private Const FLD_ACTIVE As String = "IsActive"

Dim DB_PATH As String

Private Function OpenCurrentDb() As DAO.Database
    If SRV_LOC = False Then
        DB_PATH = LOCAL_BASE
    Else
        DB_PATH = SERVER_BASE
    End If
    Set OpenCurrentDb = DBEngine.Workspaces(0).OpenDatabase(DB_PATH)
End Function

Private Sub ValidateNomenclatureTypeInput(ByVal typeName As String, ByVal typeCode As String, ByVal description As String)
    typeName = Trim$(typeName)
    typeCode = Trim$(typeCode)
    Dim message As String
    
    message = Empty
    If LenB(typeName) = 0 Then
        message = message + "Не заполнено название типа номенклатуры." + vbCrLf
    End If

    If Len(typeName) > 100 Then
        message = message + "Название типа номенклатуры не должно быть длиннее 100 символов." + vbCrLf
    End If

    If Len(typeCode) > 20 Then
        message = message + "Код типа номенклатуры не должен быть длиннее 20 символов." + vbCrLf
    End If

    If Len(description) > 255 Then
        message = message + "Описание типа номенклатуры не должно быть длиннее 255 символов." + vbCrLf
    End If
    If message <> Empty Then ShowWarning message
End Sub

Public Function GetNomenclatureTypeById(ByVal nomenclatureTypeID As Long) As NomenclatureTypeInfo
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim info As NomenclatureTypeInfo

    If nomenclatureTypeID <= 0 Then Exit Function

    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset( _
        "SELECT NomenclatureTypeID, TypeName, TypeCode, Description, IsActive " & _
        "FROM NomenclatureTypes WHERE NomenclatureTypeID = " & nomenclatureTypeID, _
        dbOpenSnapshot)

    If Not rs.EOF Then
        info.nomenclatureTypeID = NzLng(rs.Fields(FLD_ID).Value)
        info.typeName = NzStr(rs.Fields(FLD_NAME).Value)
        info.typeCode = NzStr(rs.Fields(FLD_CODE).Value)
        info.description = NzStr(rs.Fields(FLD_DESC).Value)
        info.isActive = NzBool(rs.Fields(FLD_ACTIVE).Value, False)
    End If

    rs.Close
    Set rs = Nothing
    Set db = Nothing

    GetNomenclatureTypeById = info
End Function

Public Function GetNomenclatureTypeIdByName(ByVal typeName As String) As Long
    Dim db As DAO.Database
    Dim rs As DAO.Recordset

    typeName = Trim$(typeName)
    If LenB(typeName) = 0 Then Exit Function

    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset( _
        "SELECT NomenclatureTypeID FROM NomenclatureTypes WHERE TypeName = " & Q(typeName), _
        dbOpenSnapshot)

    If Not rs.EOF Then
        GetNomenclatureTypeIdByName = NzLng(rs.Fields(0).Value)
    End If

    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Function GetNomenclatureTypeIdByCode(ByVal typeCode As String) As Long
    Dim db As DAO.Database
    Dim rs As DAO.Recordset

    typeCode = Trim$(typeCode)
    If LenB(typeCode) = 0 Then Exit Function

    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset( _
        "SELECT NomenclatureTypeID FROM NomenclatureTypes WHERE TypeCode = " & Q(typeCode), _
        dbOpenSnapshot)

    If Not rs.EOF Then
        GetNomenclatureTypeIdByCode = NzLng(rs.Fields(0).Value)
    End If

    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Function NomenclatureTypeNameExists(ByVal typeName As String, Optional ByVal excludeID As Long = 0, Optional ByVal db As DAO.Database = Nothing) As Boolean
    Dim ownDb As Boolean
    Dim rs As DAO.Recordset
    Dim sql As String

    typeName = Trim$(typeName)
    If LenB(typeName) = 0 Then Exit Function

    If db Is Nothing Then
        Set db = OpenCurrentDb()
        ownDb = True
    End If

    sql = "SELECT NomenclatureTypeID FROM NomenclatureTypes WHERE TypeName = " & Q(typeName)
    If excludeID > 0 Then
        sql = sql & " AND NomenclatureTypeID <> " & excludeID
    End If

    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    NomenclatureTypeNameExists = Not rs.EOF

    rs.Close
    Set rs = Nothing
    If ownDb Then Set db = Nothing
End Function

Public Function NomenclatureTypeCodeExists(ByVal typeCode As String, Optional ByVal excludeID As Long = 0, Optional ByVal db As DAO.Database = Nothing) As Boolean
    Dim ownDb As Boolean
    Dim rs As DAO.Recordset
    Dim sql As String

    typeCode = Trim$(typeCode)
    If LenB(typeCode) = 0 Then Exit Function

    If db Is Nothing Then
        Set db = OpenCurrentDb()
        ownDb = True
    End If

    sql = "SELECT NomenclatureTypeID FROM NomenclatureTypes WHERE TypeCode = " & Q(typeCode)
    If excludeID > 0 Then
        sql = sql & " AND NomenclatureTypeID <> " & excludeID
    End If

    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    NomenclatureTypeCodeExists = Not rs.EOF

    rs.Close
    Set rs = Nothing
    If ownDb Then Set db = Nothing
End Function

Public Function CreateNomenclatureType( _
    ByVal typeName As String, _
    ByVal typeCode As String, _
    ByVal description As String, _
    ByVal isActive As Boolean, _
    ByVal changedByUserId As Long) As Long

    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim newID As Long

    typeName = Trim$(typeName)
    typeCode = Trim$(typeCode)
    description = Trim$(description)

    ValidateNomenclatureTypeInput typeName, typeCode, description

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb()

    On Error GoTo EH
    ws.BeginTrans

    If NomenclatureTypeNameExists(typeName, 0, db) Then
        ShowWarning "Тип номенклатуры с названием """ & typeName & """ уже существует в базе."
        GoTo CleanExit
    End If

    If LenB(typeCode) > 0 Then
        If NomenclatureTypeCodeExists(typeCode, 0, db) Then
            ShowWarning "Тип номенклатуры с кодом """ & typeCode & """ уже существует в базе."
            GoTo CleanExit
        End If
    End If

    Set rs = db.OpenRecordset(TBL_NOM_TYPES, dbOpenDynaset, dbAppendOnly)

    rs.AddNew
    rs.Fields(FLD_NAME).Value = typeName
    If LenB(typeCode) > 0 Then
        rs.Fields(FLD_CODE).Value = typeCode
    Else
        rs.Fields(FLD_CODE).Value = Null
    End If
    If LenB(description) > 0 Then
        rs.Fields(FLD_DESC).Value = Left$(description, 255)
    Else
        rs.Fields(FLD_DESC).Value = Null
    End If
    rs.Fields(FLD_ACTIVE).Value = isActive
    rs.Update

    rs.Bookmark = rs.LastModified
    newID = NzLng(rs.Fields(FLD_ID).Value)

    rs.Close
    Set rs = Nothing

    WriteAuditEvent db, TBL_NOM_TYPES, newID, FLD_NAME, vbNullString, typeName, "INSERT", "NomenclatureTypeCreate", changedByUserId, Null
    WriteAuditEvent db, TBL_NOM_TYPES, newID, FLD_CODE, vbNullString, typeCode, "INSERT", "NomenclatureTypeCreate", changedByUserId, Null
    WriteAuditEvent db, TBL_NOM_TYPES, newID, FLD_DESC, vbNullString, Left$(description, 255), "INSERT", "NomenclatureTypeCreate", changedByUserId, Null
    WriteAuditEvent db, TBL_NOM_TYPES, newID, FLD_ACTIVE, vbNullString, BoolToText(isActive), "INSERT", "NomenclatureTypeCreate", changedByUserId, Null

    ws.CommitTrans
    CreateNomenclatureType = newID

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Function

EH:
    On Error Resume Next
    ws.Rollback
    ShowError "CreateNomenclatureType", Err.Number, , Err.description
    Resume CleanExit
End Function

Public Sub UpdateNomenclatureType( _
    ByVal nomenclatureTypeID As Long, _
    ByVal newTypeName As String, _
    ByVal newTypeCode As String, _
    ByVal newDescription As String, _
    ByVal newIsActive As Boolean, _
    ByVal changedByUserId As Long)

    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldInfo As NomenclatureTypeInfo

    If nomenclatureTypeID <= 0 Then
        ShowWarning "Некорректный NomenclatureTypeID."
        GoTo CleanExit
    End If

    newTypeName = Trim$(newTypeName)
    newTypeCode = Trim$(newTypeCode)
    newDescription = Trim$(newDescription)

    ValidateNomenclatureTypeInput newTypeName, newTypeCode, newDescription

    oldInfo = GetNomenclatureTypeById(nomenclatureTypeID)
    If oldInfo.nomenclatureTypeID = 0 Then
        ShowWarning "Тип номенклатуры не найден."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb()

    On Error GoTo EH
    ws.BeginTrans

    If StrComp(oldInfo.typeName, newTypeName, vbTextCompare) <> 0 Then
        If NomenclatureTypeNameExists(newTypeName, nomenclatureTypeID, db) Then
            ShowWarning "Тип номенклатуры с названием """ & newTypeName & """ уже существует в базе."
            GoTo CleanExit
        End If
    End If

    If StrComp(NzStr(oldInfo.typeCode), NzStr(newTypeCode), vbTextCompare) <> 0 Then
        If LenB(newTypeCode) > 0 Then
            If NomenclatureTypeCodeExists(newTypeCode, nomenclatureTypeID, db) Then
                ShowWarning "Тип номенклатуры с кодом """ & newTypeCode & """ уже существует в базе."
                GoTo CleanExit
            End If
        End If
    End If

    Set rs = db.OpenRecordset( _
        "SELECT * FROM NomenclatureTypes WHERE NomenclatureTypeID = " & nomenclatureTypeID, _
        dbOpenDynaset)

    If rs.EOF Then
        ShowWarning "Тип номенклатуры не найден."
        GoTo CleanExit
    End If

    rs.Edit
    rs.Fields(FLD_NAME).Value = newTypeName
    If LenB(newTypeCode) > 0 Then
        rs.Fields(FLD_CODE).Value = newTypeCode
    Else
        rs.Fields(FLD_CODE).Value = Null
    End If
    If LenB(newDescription) > 0 Then
        rs.Fields(FLD_DESC).Value = Left$(newDescription, 255)
    Else
        rs.Fields(FLD_DESC).Value = Null
    End If
    rs.Fields(FLD_ACTIVE).Value = newIsActive
    rs.Update

    rs.Close
    Set rs = Nothing

    If StrComp(oldInfo.typeName, newTypeName, vbBinaryCompare) <> 0 Then
        WriteAuditEvent db, TBL_NOM_TYPES, nomenclatureTypeID, FLD_NAME, oldInfo.typeName, newTypeName, "UPDATE", "NomenclatureTypeUpdate", changedByUserId, Null
    End If

    If NzStr(oldInfo.typeCode) <> NzStr(newTypeCode) Then
        WriteAuditEvent db, TBL_NOM_TYPES, nomenclatureTypeID, FLD_CODE, oldInfo.typeCode, newTypeCode, "UPDATE", "NomenclatureTypeUpdate", changedByUserId, Null
    End If

    If NzStr(oldInfo.description) <> NzStr(newDescription) Then
        WriteAuditEvent db, TBL_NOM_TYPES, nomenclatureTypeID, FLD_DESC, oldInfo.description, newDescription, "UPDATE", "NomenclatureTypeUpdate", changedByUserId, Null
    End If

    If oldInfo.isActive <> newIsActive Then
        WriteAuditEvent db, TBL_NOM_TYPES, nomenclatureTypeID, FLD_ACTIVE, BoolToText(oldInfo.isActive), BoolToText(newIsActive), "UPDATE", "NomenclatureTypeUpdate", changedByUserId, Null
    End If

    ws.CommitTrans

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub

EH:
    On Error Resume Next
    ws.Rollback
    ShowError "UpdateNomenclatureType", Err.Number, , Err.description
    Resume CleanExit
End Sub

Public Sub DeleteNomenclatureTypeSafe(ByVal nomenclatureTypeID As Long, ByVal changedByUserId As Long)
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim info As NomenclatureTypeInfo
    Dim cnt As Long

    If nomenclatureTypeID <= 0 Then
        ShowWarning "Некорректный NomenclatureTypeID."
        GoTo CleanExit
    End If

    info = GetNomenclatureTypeById(nomenclatureTypeID)
    If info.nomenclatureTypeID = 0 Then
        ShowWarning "Тип номенклатуры не найден."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb()

    Set rs = db.OpenRecordset( _
        "SELECT COUNT(*) AS Cnt FROM Nomenclatures WHERE NomenclatureTypeID = " & nomenclatureTypeID, _
        dbOpenSnapshot)

    If Not rs.EOF Then cnt = NzLng(rs.Fields(0).Value)
    rs.Close
    Set rs = Nothing

    If cnt > 0 Then
        ShowWarning "Тип номенклатуры нельзя удалить, так как он используется в номенклатуре. Количество связанных записей: " & cnt & "."
        GoTo CleanExit
    End If

    On Error GoTo EH
    ws.BeginTrans

    db.Execute "DELETE FROM NomenclatureTypes WHERE NomenclatureTypeID = " & nomenclatureTypeID, dbFailOnError

    WriteAuditEvent db, TBL_NOM_TYPES, nomenclatureTypeID, FLD_NAME, info.typeName, "DELETED", "DELETE", "NomenclatureTypeDelete", changedByUserId, Null

    ws.CommitTrans

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub

EH:
    On Error Resume Next
    ws.Rollback
    ShowError "DeleteNomenclatureTypeSafe", Err.Number, , Err.description
    Resume CleanExit
End Sub

Public Function GetAllNomenclatureTypes(Optional ByVal onlyActive As Boolean = False) As DAO.Recordset
    Dim db As DAO.Database
    Dim sql As String

    Set db = OpenCurrentDb()

    sql = "SELECT NomenclatureTypeID, TypeName, TypeCode, Description, IsActive " & _
          "FROM NomenclatureTypes"

    If onlyActive Then
        sql = sql & " WHERE IsActive = True"
    End If

    sql = sql & " ORDER BY TypeName"

    Set GetAllNomenclatureTypes = db.OpenRecordset(sql, dbOpenSnapshot)
End Function
```

## Черновые заметки

