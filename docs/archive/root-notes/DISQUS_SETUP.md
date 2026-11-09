# Настройка Disqus для комментариев без регистрации

## Шаг 1: Регистрация в Disqus

1. Перейдите: https://disqus.com/
2. Нажмите **"Get Started"** или **"Sign Up"**
3. Зарегистрируйтесь (можно через Google/GitHub/Facebook или email)
4. После регистрации перейдите в панель управления

## Шаг 2: Создать сайт (Site)

1. В панели управления нажмите **"Add Disqus to site"** или **"I want to install Disqus on my site"**
2. Заполните форму:
   - **Website Name**: `WSDC Analytics` (или другое название)
   - **Website URL**: `https://wsdc-analytics.github.io`
   - **Category**: `Education` или `Other`
   - **Language**: `Russian` (для RU версии) или `English` (для EN версии)
3. Нажмите **"Create Site"**

## Шаг 3: Получить Shortname

После создания сайта вы получите **Shortname** (уникальный идентификатор).

**Пример:** `wsdc-analytics` или `wsdcanalytics`

Этот Shortname будет использоваться в коде.

## Шаг 4: Настроить анонимные комментарии

1. Перейдите в **Settings** вашего сайта
2. Найдите раздел **"Community Rules"** или **"Moderation"**
3. Убедитесь, что включена опция **"Allow guest commenting"** или **"Enable anonymous commenting"**

## Шаг 5: Код для вставки

Disqus предоставит вам код вида:

```html
<div id="disqus_thread"></div>
<script>
    (function() {
    var d = document, s = d.createElement('script');
    s.src = 'https://YOUR-SHORTNAME.disqus.com/embed.js';
    s.setAttribute('data-timestamp', +new Date());
    (d.head || d.body).appendChild(s);
    })();
</script>
<noscript>Please enable JavaScript to view the <a href="https://disqus.com/?ref_noscript">comments powered by Disqus.</a></noscript>
```

Нужно заменить `YOUR-SHORTNAME` на ваш Shortname.

---

## После получения Shortname

Сообщите мне Shortname, и я:
1. Заменю Giscus на Disqus
2. Настрою для обеих версий (RU и EN)
3. Добавлю правильную конфигурацию

**Или** можете добавить код сами, если предпочитаете.

