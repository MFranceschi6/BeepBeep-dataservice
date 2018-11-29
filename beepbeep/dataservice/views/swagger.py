import os

from flakon import SwaggerBlueprint, request_utils
from flask import request, jsonify
from beepbeep.dataservice.database import db, User, Run, ReportPeriodicity
from sqlalchemy import and_
from datetime import datetime
from .util import bad_response, existing_user
from requests import RequestException
from stravalib import client


HERE = os.path.dirname(__file__)
YML = os.path.join(HERE, '..', 'static', 'api.yaml')
api = SwaggerBlueprint('API', __name__, swagger_spec=YML)


@api.operation('addRuns')
def add_runs():
    added = 0
    for user, runs in request.json.items():
        q = db.session.query(User).filter(User.id == int(user))
        if q.count() == 0:
            continue
        u = q.first()
        for run in runs:
            db_run = Run.from_json(run, u.id)
            q = db.session.query(Run).filter(Run.strava_id == db_run.strava_id)
            if q.count() > 0:
                continue
            u.total_speed += db_run.average_speed
            u.total_runs += 1
            db.session.add(db_run)
            added += 1

    if added > 0:
        db.session.commit()

    return "", 204


@api.operation('getAverage')
def get_average_speed(user_id):
    q = db.session.query(User).filter(User.id == user_id)
    if q.count() == 0:
        return bad_response(404, 'Error no User with ID ' + user_id)
    u = q.first()
    average_speed = u.total_speed / u.total_runs if u.total_runs > 0 else 0
    return {'average_speed': float('%.2f' % average_speed)}


@api.operation('getRuns')
def get_runs(user_id):
    start_date = request.args.get('start-date')
    finish_date = request.args.get('finish-date')
    max_id = request.args.get('from-id')
    page = request.args.get('page')
    per_page = request.args.get('per_page')

    if per_page is None:
        per_page = 10
    per_page = int(per_page)

    if page is None:
        per_page = None
    else:
        page = int(page)

    fun = True
    if not existing_user(user_id):
        return bad_response(404, 'Error no User with ID ' + user_id)
    if start_date is not None:
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
        fun = and_(fun, start_date <= Run.start_date)
    if finish_date is not None:
        finish_date = datetime.strptime(finish_date, '%Y-%m-%dT%H:%M:%SZ')
        fun = and_(fun, Run.start_date <= finish_date)
    if max_id is not None:
        fun = and_(fun, Run.id > max_id)
    fun = and_(fun, Run.runner_id == user_id)
    runs = db.session.query(Run).filter(fun)

    if page is not None and per_page is not None:
        offset = page * per_page
        runs = runs.offset(offset).limit(per_page)

    return jsonify([run.to_json() for run in runs])


@api.operation('getSingleRun')
def get_single_run(user_id, run_id):
    if not existing_user(user_id):
        return bad_response(404, 'Error, No user with ID ' + str(user_id))
    q = db.session.query(Run).filter(and_(Run.id == run_id, Run.runner_id == user_id))
    if q.count() == 0:
        return bad_response(404, 'Error, No run with ID ' + str(run_id) + ' for User')
    return q.first().to_json()


@api.operation('getUsers')
def get_users():
    users = db.session.query(User)
    page = 0
    page_size = None
    if page_size:
        users = users.limit(page_size)
    if page != 0:
        users = users.offset(page * page_size)
    return {'users': [user.to_json(secure=True) for user in users]}


@api.operation('getSingleUser')
def get_single_user(user_id):
    q = db.session.query(User).filter(User.id == user_id)
    if q.count() == 0:
        return bad_response(404, 'No user with ID ' + str(user_id))
    return q.first().to_json(secure=False)


@api.operation('addUser')
def add_single_user():
    u = User.from_json(request.json)
    if existing_user(u.id, u.email):
        return bad_response(400, 'Error, exists already an user with the email: ' + u.email)
    db.session.add(u)
    db.session.commit()
    return "", 204


@api.operation('updateSingleUser')
def update_single_user(user_id):
    user_id = int(user_id)
    u = User.from_json(request.json)
    if user_id != u.id:
        return bad_response(400, 'user_id mismatch: user_id in path: ' + str(user_id) + ', in json: ' + str(u.id))
    q = db.session.query(User).filter(User.id == user_id)
    if q.count() == 0:
        return bad_response(404, 'No user with  ID ' + str(user_id))
    us = q.first()
    if us.email != u.email:
        q = db.session.query(User).filter(User.email == u.email)
        if q.count() > 0:
            return bad_response(400, 'Trying to update the email of the user with: ' + u.email + 'but another user '
                                                                                                 'already has that '
                 
                                                                                                 'email')
    for attr in request.json:
        setattr(us, attr, request.json[attr])
    print(us)
    db.session.commit()
    return "", 204


@api.operation('deleteSingleUser')
def delete_single_user(user_id):
    q = db.session.query(User).filter(User.id == user_id)
    if q.count() == 0:
        return bad_response(404, 'No user with ID ' + str(user_id))
    u = q.first()
    try:
        request_utils.delete_request_retry(request_utils.challenges_endpoint(u.id))
        request_utils.delete_request_retry(request_utils.objectives_endpoint(u.id))
    except RequestException:
        return bad_response(400, 'Error removing the user')
    if u.strava_token is not None:
        c = client.Client(access_token=u.strava_token)
        c.deauthorize()
    db.session.delete(q.first())
    db.session.commit()
    return "", 204
