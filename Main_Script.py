__author__ = 'brucepannaman'

#!flask/bin/python
from flask import Flask, jsonify, request, make_response
import MySQLdb
import configparser

# Get credentials from the conf2.ini file
config = configparser.ConfigParser()
ini = config.read('conf.ini')

HOST = config.get('Brandwritten_DB', 'HOST')
USER = config.get('Brandwritten_DB', 'USER')
PASSWORD = config.get('Brandwritten_DB', 'PASSWORD')
app = Flask(__name__)

@app.route('/directors/api/v1.0/list', methods=['GET'])
def get_directors():

    cursor.execute("select * from api_test;")
    directors_query = cursor.fetchall()

    directors = []
    for director in directors_query:
        el_jefe = {}
        el_jefe['name'] = director[1]
        el_jefe['age'] = director[2]
        el_jefe['position'] = director[3]
        directors.append(el_jefe)

    return jsonify({'directors': directors})


@app.route('/directors/api/v1.0/add', methods=['POST'])
def add_directors():

    if not request.json or not 'name' or not 'age' or not 'position' in request.json:
        make_response(jsonify({'error': 'Un-Authorised'}), 400)

    else:

        name = request.json['name']
        age = request.json['age']
        position = request.json['position']

        cursor.execute("insert into api_test (name, age, position) values ('%s', %s, '%s');" % (name, age, position))
        db.commit()

        return jsonify({'task': 'Success - Added %s to the table' % name}), 201

@app.route('/directors/api/v1.0/remove', methods=['POST'])
def delete_directors():

    if not request.json or not 'name' in request.json:
        make_response(jsonify({'error': 'Un-Authorised'}), 400)

    else:

        name = request.json['name']

        cursor.execute("delete from api_test where name = '%s';" % name)
        db.commit()

        return jsonify({'task': 'Success - Removed %s from the table' % name}), 201

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    # Open database connection
    db = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWORD, db="brandwritten")
    # prepare a cursor object using cursor() method
    cursor = db.cursor()

    app.run(host='0.0.0.0', port=10101, debug=True)

    db.close()
