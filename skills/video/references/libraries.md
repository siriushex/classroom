# Библиотеки и примеры

Официальные API и репозитории проверены 2026-10-02. Не привязывайся к числу шаблонов из подборки: оно меняется. [reference-catalog.json](reference-catalog.json) хранит проверку ссылок и метаданные лицензии. Перед копированием кода проверяй LICENSE конкретного commit, сохрани attribution. Если лицензия неизвестна, изучай принцип и пиши собственную реализацию; не объявляй код свободным.

## Основной стек

| Средство | Когда применять |
|---|---|
| [Remotion](https://www.remotion.dev/docs/) | Композиция, timeline, кадры, React/SVG, экспорт |
| [Google Fonts API](https://www.remotion.dev/docs/google-fonts) / [local fonts](https://www.remotion.dev/docs/fonts-api) | Управляемая загрузка шрифтов с глифами и нужными начертаниями |
| [Transitions](https://www.remotion.dev/docs/transitions) | Перекрытия и композиция переходов |
| [Motion blur](https://www.remotion.dev/docs/motion-blur) | Размытие по временным выборкам для быстрого движения |
| [Captions](https://www.remotion.dev/docs/captions) | Словесные таймкоды и стилизация проверенной расшифровки |
| [FFmpeg](https://ffmpeg.org/documentation.html) / [libass](https://github.com/libass/libass) | Муксинг, декодирование, цвет, звук, ASS/SSA |

Не устанавливай всё сразу. Сначала имеющиеся инструменты, затем один обоснованный пакет. Для `@remotion/*` подбирай версию установленного `remotion`, не обновляй весь проект автоматически. Нативные SVG предпочтительны для узнаваемых игровых фигур; Three.js добавляй, когда нужна настоящая объёмная сцена, а не только эффект глубины.

## Каталог референсов

| Репозиторий | Что изучать | Ограничение |
|---|---|---|
| [reactvideoeditor/remotion-templates](https://github.com/reactvideoeditor/remotion-templates) | Zoom-through, wipe, parallax, reveal | Отдельные self-contained примеры; LICENSE проверить |
| [tamagossi/react-remotion-presets](https://github.com/tamagossi/react-remotion-presets) | Принципы title/background/text presets | Совместимость и API проверять до переноса |
| [Thedurancode/locomotion-templates](https://github.com/Thedurancode/locomotion-templates) | Компоновка сцен и монтаж продуктовых роликов | Переносить ритм/принцип, не чужой бренд |
| [yanone/fontanimation](https://github.com/yanone/fontanimation) | Анимация параметров variable fonts | Оси и диапазоны конкретного шрифта |
| [motion-canvas](https://github.com/motion-canvas/motion-canvas) | Объясняющая векторная анимация | Отдельный engine; результат интегрировать как материал |
| [openvideodev/react-video-editor](https://github.com/openvideodev/react-video-editor) | Timeline/clip/effect architecture | Не превращать рекламу в разработку редактора |
| [m333x/hygc-editor](https://github.com/m333x/hygc-editor) | Модель keyframes и preview/export | Не считать UI preview равным итоговому рендеру |

Храни только выбранные нужные примеры в проекте `references/`, с source URL, commit, license и назначением. Не клонируй и не запускай все репозитории ради количества. Для Scenario/другой AI-площадки используй её инструменты или разрешённый браузерный workflow, фиксируй реальную модель/длину/формат и лимит. При нехватке лимита готовь локальный вариант с честной маркировкой.
