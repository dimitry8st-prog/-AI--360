from uuid import UUID

ROLE_EMPLOYEE_ID = UUID("00000000-0000-4000-8000-000000000001")
ROLE_MANAGER_ID = UUID("00000000-0000-4000-8000-000000000002")
ROLE_METHODIST_ID = UUID("00000000-0000-4000-8000-000000000003")
ROLE_ADMIN_ID = UUID("00000000-0000-4000-8000-000000000004")
ROLE_AUDITOR_ID = UUID("00000000-0000-4000-8000-000000000005")

SYSTEM_ROLES: tuple[tuple[UUID, str, str], ...] = (
    (ROLE_EMPLOYEE_ID, "employee", "Сотрудник: обучение, практика, экзамен, личный прогресс, апелляция"),
    (ROLE_MANAGER_ID, "manager", "Руководитель: назначения команде, прогресс, эскалация проверки"),
    (ROLE_METHODIST_ID, "methodist", "Методист: программы, база знаний, банк вопросов, апелляции"),
    (ROLE_ADMIN_ID, "admin", "Администратор: пользователи, подразделения, настройки AI, журналы"),
    (ROLE_AUDITOR_ID, "auditor", "Аудитор: только чтение версий, попыток и журнала"),
)
