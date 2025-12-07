# CRM
В данный момент просто обработка данных о товарах и сопоставление; в будущем планируется автоматика для работы с накладными и оприходованием товаров.

## Настройка удалённого доступа к GitHub
Чтобы связать локальный репозиторий с GitHub (`origin`):
1. Текущий `origin` уже прописан на `https://github.com/IIIBadWolf/CRM.git`; проверить можно командой `git remote -v`.
2. Если нужно поменять URL (например, на SSH), выполните в корне проекта:
   ```bash
   git remote set-url origin git@github.com:IIIBadWolf/CRM.git
   git remote -v   # убедиться, что origin указывает на корректный адрес
   ```
3. Если origin отсутствует, добавьте его:
   ```bash
   git remote add origin https://github.com/IIIBadWolf/CRM.git
   git remote -v
   ```
4. Для авторизации через HTTPS используйте персональный токен (PAT) вместо пароля; для SSH убедитесь, что ключ добавлен в GitHub и агент.
5. Опубликуйте коммиты: `git push -u origin work` (или другую вашу ветку, например `main`).
6. Перед новой работой: `git pull` для получения свежих изменений.

## Базовый рабочий цикл
- Перед изменениями: `git pull`.
- После правок: `git status` → `git add` → `git commit -m "..."` → `git push`.
- Для фич создавайте ветки: `git checkout -b feature/<описание>` → коммиты → `git push -u origin feature/<описание>` → Pull Request.
