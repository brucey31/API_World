__author__ = 'brucepannaman'

#curl -i -H "Content-Type: application/json" -X POST -d '{"name":"Hannah", "age":25, "position":"On Her Knees"}' http://localhost:10101/directors/api/v1.0/add
#!flask/bin/python
from flask import Flask, jsonify, request, make_response
import MySQLdb
import configparser
import time
import datetime


# Set variables for the future
LetterTTC = 4

# Get credentials from the conf2.ini file
config = configparser.ConfigParser()
ini = config.read('conf.ini')

HOST = config.get('Brandwritten_DB', 'HOST')
USER = config.get('Brandwritten_DB', 'USER')
PASSWORD = config.get('Brandwritten_DB', 'PASSWORD')
app = Flask(__name__)

# AUTHENTICATES USER WITH THEIR AUTHENTICATION CREDS IN
def check_authentication(hashkey):
    cursor.execute("select count(distinct company) from companies where hashkey = '%s';" % hashkey)
    answer = str(cursor.fetchone()).replace("(", "").replace("L,)", "")
    answer = int(answer)
    if answer >= 1:
        print "passed authentication"
        return True

# WRITES TO THE DB WHEN CALLED WITH THE TIME AND IP TO COLLECT DATA ON SERVER UPTIME
@app.route('/maintenance/api/uptime', methods=['POST'])
def check_uptime():

    if not request.headers or "authentication" not in request.headers:
        return jsonify({'error': 'Please provide authentication'})

    else:
        if check_authentication(request.headers["authentication"]) == True:

            uptime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            ip = request.remote_addr

            cursor.execute("insert into uptime_check (call_timestamp, ip) values ('%s', '%s');" % (uptime, ip))
            db.commit()

            return jsonify({'Success': True, "Action": "Uptime tag entered into database"})

        else:
            return make_response(jsonify({'Call Failed': "Unauthenticated Call, Credentials Wrong"}), 401)

@app.route('/handwritten/api/submit', methods=['POST'])
def submit_letters():
    try:
        if not request.headers or "authentication" not in request.headers:
            return make_response(jsonify({'error': 'Please provide authentication'}),401)

        else:
            if check_authentication(request.headers["authentication"]) == True:
                mandatory_list = ["first_name", "second_name", "first_line_address", "city", "postcode", "salutation_type","content"]
                for thing in mandatory_list:
                    if thing not in request.json:
                        print "started looking at things"
                        return make_response(jsonify({'error': 'Please enter all required details - missing %s' % thing}),428)
                    else:
                        continue

                first_name = request.json['first_name']
                second_name = request.json['second_name']
                if 'company' in request.json:
                    company = request.json['company']
                else:
                    company = 'Null'
                first_line_address = request.json['first_line_address']
                if 'second_line_address' in request.json:
                    second_line_address = request.json['second_line_address']
                else:
                    second_line_address = 'Null'
                city = request.json['city']
                postcode = request.json['postcode']
                if "country" in request.json:
                    country = request.json['country']
                else:
                    country = 'Null'
                salutation_type = request.json['salutation_type']
                content = request.json['content']

                ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                # GRAB COMPANY ID TO ASSIGN LETTER FOR
                cursor.execute("select id from companies where hashkey = '%s';" % request.headers['authentication'])
                company_id = str(cursor.fetchone()).replace("(", "").replace("L,)", "")

                cursor.execute("insert into submitted_letters (letter_created, submit_company_id, first_name,second_name,company,first_line_address,second_line_address, city,postcode,country,salutation_number,content) values ('%s',%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % (ts, company_id, first_name, second_name, company, first_line_address, second_line_address, city, postcode, country, salutation_type, content))
                db.commit()

                return make_response(jsonify({'Call Status': "Success", "Details":{"first_name": first_name, "second_name": second_name, "first_line_address": first_line_address, "second_line_address": second_line_address, "city": city, "postcode": postcode, "country": country, "salutation_number": salutation_type}}),200)

            else:
                return make_response(jsonify({'Call Failed': "Unauthenticated Call, Credentials Wrong"}), 401)
    except :
        return make_response(jsonify({'error': 'bad request'}), 400)

@app.route('/handwritten/api/status', methods=['POST'])
def check_status():
    try:
        if not request.headers or "authentication" not in request.headers:
            return make_response(jsonify({'error': 'Please provide authentication'}), 401)

        else:
            if check_authentication(request.headers["authentication"]) == True:

                if not request.json or not 'start_date' or not 'end_date' in request.json:
                    return make_response(jsonify({'error': 'Please provide start_date and end_date parameters'}), 400)

                else:
                    start_date = request.json['start_date']
                    end_date = request.json['end_date']

                    cursor.execute("select case when datediff(now(),letter_created) <= %s then 'Processing' else 'Sent' end as status, letter_created, first_name, second_name, sub.company, first_line_address, city, postcode, salutation_number, substring(content, 0, 3 ) content_preview from submitted_letters sub inner join companies com on com.id = sub.submit_company_id where com.hashkey = '%s' and date(letter_created) >= '%s' and date(letter_created) <= '%s';" % (LetterTTC, request.headers['authentication'], start_date, end_date))
                    job_query = cursor.fetchall()

                    jobs= []

                    for job in job_query:
                        param = {}
                        param['Company'] = job[4]
                        param['Status'] = job[0]
                        param['Letter Created'] = job[1]
                        param['First Name'] = job[2]
                        param['Second Name'] = job[3]
                        param['City'] = job[5]
                        param['Postcode'] = job[6]
                        param['Salutation Number'] = job[7]
                        param['Content Head'] = job[8]
                        jobs.append(param)

                    return make_response(jsonify({'Success': True, "Jobs": jobs}), 200)

            else:
                return make_response(jsonify({'Call Failed': "Unauthenticated Call, Credentials Wrong"}),401)
    except Exception, e:
        print str(e)
        return make_response(jsonify({'error': 'bad request'}), 400)

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
