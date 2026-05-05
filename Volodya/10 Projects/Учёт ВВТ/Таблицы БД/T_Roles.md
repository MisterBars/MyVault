---
type: db-table
status: in-progress
project: "[[Учёт ВВТ]]"
table_name: Roles
table_order: 1
domain: users-and-rights
db_engine: access
source_of_truth: "[[ModCreateDB]]"
tags:
  - db
  - table
  - access
  - roles
---

# Таблица `Roles`

## Назначение
Хранит роли пользователей системы и их права доступа.
Является справочником — записи создаются один раз при инициализации через `InitDefaultRoles`.

## Бизнес-смысл
Одна запись = одна роль. Роль определяет, что пользователь может делать в системе:
управлять другими пользователями, редактировать данные, согласовывать изменения.

## Поля
| Поле | Тип | Обяз. | PK | FK | Default | Индекс | Описание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RoleID | AutoNumber | Да | Да | Нет | — | PK | Идентификатор роли |
| RoleName | Text(50) | Да | Нет | Нет | — | Unique | Название роли |
| Description | Text(255) | Нет | Нет | Нет | NULL | No | Описание роли |
| CanManageUsers | YesNo | Да | Нет | Нет | False | No | Управление пользователями |
| CanManageAdmin | Да | Нет | Нет | Нет | False | No | Управление администраторами |
| CanEditAny | YesNo | Да | Нет | Нет | False | No | Редактирование любых данных |
| CanApproveAny | YesNo | Да | Нет | Нет | False | No | Согласование любых изменений |
| CanChangeOwnPwd | YesNo | Да | Нет | Нет | True | No | Смена собственного пароля |

## Первичный ключ
- `RoleID`

## Внешние ключи
Нет.

## Уникальные ограничения
- `RoleName`

## Правила заполнения
- `RoleName` — обязателен, уникален.
- Флаги прав — обязательны, по умолчанию `False`, кроме `CanChangeOwnPwd = True`.
- Записи создаются только через `InitDefaultRoles` (Admin, ChiefUser, ServiceEditor, User).

## Правила изменения
- Создавать и изменять роли может только пользователь с `CanManageAdmin = True`.
- `RoleName` нельзя менять у системных ролей через UI — только через `RenameUserLogin`.
- Удаление роли возможно только если на ней нет пользователей — проверяется в `DeleteRoleSafe`.
- Все изменения логируются в `AuditLog`.

## Использование в коде
### Формы
- [[F_ListsDB]] (вкладка 0)
- [[F_Change]] (вкладка 0)

### Модули
- [[ModRoles]]
- [[ModUsers]] (проверка прав)
- [[ModFillsLB]] (FillRolesListBox)

### Связанные таблицы
- [[T_Users]] (Users.RoleID → Roles.RoleID)

## CRUD-операции
| Операция | Где реализовано | Статус |
| --- | --- | --- |
| Create | [[ModRoles]] InitDefaultRoles | in-progress |
| Read | [[ModRoles]] GetAllRoles, GetRoleById, GetRoleByName | in-progress |
| Update | [[ModRoles]] | in-progress |
| Delete | [[ModRoles]] DeleteRoleSafe | in-progress |

## Типовые запросы
```sql
SELECT * FROM Roles ORDER BY RoleName;
```

## Открытые вопросы
- Нужно ли хранить системный флаг `IsSystem` чтобы защитить встроенные роли от удаления?