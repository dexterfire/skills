# Руководство: Публикация в группу ВК через токен профиля Михаила

## 1. Идентификация и профили

- **Целевая группа**: [vk.ru/glfire_streamer](https://vk.ru/glfire_streamer) («Малышкин GLFire | Играем в игры»)
- **ID группы**: `137821447` (в вызовах API `owner_id = -137821447`).
- **Аккаунт Михаила**: ID `278944561` — владелец/создатель группы (`admin_level: 3`, `can_post: 1`).
- **Профиль Chrome**: `User Data Mikhail` (`C:\Users\glfire\AppData\Local\Google\Chrome\User Data Mikhail`).
- **CDP Порт**: `9223`.

## 2. Механизм работы с токеном

### Почему используется сессия браузера через CDP:
1. Веб-токен VK (`localStorage.getItem('6287487:web_token:login:auth')`) привязан к IP-адресу и браузерной сессии.
2. При вызове `api.vk.ru` напрямую через внешний HTTP-клиент с другим IP, VK возвращает ошибку:
   `error_code: 5, error_subcode: 1130: User authorization failed: access_token was given to another ip address`.
3. Вызов методов VK API через `fetch()` прямо внутри вкладки `vk.ru` в Chrome через CDP (`Runtime.evaluate`) решает проблему привязки IP и капч — все запросы идут с легитимного IP браузера с куками и сессией.

## 3. Методы API

- **Проверка прав**: `groups.getById(group_id="137821447", fields="can_post,is_admin,admin_level")`
- **Загрузка обложки/фото**:
  1. `photos.getWallUploadServer(group_id="137821447")` -> `upload_url`
  2. POST multipart файла на `upload_url` -> `photo`, `server`, `hash`
  3. `photos.saveWallPhoto(group_id="137821447", photo=..., server=..., hash=...)` -> `photo{owner_id}_{id}`
- **Публикация записи**:
  `wall.post(owner_id="-137821447", from_group=1, message=..., attachments=..., publish_date=...)`
