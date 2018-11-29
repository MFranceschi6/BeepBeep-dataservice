import os, unittest, jwt, pytest
from datetime import datetime
from beepbeep.dataservice.app import create_app
from flask_webtest import TestApp as _TestApp
from beepbeep.dataservice.database import db, User, Run
from unittest import mock
from unittest.mock import patch, Mock
from flask.json import jsonify


_HERE = os.path.dirname(__file__)
with open(os.path.join(_HERE, 'privkey.pem')) as f:
    _KEY = f.read()


def create_token(data):
    return jwt.encode(data, _KEY, algorithm='RS512')


_TOKEN = {'iss': 'beepbeep',
          'aud': 'beepbeep.io'}


class TestViews(unittest.TestCase):
    def setUp(self):
        app = create_app()
        self.app = _TestApp(app)
        self.token = create_token(_TOKEN).decode('ascii')
        self.headers = {'Authorization': 'Bearer ' + self.token}

    

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/beepbeep.dataservice_test.db'

    yield app
    os.unlink('/tmp/beepbeep.dataservice_test.db')


@pytest.fixture
def db_instance(app):
    db.init_app(app)
    db.create_all(app=app)

    with app.app_context():
        yield db


@pytest.fixture
def client(app):
    client = app.test_client()

    yield client


def deletinguser(client, db_instance):
    response=client.delete('/users/1')
    return response


def add_user_again(client, db_instance):
    response = client.post('/users', json={          
                    "id":3,
                    "email": "pinco2@gmail.it",
                    "firstname": "pinco",
                    "lastname": "panco",
                    "age": 2,
                    "weight": 1,
                    "max_hr": 2,
                    "rest_hr": 1,
                    "vo2max": 1
                })
    return response


def add_user(client, db_instance):
    response = client.post('/users', json={          
                    "id":1,
                    "email": "pinco@gmail.it",
                    "firstname": "pinco",
                    "lastname": "panco",
                    "age": 2,
                    "weight": 1,
                    "max_hr": 2,
                    "rest_hr": 1,
                    "vo2max": 1
                })
    return response

def add_user4(client, db_instance):
    response = client.post('/users', json={          
                    "id":None,
                    "email":None ,
                    "firstname": "pinco",
                    "lastname": "panco",
                    "age": 2,
                    "weight": 1,
                    "max_hr": 2,
                    "rest_hr": 1,
                    "vo2max": 1
                })
    return response



def add_user3(client, db_instance):
    response = client.put('/users/15', json={          
                    "id":15,
                    "email": "pinco@gmail.it",
                    "firstname": "pinco",
                    "lastname": "panco",
                    "age": 2,
                    "weight": 1,
                    "max_hr": 2,
                    "rest_hr": 1,
                    "vo2max": 1
                })
    return response
def add_user33(client, db_instance):
    response = client.put('/users/3', json={          
                    "id":3,
                    "email": "pinco@gmail.it",
                    "firstname": "pinco",
                    "lastname": "panco",
                    "age": 2,
                    "weight": 1,
                    "max_hr": 2,
                    "rest_hr": 1,
                    "vo2max": 1
                })
    return response

def add_user2(client, db_instance,idd):
    response = client.put('/users/1', json={          
                    "id":idd,
                    "email": "pinco@gmail.it",
                    "firstname": "pinco",
                    "lastname": "panco",
                    "age": 2,
               #### updating the weight from 1 to 2     
                    "weight": 2,
                    "max_hr": 2,
                    "rest_hr": 1,
                    "vo2max": 1
                })
    return response


### Test:1

def test_users(client, db_instance):
    response = client.get('/users')
    print(response)
    assert response.status_code == 200


def test_verifyall(client, db_instance):
################################################################### Test:2 add user ########################################################################
    response = add_user(client, db_instance)
    response2 = add_user_again(client, db_instance)   ### adding another user
    assert response.status_code == 204
    assert response2.status_code==204
    assert db_instance.session.query(User).filter(User.id==1).count()==1
    assert db_instance.session.query(User).filter(User.id==3).count()==1

################################################################### Test:3 creting new user with same email id ##########################################
    response = add_user(client, db_instance)
    assert response.status_code == 400
    print(db_instance.session.query(User).count())
################################################################### Test:4 creting new user no id and no email ##########################################
    response = add_user4(client, db_instance)
    assert response.status_code == 400
############################################################## Test:5 add run ################################################################################
    response = client.post('/add_runs', json={
                         1 : 
                         [
                          {
                            "title" : "Run",
                            "description" : "Description",
                            "strava_id" : 3,
                            "distance" : 1000,
                            "start_date" : 1520072989,
                            "elapsed_time" : 1000,
                            "average_speed" : 33.23,
                            "average_heartrate": 0,
                            "total_elevation_gain": 12.2
                          },
                          {
                            "title" : "Run1",
                            "description" : "Description1",
                            "strava_id" : 4,
                            "distance" : 1000,
                            "start_date" : 1553072989,
                            "elapsed_time" : 1000,
                            "average_speed" : 30.23,
                            "average_heartrate": 0,
                            "total_elevation_gain": 12.2
                          }  
                         ]
                        })
    assert response.status_code == 204
    assert db_instance.session.query(Run.runner_id==1).count()==2
############################################################## Test:6 adding runs for a user that doesnt exist ################################################################################
    response = client.post('/add_runs', json={
                         4 : 
                         [
                          {
                            "title" : "Run",
                            "description" : "Description",
                            "strava_id" : 3,
                            "distance" : 1000,
                            "start_date" : 1520072989,
                            "elapsed_time" : 1000,
                            "average_speed" : 33.23,
                            "average_heartrate": 0,
                            "total_elevation_gain": 12.2
                          },
                          {
                            "title" : "Run1",
                            "description" : "Description1",
                            "strava_id" : 4,
                            "distance" : 1000,
                            "start_date" : 1553072989,
                            "elapsed_time" : 1000,
                            "average_speed" : 30.23,
                            "average_heartrate": 0,
                            "total_elevation_gain": 12.2
                          }  
                         ]
                        })
    assert response.status_code == 204
    assert db_instance.session.query(Run.runner_id==1).count()==2
########################################################## Test:7 get runs for user 1 ###############################################################################
    response = client.get('/users/1/runs')
    assert response.status_code == 200
########################################################### Test:8 getting runs for a user which doesnt exist ##########################################
    response = client.get('/users/2/runs')
    assert response.status_code == 404
############################################################ Test:9 getting single run specifing user and run id #######################################
    response = client.get('/users/1/runs/1')
    assert response.status_code == 200
    ############################################################ Test:10 getting single run specifing user and run id #######################################
    response = client.get('/users/1/runs/2')
    assert response.status_code == 200
############################################################ Test:11 trying to get a run which doesnt exist for this user #######################################
    response = client.get('/users/1/runs/3')
    assert response.status_code == 404
############################################################ Test:12 verying to get a run for a user who doesnt exist #######################################
    response = client.get('/users/245/runs/1')
    assert response.status_code == 404
############################################################ Test:13 trying to get a single user ########################################## 
    response = client.get('/users/1')
    assert response.status_code == 200
############################################################ Test:14 trying to get a user who doesnt exist ############################################## 
    response = client.get('/users/2')
    assert response.status_code == 404
############################################################ Test:15 updating single user ########################################################## 
    response = add_user2(client, db_instance,1)
    assert response.status_code == 204
    assert db_instance.session.query(User).filter(User.id==1).first().weight==2
################# Test:16 updating single user but wiht conflicting path and Json id ########################################################## 
    response = add_user2(client, db_instance,2)
    assert response.status_code == 400
################# Test:17 updating a user that does not exist ########################################################## 
    response = add_user3(client, db_instance)
    assert response.status_code == 404
################# Test:18 updating a user with conflicting email address ########################################################## 
    response = add_user33(client, db_instance)
    assert response.status_code == 400
################# Test:19 deleting a single user that exist ########################################################## 
    with mock.patch('beepbeep.dataservice.views.swagger.request_utils')as mocked:
        mocked.delete_request_retry.return_value.status_code=204
        response = deletinguser(client, db_instance)
        #print("HJHJHKGJH {}".format(response))
        #print(db_instance.session.query(User).filter(User.id==1).first().id)
        assert response.status_code == 204
    assert db_instance.session.query(User).filter(User.id==1).count()==0
################ Test:20 deleting again ############################################################################ 
    response = deletinguser(client, db_instance)
    assert response.status_code == 404







#i created multiple functions just because i wanted to keep the json post requests seperate.