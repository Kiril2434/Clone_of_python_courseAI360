# Pipeline: пишем .gitlab-ci.yml

### Введение

На лекции мы вместе написали CI/CD-пайплайн для Flask-приложения и разобрали:
- структуру pipeline → stage → job
- cache vs artifacts
- needs и DAG
- rules для условного запуска
- manual job и работу с секретами
- extends для переиспользования

Задача — самостоятельно написать `.gitlab-ci.yml` с нуля под заданные требования. Файл нужно сохранить в этой задаче под именем **`pipeline.yml`** (не `.gitlab-ci.yml`).

Тесты парсят YAML и проверяют структуру: правильные stages, правильные ключи, правильно настроенный кэш и т.д. Реальный пайплайн запускать не нужно тут проверка конкертно на правильность написания, что вы понимаете *как* такой пайплайн писать.
Однако для желающих позапускать пайплайны на реальном инстансе гитлаба - могу пустить на свой, пишите в личку @KIoppert

### Контекст приложения

Представьте Python-приложение со следующей структурой:

```
.
├── app.py
├── tests/
│   └── test_app.py
├── requirements.txt
└── pyproject.toml
```

Вам нужно написать пайплайн, который:
1. Линтит код через `ruff`
2. Прогоняет тесты через `pytest` с покрытием
3. Собирает артефакт сборки
4. Пакует артефакт для деплоя
5. Выкатывает на staging автоматически (только из main)
6. Выкатывает на prod вручную (только из main)

### Требования

#### Структура

1. **Stages.** Объявите ровно эти stage'ы в этом порядке:
   `lint`, `test`, `build`, `deploy`

2. **Job'ы.** Должны быть описаны ровно эти задачи:
   - `lint`, `test`, `build`, `package`, `deploy-staging`, `deploy-prod`

3. **Шаблон.** Заведите скрытый job-шаблон `.python` (имя начинается с точки) с ключом `image: python:3.12`. Все остальные job'ы должны наследоваться от него через `extends: .python` и **не указывать** `image:` напрямую.

#### Кэш и переменные

4. **Глобальные переменные.** На верхнем уровне определите `variables.PIP_CACHE_DIR` со значением `$CI_PROJECT_DIR/.cache/pip`. Чтобы pip мог корректно находить папку с кешом.

5. **Глобальный cache.** На верхнем уровне определите `cache:` с правильным ключом:
   - `cache.key.files` должно содержать `requirements.txt`
   - `cache.key.prefix` должен включать `$CI_JOB_NAME` и `$CI_COMMIT_REF_SLUG` (чтобы изолировать кэш по job'у и ветке)
   - `cache.paths` должно содержать `.cache/pip`

#### Job lint

6. `lint`: stage `lint`, в `script` запускает `ruff check .` после установки `ruff`.

#### Job test

7. `test`: stage `test`, в `script`:
   - устанавливает зависимости из `requirements.txt`
   - запускает `pytest` с генерацией junit XML (`--junitxml=report.xml`) и cobertura coverage (`--cov-report=xml`, файл `coverage.xml`)
8. `test.artifacts`:
   - `when: always` (отчёт сохраняется даже при падении тестов)
   - `reports.junit` указывает на `report.xml`
   - `reports.coverage_report.coverage_format: cobertura`
   - `reports.coverage_report.path: coverage.xml`
   - `expire_in` задан (любое разумное значение)

#### Job build

9. `build`: stage `build`, собирает архив (например, `tar.gz`).
10. `build.artifacts.paths` содержит созданный артефакт. `expire_in` задан.

#### Job package

11. `package`: stage `build`, **зависит только от `build`** через `needs: [build]` (создаёт DAG, не ждёт `test`).

#### Деплой

12. `deploy-staging`: stage `deploy`. Запускается **автоматически** только когда коммит в `main` (через `rules` с `if: $CI_COMMIT_BRANCH == "main"` или равноценное `$CI_DEFAULT_BRANCH`).

13. `deploy-prod`: stage `deploy`. Запускается **только вручную** (`when: manual`) и **только из main**. Оба условия должны быть выполнены — pipeline на других ветках не должен показывать кнопку Play.

### Что надо сдать

Один файл — **`pipeline.yml`** в директории задачи.

### Как проверить локально

```bash
pytest 08.1.GitLabCI/tasks/pipeline/
```

Публичные тесты дадут понять, что базовая структура на месте. Приватные тесты прогонятся при пуше в gitlab.

### Подсказки

- В YAML списки можно писать как `[a, b, c]` или построчно с `-`. Оба варианта валидны.
- Если не уверены в синтаксисе rules или extends — пересмотрите слайды лекции и финальный pipeline из практики.

### Подводные камни

- `extends: .python` это не то же самое, что просто `image: python:3.12`. Тесты проверяют именно использование `extends`.
- `needs: [build]` для `package` — без этого job окажется в обычном последовательном stage и тесты упадут.
- В `deploy-prod` нужны **оба** условия: и `if: branch=main`, и `when: manual`. Только `when: manual` без `if:` даст кнопку Play на любой ветке.
- `cache.key` должен быть словарём с `files:` и `prefix:`, а не строкой.
