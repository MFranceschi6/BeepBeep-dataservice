import os

from flakon import SwaggerBlueprint
from flask import request, jsonify
from beepbeep.dataservice.database import db, User, Run
from sqlalchemy import and_
from datetime import datetime
from .util import bad_response, existing_user
import json
from json import loads

HERE = os.path.dirname(__file__)
YML = os.path.join(HERE, '..', 'static', 'api.yaml')
api = SwaggerBlueprint('API', __name__, swagger_spec=YML)


@api.operation('addRuns')
def add_runs():
    added = 0
    for user, runs in request.json.items():
        runner_id = int(user)
        for run in runs:
            db_run = Run.from_json(run, runner_id)
            db.session.add(db_run)
            added += 1

    if added > 0:
        db.session.commit()

    return "", 204


@api.operation('getRuns')
def get_runs(user_id):
    start_date = request.args.get('start-date')
    finish_date = request.args.get('finish-date')
    fun = True
    if not existing_user(user_id):
        return bad_response(404, 'Error no User with ID '+ user_id)
    try:
        if start_date is not None:
            start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
            fun = and_(fun, start_date <= Run.start_date)
    except ValueError:
        return bad_response(404, 'Error in parsing the start_date parameter: ' + start_date + ' is not a valid date')
    try:
        if finish_date is not None:
            finish_date = datetime.strptime(finish_date, '%Y-%m-%dT%H:%M:%SZ')
            fun = and_(fun, Run.start_date <= start_date)
    except ValueError:
        return bad_response(404, 'Error in parsing the finish_date parameter: ' + finish_date + ' is not a valid date')
    fun = and_(fun, Run.runner_id == user_id)
    runs = db.session.query(Run).filter(fun)
    return jsonify([run.to_json() for run in runs])


@api.operation('getSingleRun')
def get_single_run(user_id, run_id):
    if not existing_user(user_id):
        return bad_response(404, 'Error, No user with ID '+str(user_id))
    q = db.session.query(Run).filter(and_(Run.id == run_id, Run.runner_id == user_id))
    if q.count() == 0:
        return bad_response(404, 'Error, No run with ID '+str(run_id)+' for User')
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
    if existing_user(email=u.email):
        return bad_response(400, 'Error, exists already an user with the email: ' + u.email)
    db.session.add(u)
    db.session.commit()
    return "", 204


@api.operation('updateSingleUser')
def update_single_user(user_id):
    u = User.from_json(request.json)
    if user_id != u.id:
        return bad_response(400, 'user_id mismatch: user_id in path: ' + str(user_id) + ', in json: ' + str(u.id))
    q = db.query(User).filter(User.id == user_id)
    if q.count() == 0:
        return bad_response(404, 'No user with  ID ' + str(user_id))
    us = q.first()
    if us.email != u.email:
        q = db.query(User).filter(User.email == u.email)
        if q.count() > 0:
            return bad_response(400, 'Trying to update the email of the user with: ' + u.email + 'but another user '
                                                                                                 'already has that '
                                                                                                 'email')
    for attr in User.__table__.columns:
        setattr(us, attr, getattr(u, attr))
    db.session.commit()
    return "", 204


@api.operation('deleteSingleUser')
def delete_single_user(user_id):
    q = db.query(User).filter(User.id == user_id)
    if q.count() == 0:
        return bad_response(404, 'No user with ID ' + str(user_id))
    db.session.delete(q.first())
    db.session.commit()
    return "", 204
