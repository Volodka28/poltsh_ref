# polirol
Требуется python ~= 3.10.0

Поддерживаемые форматы файлов конфигурации: `JSON`, `YAML`, `TOML`

Ключи не могут содержать в именах пробелы.


## Концепция наследования

Наследование реализуется с помощью ключа `extends`.
В значении необходимо указать путь к родителю.
Пути в файлах разделяются символом двоеточия `:`.


В пути к файлу можно не указывать расширение. (для `base.yml` допустимо `base`). 
Расширение будет проигнорировано если не будет найден нужный файл.
Т.е. Если в одной папке лежит `base.yml` и `base.json` для ясности нужно указать расширение

В случае, если папка содержащая нужный файл добавлена в реестр, 
файл будет доступен как и по полному пути, так и просто по имени

В наследовании пока могут участвовать только словари. Наследоваться от списков или скаляров пока запрещено

Зарезервированные, но не используемые слова (избегайте использования в качестве ключей и значений, имен файлов и тд):
- `super`
- `inherit`
- `global`
- `this`
- `auto`
- `self`

### Примеры
Для примеров используется `YAML`, но для других поддерживаемых форматов поведение эквивалентно.
```yaml
# examples/presets/base.yml
data:
  param: 120.0
  param2: true
tasks:
  mi38-0:
    speed: 0
    timeout: 100
  mi38-100:
    speed: 100
    timeout: 100
```
```yaml
# examples/presets/param2-false.yml
extends: "base"

data:
  extends: "examples/presets/base:data" # наследование значения 'data' из 'base' чтобы сохранить остальные значения
  param2: false
# все остальные данные будут взяты из `base`
```
```yaml
# examples/presets/another-demo.yml
extends: "examples/presets/param2-false"
tasks:
  # так как у 'param2-false' нет 'tasks', 'tasks' будет найден среди его родителей
  extends: "examples/presets/param2-false:tasks"
  extended_tasks:
    # синтетический пример:
    extends: "examples/presets/param2-false:tasks" # вложит всю структуру `tasks` из родителя в `extended_tasks`
  mi38-0:
    # это перезапишет только 'timeout' из этой задачи
    extends: "examples/presets/param2-false:tasks:mi38-0"
    timeout: 1
  mi38-200:
    # этот пример показывает как использовать готовый шаблон.
    # 'mi38-200' будет унаследован от 'mi38-0' c изменением параметра 'speed'
    extends: "examples/presets/another-demo:tasks:mi38-0"
    speed: 200
```
```yaml
# examples/presets/result.yml
# 'Живой' пример того, как будет раскрыт файл 'another-demo.yml'

data:
  param: 120.0
  param2: false
tasks:
  extended_tasks:
    # обратите внимание, что структура была вложена полностью (см. пример выше)
    mi38-0:
      speed: 0
      timeout: 100
    mi38-100:
      speed: 100
      timeout: 100
  mi38-0:
    speed: 0
    timeout: 1
  mi38-100:
    speed: 100
    timeout: 100
  mi38-200:  # 'mi-38-200' унаследовал 'timeout' из 'mi38-0', а значение 'speed' было переопределено
    speed: 200
    timeout: 1
```