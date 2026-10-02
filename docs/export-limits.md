# Границы переноса

## Ограниченная лицензия

Навык `documents` из установленного набора проверен перед экспортом.
Его `LICENSE.txt` запрещает извлечение и хранение копий вне сервиса,
копирование, распространение и передачу третьим лицам.
Он не скопирован в репозиторий. Для его использования установите официальный плагин
в поддерживаемой среде. Это ограничение относится к этому конкретному компоненту;
остальные копии содержат свои исходные лицензии и сведения об авторах.

## Исторические файлы, которые отсутствуют

Факт прежнего удаления подтверждён локальным манифестом очистки
`classroom_skill_cleanup_manifest_20260713T1006.json` и проверкой исходных путей
2 октября 2026 года. Историческое описание не является копией исходного кода.

Среди отсутствующих школьных навыков:

- `classroom-map`, `school-tutor`, `biology-exam-rf`, `physics-exam-rf`, `spellcheck`.

Среди отсутствующих скриптов:

- `classroom_docs_workflow.py`, `classroom_docs_workflow.sh`;
- `classroom_scan.sh`, `classroom_mark_done.sh`, `classroom_next.sh`, `classroom_reply.sh`;
- `classroom_sync_courses.sh`, `classroom_task_probe.sh`;
- `gmail_gradebook.sh`, `gmail_lessons_plan.sh`;
- `school_browser_fallback.py`, `school_db_init.py`, `school_db_report.py`, `school_db_sync_to_pg.py`;
- `school_mail_run.py`, `school_mail_run.sh`, `school_morning_refresh.sh`;
- `school_quality_check.sh`, `school_tasks_recheck.sh`;
- `youtube_lesson_helper.sh`, `quiz_cache_warmup.sh`, `schedule_quiz_cache_warmup_cron.sh`.

Их реализации не восстановлены и не заменены выдуманными копиями.
При появлении резервной копии можно отдельно проверить и перенести оригиналы.

## Что требуется настроить на другом компьютере

Навыки являются инструкциями и вспомогательными материалами, а не единым приложением.
Google Workspace, браузерные инструменты, мультимедийные API и среда создания артефактов
подключаются отдельно. Локальные ключи и аккаунты не экспортируются.
Сервисные команды из навыков могут быть недоступны вне исходной среды.
