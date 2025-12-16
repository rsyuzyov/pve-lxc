# Implementation Plan

- [x] 1. Создать модуль определения платформы
  - [x] 1.1 Создать lib/platform.py с OSType enum и OS_TYPE
    - Реализовать enum OSType с значениями WINDOWS, LINUX, MACOS
    - Реализовать функцию _detect_os()
    - Инициализировать OS_TYPE при импорте модуля
    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 1.2 Написать property-based тест для определения ОС
    - **Property 1: OS_TYPE is always valid**
    - **Validates: Requirements 1.1, 1.2**

- [x] 2. Адаптировать lib/system.py
  - [x] 2.1 Добавить проверку OS_TYPE в метод write_file
    - Импортировать OS_TYPE и OSType из lib.platform
    - Обернуть chmod в проверку `if OS_TYPE != OSType.WINDOWS`
    - _Requirements: 2.1, 2.2_
  - [x] 2.2 Добавить проверку OS_TYPE в метод mkdir
    - Обернуть chmod в проверку `if OS_TYPE != OSType.WINDOWS`
    - _Requirements: 2.1, 2.2_

- [x] 3. Адаптировать cli/core/ssh_config.py
  - [x] 3.1 Добавить проверку OS_TYPE в метод _write_config
    - Импортировать OS_TYPE и OSType из lib.platform
    - Обернуть chmod в проверку `if OS_TYPE != OSType.WINDOWS`
    - _Requirements: 2.3_

- [x] 4. Исправить работу с путями
  - [x] 4.1 Исправить cli/core/pve.py
    - Заменить `str(__file__).rsplit("/", 3)[0]` на `str(Path(__file__).parent.parent.parent)`
    - _Requirements: 3.1_
  - [x] 4.2 Исправить cli/core/container.py
    - Заменить `str(__file__).rsplit("/", 3)[0]` на `str(Path(__file__).parent.parent.parent)`
    - _Requirements: 3.1_

- [x] 5. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.
