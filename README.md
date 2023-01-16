<h1 align="center">Приложение для мониторинга рабочего состояния сервисов</h1>

![](https://github.com/katecapri/images-for-readme/blob/main/flask.png)


##  Описание ##

В базе хранится информация о сервисах и их состояниях - сервис может быть работающим, неработающим, либо может работать, но нестабильно.
![](https://github.com/katecapri/images-for-readme/blob/main/020.png) 


##  Используемые технологии ##

- Python 3.10.2
- Docker
- Flask==2.2.2
- Flask-SQLAlchemy==3.0.2
- Jinja2==3.0.3


##  Инструкция по запуску ##

1. Инициализировать новый репозиторий в папке:

> git init

2. Загрузить репозиторий с проектом:

> git pull https://github.com/katecapri/service_status_api.git

3. Запустить контейнер:

> docker-compose up


##  Результат ##

- По адресу <http://127.0.0.1:5000> открывается главная страница сайта. По адресу <http://127.0.0.1:5000/services> выдется список отслеживаемых сервисов. 

![](https://github.com/katecapri/images-for-readme/blob/main/021.png)

- На странице <http://127.0.0.1:5000/state_history> можно выбрать интересующий сервис и по нему откроется вся история изменения состояний.

![](https://github.com/katecapri/images-for-readme/blob/main/022.png)

- На странице SLA <http://127.0.0.1:5000/sla> рассчитывается уровень сервиса сервиса :) и время его простоя. 

![](https://github.com/katecapri/images-for-readme/blob/main/023.png)

- Пример обращений через Postman.

![](https://github.com/katecapri/images-for-readme/blob/main/024.png)
---
![](https://github.com/katecapri/images-for-readme/blob/main/025.png)
---
![](https://github.com/katecapri/images-for-readme/blob/main/026.png)
![](https://github.com/katecapri/images-for-readme/blob/main/028.png)
---
![](https://github.com/katecapri/images-for-readme/blob/main/027.png)
