import json
from datetime import datetime

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///services.db'
db = SQLAlchemy(app)


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<State %r>' % self.name


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.Integer, db.ForeignKey(State.id))

    def __repr__(self):
        return '<Service %r>' % self.name


class StateOfService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.Integer, db.ForeignKey(Service.id))
    state = db.Column(db.Integer, db.ForeignKey(State.id))
    description = db.Column(db.String(255), nullable=False)
    change_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<State of service %r change to %r>' % (self.service, self.state)


def get_states_of_service(service_id):
    states_of_service_obj = StateOfService.query.order_by(StateOfService.change_time.desc()).filter_by(
        service=service_id).all()
    states_dict = get_states_id_name_dict()
    states_of_service = []
    for s_of_s in states_of_service_obj:
        state_of_service = {
            'state_name': states_dict[s_of_s.state],
            'description': s_of_s.description,
            'change_time': str(s_of_s.change_time)[:19]
        }
        states_of_service.append(state_of_service)
    return states_of_service


def get_states_id_name_dict():
    states_obj = State.query.all()
    states_dict = {}
    for state in states_obj:
        states_dict[state.id] = state.name
    return states_dict


def get_all_services():
    services_obj = Service.query.order_by(Service.id).all()
    states_dict = get_states_id_name_dict()
    services_list = []
    for service in services_obj:
        services_list.append({
            'id': service.id,
            'name': service.name,
            'state': states_dict[service.state]
        })
    return services_list


def seconds_to_string(sec):
    result = ''
    if sec > 86400:
        d = round(sec // 86400)
        result += f'{d} д. '
        sec -= d * 86400
    if sec > 3600:
        h = round(sec // 3600)
        result += f'{h} ч. '
        sec -= h * 3600
    if sec > 60:
        m = round(sec // 60)
        result += f'{m} м. '
        sec -= m * 60
    if sec > 0:
        result += f'{round(sec)} с.'
    return result


def get_sla(service_id, start, end):
    states_of_service_obj = StateOfService.query.order_by(StateOfService.change_time).filter_by(
        service=service_id).all()
    states_dict = get_states_id_name_dict()
    start_in_seconds = start.timestamp()
    end_in_seconds = end.timestamp()
    all_time = end_in_seconds - start_in_seconds
    current_state = ''
    time_of_unavailable = 0
    intermediate_time = 0
    for s_of_s in states_of_service_obj:
        if s_of_s.change_time.timestamp() < start_in_seconds:  # Запись раньше начала отсчета
            current_state = states_dict[s_of_s.state]
        else:  # Запись после начала отсчета
            if s_of_s.change_time.timestamp() <= end_in_seconds:  # Запись до конца отсчета
                if current_state == '':
                    time_of_unavailable += s_of_s.change_time.timestamp() - start_in_seconds
                if current_state == 'Не работает':
                    if intermediate_time > 0:
                        time_of_unavailable += s_of_s.change_time.timestamp() - intermediate_time
                    else:
                        time_of_unavailable += s_of_s.change_time.timestamp() - start_in_seconds
                current_state = states_dict[s_of_s.state]
                intermediate_time = s_of_s.change_time.timestamp()
            else:  # Запись позже конца отсчета
                if current_state == 'Не работает' or current_state == '':
                    if intermediate_time > 0:
                        time_of_unavailable += end_in_seconds - intermediate_time
                    else:
                        time_of_unavailable += end_in_seconds - start_in_seconds
    if intermediate_time < start_in_seconds and current_state == 'Не работает':  # Все записи до начала отсчета
        time_of_unavailable += end_in_seconds - start_in_seconds
    answer = {
        'sla': f"{(all_time - time_of_unavailable) / all_time:.3%}",
        'time_of_unavailable': seconds_to_string(time_of_unavailable)
    }
    return answer


@app.get('/')
def index():
    return render_template("index.html")


@app.get('/services')
def services():
    services_list = get_all_services()
    return render_template("services.html", services=services_list)


@app.route('/state_history', methods=['POST', 'GET'])
def state_history():
    service_names = Service.query.order_by(Service.id).all()
    error = ''
    if request.method == "POST":
        if 'service_id' not in request.form:
            error = 'Вы не выбрали сервис'
        else:
            service_id = request.form["service_id"]
            return redirect(f'/state_history/{service_id}')
    context = {
        'services': service_names,
        'error': error
    }
    return render_template("state_history.html", context=context)


@app.get('/state_history/<int:service_id>')
def state_history_of_service(service_id):
    states_of_service = get_states_of_service(service_id)
    context = {
        'service_name': Service.query.get(service_id).name,
        'states_of_service': states_of_service
    }
    return render_template("state_history_of_service.html", context=context)


@app.route('/sla', methods=['POST', 'GET'])
def sla():
    service_names = Service.query.order_by(Service.id).all()
    error = ''
    answer = ''
    if request.method == "POST":
        if 'service_id' not in request.form:
            error += 'Вы не выбрали сервис.   '
        else:
            service_id = request.form["service_id"]
            if request.form["start"] == '' or request.form["end"] == '':
                error += 'Введите время.'
            else:
                start = datetime.strptime(request.form["start"], "%Y-%m-%dT%H:%M")
                end = datetime.strptime(request.form["end"], "%Y-%m-%dT%H:%M")
                if end <= start:
                    error += 'Время конца не может быть раньше времени начала.'
                else:
                    answer = get_sla(service_id, start, end)
                    answer['service_id'] = service_id
                    answer['service'] = Service.query.filter_by(id=service_id).first().name
                    answer['start'] = start
                    answer['end'] = end
    context = {
        'services': service_names,
        'error': error,
        'answer': answer
    }
    return render_template("sla.html", context=context)


@app.route('/add_info', methods=['POST', 'GET'])
def add_info():
    service_names = Service.query.order_by(Service.id).all()
    states = State.query.all()
    context = {
        'services': service_names,
        'states': states
    }
    if request.method == "POST":
        if 'state_id' in request.form:
            state_id = request.form['state_id']
        else:
            return 'Вы не выбрали состояние сервиса'
        description = request.form['description']
        if 'service_id' in request.form:
            service_id = request.form['service_id']
            service_to_change = Service.query.get(service_id)
            service_to_change.state = state_id
            try:
                db.session.commit()
            except:
                return "При обновлении сервиса произошла ошибка"
        else:
            if request.form['service_new_name'] == '':
                return 'Вы не выбрали сервис'
            else:
                service_new_name = request.form['service_new_name']
                new_service = Service(name=service_new_name, state=state_id)
                try:
                    db.session.add(new_service)
                    db.session.commit()
                    service_id = Service.query.filter_by(name=service_new_name).first().id
                except:
                    return "При добавлении сервиса произошла ошибка"
        new_state_of_service = StateOfService(service=service_id, state=state_id, description=description)
        try:
            db.session.add(new_state_of_service)
            db.session.commit()
        except:
            return "При добавлении состояния сервиса произошла ошибка"
        return redirect('/services')
    else:
        return render_template("add_info.html", context=context)


@app.post('/add_info/api')
def add_info_post():
    service_name = request.get_json()['service']
    state_name = request.get_json()['state']
    description = request.get_json()['description']
    if State.query.filter_by(name=state_name).first() is None:
        answer = {"error": "Состояние сервиса может быть Работает / Не работает / Работает нестабильно"}
        return json.dumps(answer, ensure_ascii=False)
    else:
        state_id = State.query.filter_by(name=state_name).first().id

    if Service.query.filter_by(name=service_name).first() is not None:
        service_id = Service.query.filter_by(name=service_name).first().id
        service_to_change = Service.query.get(service_id)
        service_to_change.state = state_id
        try:
            db.session.commit()
        except:
            answer = {"error": "При обновлении сервиса произошла ошибка"}
            return json.dumps(answer, ensure_ascii=False)
    else:
        new_service = Service(name=service_name, state=state_id)
        try:
            db.session.add(new_service)
            db.session.commit()
            service_id = Service.query.filter_by(name=service_name).first().id
        except:
            answer = {"error": "При добавлении сервиса произошла ошибка"}
            return json.dumps(answer, ensure_ascii=False)

    new_state_of_service = StateOfService(service=service_id, state=state_id, description=description)
    try:
        db.session.add(new_state_of_service)
        db.session.commit()
    except:
        answer = {"error": "При добавлении состояния сервиса произошла ошибка"}
        return json.dumps(answer, ensure_ascii=False)
    answer = {"success": "Новая запись добавлена"}
    return json.dumps(answer, ensure_ascii=False)


@app.route('/services/api')
def services_api():
    answer = {"services": get_all_services()}
    return json.dumps(answer, ensure_ascii=False)


@app.post('/state_history/api')
def state_history_post():
    service_name = request.get_json()['service']
    if Service.query.filter_by(name=service_name).first() is not None:
        service_id = Service.query.filter_by(name=service_name).first().id
        states_of_service = get_states_of_service(service_id)
    else:
        states_of_service = "Такой сервис в базе не найден"
    answer = {"state history": states_of_service}
    return json.dumps(answer, ensure_ascii=False)


@app.post('/sla/api')
def sla_post():
    service_name = request.get_json()['service']
    if Service.query.filter_by(name=service_name).first() is not None:
        service_id = Service.query.filter_by(name=service_name).first().id
    else:
        answer = {"error": "Такой сервис в базе не найден"}
        return json.dumps(answer, ensure_ascii=False)
    start = datetime.strptime(request.get_json()['start'], "%Y-%m-%d %H:%M")
    end = datetime.strptime(request.get_json()['end'], "%Y-%m-%d %H:%M")
    print(start, end)
    if end <= start:
        answer = {"error": "Время конца не может быть раньше времени начала"}
    else:
        answer = get_sla(service_id, start, end)
    return json.dumps(answer, ensure_ascii=False)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
