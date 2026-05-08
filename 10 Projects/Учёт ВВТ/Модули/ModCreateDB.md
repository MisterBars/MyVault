---
type: module
status: done
done_date: 2026-05-03
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - module
  - skill/vba
reward_xp: 50
---
# Модуль
## Назначение
- Для создания пустой БД с готовой структурой и поддержкой старых форматов.

## Важные решения
- Есть возможность развернуть проект на новом рабочем месте.
- Всегда создает БД через библиотеку 2010 года, чтобы избегать конфликт версий 2007 и новее.
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

# Код
```vba
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе**
' @todo: **заметка по процедуре/функции**

Option Explicit

Public Sub CreateVVTDatabase()
' @desc: Точка входа — вызывать из Excel
' @role: Init
' @todo: --
    Dim DB_PATH As String
    DB_PATH = ThisWorkbook.Path & "\vvt_db.accdb"
    If CreateAccessDB(DB_PATH) Then
        RunAllDDL DB_PATH
        ShowInfo "БД создана успешно:" & vbCrLf & DB_PATH, vbInformation
        InitDefaultRoles
        CreateDefaultAdmin
    End If
    CreateVVTMenu
End Sub

Private Function CreateAccessDB(sPath As String) As Boolean
' @desc: Создает чистую БД проекта
' @role: Service
' @todo: --
    Dim oCat As Object
    On Error GoTo ErrHandler
    If Dir(sPath) <> "" Then
        If MsgBox("Файл уже существует. Перезаписать?", vbYesNo) = vbNo Then Exit Function
        Kill sPath
    End If
    Set oCat = CreateObject("ADOX.Catalog")
    oCat.Create "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=" & sPath & ";"
    Set oCat = Nothing
    CreateAccessDB = True
    Exit Function
ErrHandler:
    ShowError "Ошибка создания файла БД.", Err.Number, Err.description
End Function

Private Sub RunAllDDL(sPath As String)
' @desc: Открывает соединение и выполняет DDL по очереди
' @role: Init
' @todo: --
    Dim oCn  As Object
    Dim oCmd As Object
    Dim aSQL() As String
    Dim i    As Long

    On Error GoTo ErrHandler
    Set oCn = CreateObject("ADODB.Connection")
    oCn.Open "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=" & sPath & ";"
    Set oCmd = CreateObject("ADODB.Command")
    oCmd.ActiveConnection = oCn

    aSQL = GetDDLStatements()
    For i = 0 To UBound(aSQL)
        Dim sSQL As String
        sSQL = Trim(aSQL(i))
        If sSQL <> "" Then
            oCmd.CommandText = sSQL
            oCmd.Execute
        End If
    Next i

    oCn.Close
    Set oCmd = Nothing
    Set oCn = Nothing
    Exit Sub
ErrHandler:
    ShowError "Ошибка на шаге " & i & ":" & vbCrLf & _
           Left(aSQL(i), 300), Err.Number, Err.description
End Sub

Private Function GetDDLStatements() As String()
' @desc: Возвращает массив DDL-запросов в правильном порядке
' @role: Init
' @todo: --
    Dim s(200) As String
    Dim n As Long
    n = 0

    ' ===== 1. Roles =====
    s(n) = "CREATE TABLE Roles (" & _
           "RoleID AUTOINCREMENT CONSTRAINT PK_Roles PRIMARY KEY, " & _
           "RoleName TEXT(50) NOT NULL, " & _
           "Description TEXT(255), " & _
           "CanManageUsers YESNO DEFAULT False NOT NULL, " & _
           "CanManageAdmin YESNO DEFAULT False NOT NULL, " & _
           "CanEditAny YESNO DEFAULT False NOT NULL, " & _
           "CanApproveAny YESNO DEFAULT False NOT NULL, " & _
           "CanChangeOwnPwd YESNO DEFAULT True NOT NULL, " & _
           "CONSTRAINT UQ_Roles_RoleName UNIQUE (RoleName))"
    n = n + 1

    ' ===== 2. Services =====
    s(n) = "CREATE TABLE Services (" & _
           "ServiceID AUTOINCREMENT CONSTRAINT PK_Services PRIMARY KEY, " & _
           "ServiceName TEXT(100) NOT NULL, " & _
           "ServiceCode TEXT(20), " & _
           "Description MEMO, " & _
           "IsActive YESNO DEFAULT True NOT NULL)"
    n = n + 1

    ' ===== 3. Users =====
    s(n) = "CREATE TABLE Users (" & _
           "UserID AUTOINCREMENT CONSTRAINT PK_Users PRIMARY KEY, " & _
           "Login TEXT(50) NOT NULL, FullName TEXT(200) NOT NULL, " & _
           "RoleID LONG NOT NULL, PasswordHash TEXT(255) NOT NULL, " & _
           "Salt TEXT(100) NOT NULL, IsActive YESNO DEFAULT True NOT NULL, " & _
           "LastLogin DATETIME, CreatedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "CreatedByUserID LONG, " & _
           "CONSTRAINT UQ_Users_Login UNIQUE (Login), " & _
           "CONSTRAINT FK_Users_Roles FOREIGN KEY (RoleID) REFERENCES Roles (RoleID))"
    n = n + 1

    s(n) = "ALTER TABLE Users ADD CONSTRAINT FK_Users_CreatedBy " & _
           "FOREIGN KEY (CreatedByUserID) REFERENCES Users (UserID)"
    n = n + 1

    ' ===== 4. UserServices =====
    s(n) = "CREATE TABLE UserServices (" & _
           "UserServiceID AUTOINCREMENT CONSTRAINT PK_UserServices PRIMARY KEY, " & _
           "UserID LONG NOT NULL, ServiceID LONG NOT NULL, " & _
           "CanEdit YESNO DEFAULT False NOT NULL, CanApprove YESNO DEFAULT False NOT NULL, " & _
           "CONSTRAINT FK_UserServices_Users FOREIGN KEY (UserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT FK_UserServices_Services FOREIGN KEY (ServiceID) REFERENCES Services (ServiceID), " & _
           "CONSTRAINT UQ_UserServices UNIQUE (UserID, ServiceID))"
    n = n + 1

    ' ===== 5. UserSessions =====
    s(n) = "CREATE TABLE UserSessions (" & _
           "SessionID AUTOINCREMENT CONSTRAINT PK_UserSessions PRIMARY KEY, " & _
           "UserID LONG NOT NULL, SessionToken TEXT(100) NOT NULL, " & _
           "LoginTime DATETIME DEFAULT Now() NOT NULL, LastPing DATETIME, " & _
           "LogoutTime DATETIME, SessionStatus TEXT(20) NOT NULL, " & _
           "WorkbookHost TEXT(100), " & _
           "CONSTRAINT FK_UserSessions_Users FOREIGN KEY (UserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT UQ_UserSessions_Token UNIQUE (SessionToken))"
    n = n + 1

    ' ===== 6. Manufacturers =====
    s(n) = "CREATE TABLE Manufacturers (" & _
           "ManufacturerID AUTOINCREMENT CONSTRAINT PK_Manufacturers PRIMARY KEY, " & _
           "ShortName TEXT(100) NOT NULL, FullName TEXT(255), " & _
           "Address TEXT(255), Phone TEXT(50))"
    n = n + 1

    ' ===== 7. NomenclatureTypes =====
    s(n) = "CREATE TABLE NomenclatureTypes (" & _
           "NomenclatureTypeID AUTOINCREMENT CONSTRAINT PK_NomenclatureTypes PRIMARY KEY, " & _
           "TypeName TEXT(100) NOT NULL, " & _
           "TypeCode TEXT(20), " & _
           "Description TEXT(255), " & _
           "IsActive YESNO DEFAULT True NOT NULL, " & _
           "CONSTRAINT UQ_NomTypes_Name UNIQUE (TypeName), " & _
           "CONSTRAINT UQ_NomTypes_Code UNIQUE (TypeCode))"
    n = n + 1

    ' ===== 8. Nomenclatures =====
    s(n) = "CREATE TABLE Nomenclatures (" & _
           "NomenclatureID AUTOINCREMENT CONSTRAINT PK_Nomenclatures PRIMARY KEY, " & _
           "NomenclatureTypeID LONG NOT NULL, " & _
           "NomenclatureCode TEXT(50) NOT NULL, " & _
           "NomenclatureName TEXT(255), Description MEMO, " & _
           "CONSTRAINT FK_Nom_Type FOREIGN KEY (NomenclatureTypeID) REFERENCES NomenclatureTypes (NomenclatureTypeID))"
    n = n + 1

    ' ===== 9. DocumentTypes =====
    s(n) = "CREATE TABLE DocumentTypes (" & _
           "DocumentTypeID AUTOINCREMENT CONSTRAINT PK_DocumentTypes PRIMARY KEY, " & _
           "TypeName TEXT(100) NOT NULL)"
    n = n + 1

    ' ===== 10. Categories =====
    s(n) = "CREATE TABLE Categories (" & _
           "CategoryID AUTOINCREMENT CONSTRAINT PK_Categories PRIMARY KEY, " & _
           "CategoryNum INTEGER NOT NULL, CategoryName TEXT(50) NOT NULL, Description MEMO)"
    n = n + 1

    ' ===== 11. ExploitationTypes =====
    s(n) = "CREATE TABLE ExploitationTypes (" & _
           "ExploitationTypeID AUTOINCREMENT CONSTRAINT PK_ExploitationTypes PRIMARY KEY, " & _
           "TypeName TEXT(100) NOT NULL)"
    n = n + 1

    ' ===== 12. ProductStatuses =====
    s(n) = "CREATE TABLE ProductStatuses (" & _
           "StatusID AUTOINCREMENT CONSTRAINT PK_ProductStatuses PRIMARY KEY, " & _
           "StatusName TEXT(100) NOT NULL)"
    n = n + 1

    ' ===== 13. ProductDocTypes =====
    s(n) = "CREATE TABLE ProductDocTypes (" & _
           "DocumentTypeID AUTOINCREMENT CONSTRAINT PK_ProductDocTypes PRIMARY KEY, " & _
           "TypeName TEXT(100) NOT NULL, Description TEXT(255), " & _
           "IsActive YESNO DEFAULT True NOT NULL)"
    n = n + 1

    ' ===== 14. ResponsiblePersons =====
    s(n) = "CREATE TABLE ResponsiblePersons (" & _
           "PersonID AUTOINCREMENT CONSTRAINT PK_ResponsiblePersons PRIMARY KEY, " & _
           "FullName TEXT(200) NOT NULL, PersonPosition TEXT(200), " & _
           "WorkPhone TEXT(50), MobilePhone TEXT(50), IsActive YESNO DEFAULT True NOT NULL)"
    n = n + 1

    ' ===== 15. Locations =====
    s(n) = "CREATE TABLE Locations (" & _
           "LocationID AUTOINCREMENT CONSTRAINT PK_Locations PRIMARY KEY, " & _
           "LocationName TEXT(200) NOT NULL, LocationCode TEXT(20), " & _
           "ParentLocationID LONG, RespPersonID LONG)"
    n = n + 1

    s(n) = "ALTER TABLE Locations ADD CONSTRAINT FK_Locations_Parent " & _
           "FOREIGN KEY (ParentLocationID) REFERENCES Locations (LocationID)"
    n = n + 1

    s(n) = "ALTER TABLE Locations ADD CONSTRAINT FK_Locations_Person " & _
           "FOREIGN KEY (RespPersonID) REFERENCES ResponsiblePersons (PersonID)"
    n = n + 1

    ' ===== 16. ArchiveCases =====
    s(n) = "CREATE TABLE ArchiveCases (" & _
           "CaseID AUTOINCREMENT CONSTRAINT PK_ArchiveCases PRIMARY KEY, " & _
           "CaseNumber TEXT(100) NOT NULL, CaseTitle TEXT(255) NOT NULL, " & _
           "PeriodFrom DATETIME, PeriodTo DATETIME, Description MEMO, " & _
           "CreatedByUserID LONG, CreatedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "IsActive YESNO DEFAULT True NOT NULL, " & _
           "CONSTRAINT FK_ArchiveCases_Users FOREIGN KEY (CreatedByUserID) REFERENCES Users (UserID))"
    n = n + 1

    ' ===== 17. Products =====
    Dim sqlA As String
    Dim sqlB As String
    Dim sqlC As String
    Dim sqlD As String

    sqlA = "CREATE TABLE Products (" & _
           "ProductID AUTOINCREMENT CONSTRAINT PK_Products PRIMARY KEY, " & _
           "SerialNumber TEXT(100), DecimalNumber TEXT(100), KVTCode TEXT(50), " & _
           "Quantity DOUBLE NOT NULL DEFAULT 1, " & _
           "ExtNomCode TEXT(100), " & _
           "ParentProductID LONG, NomenclatureID LONG, " & _
           "CategoryID LONG, ExploitationTypeID LONG, IsOnSchedule YESNO, " & _
           "LocationID LONG, RespPersonID LONG, "

    sqlB = "ManufacturerID LONG, ManufactureYear INTEGER, " & _
           "ManufactureMonth INTEGER, ManufactureDay INTEGER, " & _
           "ManufactureDatePrecision TEXT(10), " & _
           "WarrantyPeriod INTEGER, WarrantyPeriodUnit TEXT(10), " & _
           "WarrantyEndDate DATETIME, OperationLifeYears INTEGER, " & _
           "WorkHoursAsOf DATETIME, WorkHoursValue DOUBLE, " & _
           "DocumentTypeID LONG, AcceptanceDocNumber TEXT(100), AcceptanceDate DATETIME, " & _
           "InvNumberOS6 TEXT(100), OS6Date DATETIME, " & _
           "CommOrderNumber TEXT(50), CommissionDate DATETIME, "

    sqlC = "InitialCost CURRENCY, " & _
           "GoldGrams DOUBLE, SilverGrams DOUBLE, PlatinumGrams DOUBLE, MPGGrams DOUBLE, " & _
           "ZipPercent INTEGER, ZipComposition MEMO, " & _
           "StatusID LONG, StateDocPath MEMO, " & _
           "OwnershipStatus TEXT(30), " & _
           "LastServiceDate DATETIME, LastServiceNote TEXT(255), " & _
           "WriteOffStatus TEXT(30), WriteOffPlanYear INTEGER, " & _
           "WriteOffOrdNumber TEXT(100), WriteOffBy TEXT(255), " & _
           "WriteOffDocPath MEMO, WriteOffDate DATETIME, " & _
           "UtilizationNote MEMO, GeneralNote MEMO, " & _
           "CreatedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "CreatedByUserID LONG, UpdatedAt DATETIME, UpdatedByUserID LONG, " & _
           "IsDeleted YESNO DEFAULT False NOT NULL, "

    sqlD = "CONSTRAINT FK_Prod_Parent FOREIGN KEY (ParentProductID) REFERENCES Products (ProductID), " & _
           "CONSTRAINT FK_Prod_Nom FOREIGN KEY (NomenclatureID) REFERENCES Nomenclatures (NomenclatureID), " & _
           "CONSTRAINT FK_Prod_Cat FOREIGN KEY (CategoryID) REFERENCES Categories (CategoryID), " & _
           "CONSTRAINT FK_Prod_Exp FOREIGN KEY (ExploitationTypeID) REFERENCES ExploitationTypes (ExploitationTypeID), " & _
           "CONSTRAINT FK_Prod_Loc FOREIGN KEY (LocationID) REFERENCES Locations (LocationID), " & _
           "CONSTRAINT FK_Prod_Per FOREIGN KEY (RespPersonID) REFERENCES ResponsiblePersons (PersonID), " & _
           "CONSTRAINT FK_Prod_Mfg FOREIGN KEY (ManufacturerID) REFERENCES Manufacturers (ManufacturerID), " & _
           "CONSTRAINT FK_Prod_DType FOREIGN KEY (DocumentTypeID) REFERENCES DocumentTypes (DocumentTypeID), " & _
           "CONSTRAINT FK_Prod_Stat FOREIGN KEY (StatusID) REFERENCES ProductStatuses (StatusID), " & _
           "CONSTRAINT FK_Prod_CrBy FOREIGN KEY (CreatedByUserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT FK_Prod_UpdBy FOREIGN KEY (UpdatedByUserID) REFERENCES Users (UserID))"

    s(n) = sqlA & sqlB & sqlC & sqlD
    n = n + 1

    ' ===== 18. ProductServices =====
    s(n) = "CREATE TABLE ProductServices (" & _
           "ProductServiceID AUTOINCREMENT CONSTRAINT PK_ProductServices PRIMARY KEY, " & _
           "ProductID LONG NOT NULL, ServiceID LONG NOT NULL, " & _
           "IsPrimary YESNO DEFAULT False NOT NULL, AssignedAt DATETIME DEFAULT Now(), " & _
           "AssignedByUserID LONG, " & _
           "CONSTRAINT FK_ProdSvc_Prod FOREIGN KEY (ProductID) REFERENCES Products (ProductID), " & _
           "CONSTRAINT FK_ProdSvc_Svc FOREIGN KEY (ServiceID) REFERENCES Services (ServiceID), " & _
           "CONSTRAINT FK_ProdSvc_By FOREIGN KEY (AssignedByUserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT UQ_ProductServices UNIQUE (ProductID, ServiceID))"
    n = n + 1

    ' ===== 19. InventoryOrders =====
    s(n) = "CREATE TABLE InventoryOrders (" & _
           "InventoryOrderID AUTOINCREMENT CONSTRAINT PK_InventoryOrders PRIMARY KEY, " & _
           "OrderNumber TEXT(50) NOT NULL, OrderDate DATETIME NOT NULL, " & _
           "InventoryDate DATETIME NOT NULL, ServiceID LONG, Status TEXT(20), " & _
           "CommissionChairman TEXT(200), CommissionMembers MEMO, CreatedByUserID LONG, " & _
           "CONSTRAINT FK_InvOrd_Svc FOREIGN KEY (ServiceID) REFERENCES Services (ServiceID), " & _
           "CONSTRAINT FK_InvOrd_User FOREIGN KEY (CreatedByUserID) REFERENCES Users (UserID))"
    n = n + 1

    ' ===== 20. ProductTransfers =====
    s(n) = "CREATE TABLE ProductTransfers (" & _
           "TransferID AUTOINCREMENT CONSTRAINT PK_ProductTransfers PRIMARY KEY, " & _
           "ProductID LONG NOT NULL, TransferType TEXT(30) NOT NULL, " & _
           "OrderNumber TEXT(100), OrderDate DATETIME, TransferDate DATETIME NOT NULL, " & _
           "DestinationOrgName TEXT(255), DestinationAddress MEMO, " & _
           "DestinationContact TEXT(255), BasisDocumentType TEXT(100), " & _
           "BasisDocumentPath MEMO, InventoryOrderID LONG, " & _
           "Comment MEMO, CreatedByUserID LONG, CreatedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "CONSTRAINT FK_Trans_Prod FOREIGN KEY (ProductID) REFERENCES Products (ProductID), " & _
           "CONSTRAINT FK_Trans_Inv FOREIGN KEY (InventoryOrderID) REFERENCES InventoryOrders (InventoryOrderID), " & _
           "CONSTRAINT FK_Trans_User FOREIGN KEY (CreatedByUserID) REFERENCES Users (UserID))"
    n = n + 1

    ' ===== 21. ChangeRequests =====
    s(n) = "CREATE TABLE ChangeRequests (" & _
           "ChangeRequestID AUTOINCREMENT CONSTRAINT PK_ChangeRequests PRIMARY KEY, " & _
           "ProductID LONG NOT NULL, RequestedByUserID LONG NOT NULL, " & _
           "RequestedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "RequestType TEXT(30) NOT NULL, Status TEXT(20) NOT NULL, " & _
           "Comment MEMO, ReviewComment MEMO, ReviewedByUserID LONG, " & _
           "ReviewedAt DATETIME, ApprovalDecision TEXT(20), " & _
           "AppliedAt DATETIME, AppliedByUserID LONG, " & _
           "LockedByUserID LONG, LockedAt DATETIME, LockToken TEXT(100), " & _
           "CONSTRAINT FK_CR_Prod FOREIGN KEY (ProductID) REFERENCES Products (ProductID), " & _
           "CONSTRAINT FK_CR_ReqBy FOREIGN KEY (RequestedByUserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT FK_CR_RevBy FOREIGN KEY (ReviewedByUserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT FK_CR_AppBy FOREIGN KEY (AppliedByUserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT FK_CR_LckBy FOREIGN KEY (LockedByUserID) REFERENCES Users (UserID))"
    n = n + 1

    ' ===== 22. ChangeRequestItems =====
    s(n) = "CREATE TABLE ChangeRequestItems (" & _
           "ChangeItemID AUTOINCREMENT CONSTRAINT PK_ChangeRequestItems PRIMARY KEY, " & _
           "ChangeRequestID LONG NOT NULL, FieldName TEXT(100) NOT NULL, " & _
           "FieldDataType TEXT(20), OldValue MEMO, NewValue MEMO, " & _
           "CONSTRAINT FK_CRI_CR FOREIGN KEY (ChangeRequestID) REFERENCES ChangeRequests (ChangeRequestID))"
    n = n + 1

    ' ===== 23. ProductMetalHistory =====
    s(n) = "CREATE TABLE ProductMetalHistory (" & _
           "MetalHistoryID AUTOINCREMENT CONSTRAINT PK_ProductMetalHistory PRIMARY KEY, " & _
           "ProductID LONG NOT NULL, ChangeDate DATETIME NOT NULL, " & _
           "ChangeType TEXT(30) NOT NULL, Reason TEXT(255), " & _
           "DocumentNumber TEXT(100), DocumentDate DATETIME, DocumentPath MEMO, " & _
           "GoldOld DOUBLE, GoldNew DOUBLE, SilverOld DOUBLE, SilverNew DOUBLE, " & _
           "PlatinumOld DOUBLE, PlatinumNew DOUBLE, MPGOld DOUBLE, MPGNew DOUBLE, " & _
           "ChangedByUserID LONG, ApprovedByUserID LONG, ChangeRequestID LONG, " & _
           "Comment MEMO, CreatedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "CONSTRAINT FK_MH_Prod FOREIGN KEY (ProductID) REFERENCES Products (ProductID), " & _
           "CONSTRAINT FK_MH_ChBy FOREIGN KEY (ChangedByUserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT FK_MH_ApBy FOREIGN KEY (ApprovedByUserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT FK_MH_CR FOREIGN KEY (ChangeRequestID) REFERENCES ChangeRequests (ChangeRequestID))"
    n = n + 1

    ' ===== 24. MetalOperations =====
    s(n) = "CREATE TABLE MetalOperations (" & _
           "MetalOperationID AUTOINCREMENT CONSTRAINT PK_MetalOperations PRIMARY KEY, " & _
           "ProductID LONG NOT NULL, OperationDate DATETIME NOT NULL, " & _
           "OperationType TEXT(30) NOT NULL, AccountingPeriodYear INTEGER NOT NULL, " & _
           "AccountingPeriodHalfYear INTEGER, " & _
           "GoldAmount DOUBLE, SilverAmount DOUBLE, PlatinumAmount DOUBLE, MPGAmount DOUBLE, " & _
           "QuantityItems DOUBLE, BasisDocumentNumber TEXT(100), " & _
           "BasisDocumentDate DATETIME, BasisDocumentPath MEMO, " & _
           "Counterparty TEXT(255), Comment MEMO, CreatedByUserID LONG, " & _
           "CreatedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "CONSTRAINT FK_MO_Prod FOREIGN KEY (ProductID) REFERENCES Products (ProductID), " & _
           "CONSTRAINT FK_MO_User FOREIGN KEY (CreatedByUserID) REFERENCES Users (UserID))"
    n = n + 1

    ' ===== 25. AuditLog =====
    s(n) = "CREATE TABLE AuditLog (" & _
           "AuditLogID AUTOINCREMENT CONSTRAINT PK_AuditLog PRIMARY KEY, " & _
           "TableName TEXT(100) NOT NULL, RecordID LONG NOT NULL, " & _
           "FieldName TEXT(100), OldValue MEMO, NewValue MEMO, " & _
           "ActionType TEXT(10) NOT NULL, BusinessEventType TEXT(50), " & _
           "ChangedByUserID LONG, ChangedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "ChangeRequestID LONG, WorkstationName TEXT(100), " & _
           "CONSTRAINT FK_AL_User FOREIGN KEY (ChangedByUserID) REFERENCES Users (UserID), " & _
           "CONSTRAINT FK_AL_CR FOREIGN KEY (ChangeRequestID) REFERENCES ChangeRequests (ChangeRequestID))"
    n = n + 1

    ' ===== 26. InventoryItems =====
    s(n) = "CREATE TABLE InventoryItems (" & _
           "InventoryItemID AUTOINCREMENT CONSTRAINT PK_InventoryItems PRIMARY KEY, " & _
           "InventoryOrderID LONG NOT NULL, ProductID LONG NOT NULL, " & _
           "SeqNumber INTEGER NOT NULL, SnapName TEXT(255), " & _
           "SnapSerialNum TEXT(100), SnapInventNum TEXT(100), " & _
           "SnapMfgYear TEXT(10), " & _
           "SnapGoldGrams DOUBLE, SnapSilverGrams DOUBLE, " & _
           "SnapPlatinumGrams DOUBLE, SnapMPGGrams DOUBLE, " & _
           "ActualGoldGrams DOUBLE, ActualSilverGrams DOUBLE, " & _
           "ActualPlatinumGrams DOUBLE, ActualMPGGrams DOUBLE, ItemNote MEMO, " & _
           "CONSTRAINT FK_II_Ord FOREIGN KEY (InventoryOrderID) REFERENCES InventoryOrders (InventoryOrderID), " & _
           "CONSTRAINT FK_II_Prod FOREIGN KEY (ProductID) REFERENCES Products (ProductID), " & _
           "CONSTRAINT UQ_InventoryItems UNIQUE (InventoryOrderID, SeqNumber))"
    n = n + 1

    ' ===== 27. ProductDocuments =====
    s(n) = "CREATE TABLE ProductDocuments (" & _
           "DocumentID AUTOINCREMENT CONSTRAINT PK_ProductDocuments PRIMARY KEY, " & _
           "ProductID LONG NOT NULL, DocumentTypeID LONG NOT NULL, " & _
           "DocumentNumber TEXT(100), DocumentDate DATETIME, " & _
           "DocumentTitle TEXT(255), IssuedBy TEXT(255), " & _
           "ReceivedDate DATETIME, ValidUntil DATETIME, FilePath MEMO, " & _
           "Description MEMO, Comment MEMO, ArchiveCaseID LONG, " & _
           "ArchivePage TEXT(50), CreatedByUserID LONG, " & _
           "CreatedAt DATETIME DEFAULT Now() NOT NULL, " & _
           "CONSTRAINT FK_PD_Prod FOREIGN KEY (ProductID) REFERENCES Products (ProductID), " & _
           "CONSTRAINT FK_PD_DType FOREIGN KEY (DocumentTypeID) REFERENCES ProductDocTypes (DocumentTypeID), " & _
           "CONSTRAINT FK_PD_Arc FOREIGN KEY (ArchiveCaseID) REFERENCES ArchiveCases (CaseID), " & _
           "CONSTRAINT FK_PD_User FOREIGN KEY (CreatedByUserID) REFERENCES Users (UserID))"
    n = n + 1

    ' ===== ИНДЕКСЫ =====
    s(n) = "CREATE INDEX IDX_Nom_TypeID ON Nomenclatures (NomenclatureTypeID)": n = n + 1
    s(n) = "CREATE INDEX IDX_NomType_Code ON NomenclatureTypes (TypeCode)": n = n + 1
    s(n) = "CREATE INDEX IDX_Prod_Serial ON Products (SerialNumber)": n = n + 1
    s(n) = "CREATE INDEX IDX_Prod_Decimal ON Products (DecimalNumber)": n = n + 1
    s(n) = "CREATE INDEX IDX_Prod_OS6 ON Products (InvNumberOS6)": n = n + 1
    s(n) = "CREATE INDEX IDX_Prod_ExtNom ON Products (ExtNomCode)": n = n + 1
    s(n) = "CREATE INDEX IDX_Prod_Person ON Products (RespPersonID)": n = n + 1
    s(n) = "CREATE INDEX IDX_Prod_Status ON Products (StatusID)": n = n + 1
    s(n) = "CREATE INDEX IDX_Prod_Deleted ON Products (IsDeleted)": n = n + 1
    s(n) = "CREATE INDEX IDX_Prod_Nom ON Products (NomenclatureID)": n = n + 1
    s(n) = "CREATE INDEX IDX_PS_ProdID ON ProductServices (ProductID)": n = n + 1
    s(n) = "CREATE INDEX IDX_PS_SvcID ON ProductServices (ServiceID)": n = n + 1
    s(n) = "CREATE INDEX IDX_US_UserID ON UserServices (UserID)": n = n + 1
    s(n) = "CREATE INDEX IDX_US_SvcID ON UserServices (ServiceID)": n = n + 1
    s(n) = "CREATE INDEX IDX_PT_ProdID ON ProductTransfers (ProductID)": n = n + 1
    s(n) = "CREATE INDEX IDX_PT_Date ON ProductTransfers (TransferDate)": n = n + 1
    s(n) = "CREATE INDEX IDX_MH_ProdID ON ProductMetalHistory (ProductID)": n = n + 1
    s(n) = "CREATE INDEX IDX_MH_Date ON ProductMetalHistory (ChangeDate)": n = n + 1
    s(n) = "CREATE INDEX IDX_MO_ProdID ON MetalOperations (ProductID)": n = n + 1
    s(n) = "CREATE INDEX IDX_MO_Date ON MetalOperations (OperationDate)": n = n + 1
    s(n) = "CREATE INDEX IDX_MO_Year ON MetalOperations (AccountingPeriodYear)": n = n + 1
    s(n) = "CREATE INDEX IDX_CR_ProdID ON ChangeRequests (ProductID)": n = n + 1
    s(n) = "CREATE INDEX IDX_CR_Status ON ChangeRequests (Status)": n = n + 1
    s(n) = "CREATE INDEX IDX_CR_Locked ON ChangeRequests (LockedByUserID)": n = n + 1
    s(n) = "CREATE INDEX IDX_CRI_CRID ON ChangeRequestItems (ChangeRequestID)": n = n + 1
    s(n) = "CREATE INDEX IDX_AL_Table ON AuditLog (TableName)": n = n + 1
    s(n) = "CREATE INDEX IDX_AL_RecordID ON AuditLog (RecordID)": n = n + 1
    s(n) = "CREATE INDEX IDX_AL_Date ON AuditLog (ChangedAt)": n = n + 1
    s(n) = "CREATE INDEX IDX_AL_CRID ON AuditLog (ChangeRequestID)": n = n + 1
    s(n) = "CREATE INDEX IDX_PD_ProdID ON ProductDocuments (ProductID)": n = n + 1
    s(n) = "CREATE INDEX IDX_PD_DType ON ProductDocuments (DocumentTypeID)": n = n + 1
    s(n) = "CREATE INDEX IDX_PD_Date ON ProductDocuments (DocumentDate)": n = n + 1
    s(n) = "CREATE INDEX IDX_PD_Archive ON ProductDocuments (ArchiveCaseID)": n = n + 1
    s(n) = "CREATE INDEX IDX_AC_Num ON ArchiveCases (CaseNumber)": n = n + 1
    s(n) = "CREATE INDEX IDX_AC_From ON ArchiveCases (PeriodFrom)": n = n + 1
    s(n) = "CREATE INDEX IDX_AC_To ON ArchiveCases (PeriodTo)": n = n + 1
    s(n) = "CREATE INDEX IDX_Sess_UserID ON UserSessions (UserID)": n = n + 1
    s(n) = "CREATE INDEX IDX_Sess_Login ON UserSessions (LoginTime)": n = n + 1
    s(n) = "CREATE INDEX IDX_Sess_Ping ON UserSessions (LastPing)": n = n + 1
    s(n) = "CREATE INDEX IDX_Sess_Status ON UserSessions (SessionStatus)": n = n + 1

    GetDDLStatements = s
End Function
```

## Черновые заметки

