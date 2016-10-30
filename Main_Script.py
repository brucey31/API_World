__author__ = 'brucepannaman'

#!flask/bin/python
from flask import Flask, jsonify, request, make_response, redirect, url_for
from werkzeug.utils import secure_filename
import MySQLdb
import configparser
import time
import datetime


# Set variables for the future
LetterTTC = 4
UPLOAD_FOLDER = '/home/pi/Desktop/Submitted_Letters'

# Get credentials from the conf2.ini file
config = configparser.ConfigParser()
ini = config.read('conf.ini')

HOST = config.get('Brandwritten_DB', 'HOST')
USER = config.get('Brandwritten_DB', 'USER')
PASSWORD = config.get('Brandwritten_DB', 'PASSWORD')


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['pdf', 'docx', 'html'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# AUTHENTICATES USER WITH THEIR AUTHENTICATION CREDS IN
def check_authentication(hashkey):
    cursor.execute("select count(distinct company) from companies where hashkey = '%s';" % hashkey)
    answer = str(cursor.fetchone()).replace("(", "").replace("L,)", "")
    answer = int(answer)
    if answer >= 1:
        print "passed authentication"
        return True


def allowed_file(filename):
    return '.' in filename and \
filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def get_company_id(hashkey):
    # GRAB COMPANY ID TO ASSIGN LETTER FOR
    cursor.execute("select id from companies where hashkey = '%s';" % hashkey)
    return str(cursor.fetchone()).replace("(", "").replace("L,)", "")


# WRITES TO THE DB WHEN CALLED WITH THE TIME AND IP TO COLLECT DATA ON SERVER UPTIME
# e.g curl -i -H "authentication:13f8255273325f929d3ce06011b7a5eacd3bc1ebc6e2d557359ba7c5" -X POST http://api.brandwritten.com:10101/maintenance/api/uptime
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
    # Ensure no html errors
    try:
        if not request.headers or "authentication" not in request.headers:
            return make_response(jsonify({'error': 'Please provide authentication'}),401)
        # Go through authentication
        else:
            if check_authentication(request.headers["authentication"]) == True:
                mandatory_list = ["first_name", "second_name", "first_line_address", "city", "postcode", "salutation_type"]

                # Validation of field names and file types
                print "Validating submitted letter"
                for thing in mandatory_list:
                    if thing not in request.json:
                        return make_response(jsonify({'error': 'Please enter all required details - missing %s' % thing}), 428)
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
                content = 0

                ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                hashkey = request.headers['authentication']
                company_id = get_company_id(hashkey)

                cursor.execute("insert into submitted_letters (letter_created, submit_company_id, first_name,second_name,company,first_line_address,second_line_address, city,postcode,country,salutation_number,content) values ('%s',%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % (ts, company_id, first_name, second_name, company, first_line_address, second_line_address, city, postcode, country, salutation_type, content))
                db.commit()

                # Grab the of the job to return
                cursor.execute("select max(sub.id) from submitted_letters sub inner join companies com on com.id = sub.submit_company_id where hashkey = '%s';" % request.headers['authentication'])
                job_id = str(cursor.fetchone()).replace("(", "").replace("L,)", "")

                return make_response(jsonify({'Call Status': "Success", "Job_id":job_id, "Details": {"first_name": first_name, "second_name": second_name, "first_line_address": first_line_address, "second_line_address": second_line_address, "city": city, "postcode": postcode, "country": country, "salutation_number": salutation_type}}), 200)

            else:
                return make_response(jsonify({'Call Failed': "Unauthenticated Call, Credentials Wrong"}), 401)
    except Exception, e:
        print str(e)
        return make_response(jsonify({'error': 'bad request'}), 400)

@app.route('/handwritten/api/submit_file', methods=['POST'])
def submit_letter_file():
    try:
        # Go through authentication
        if not request.headers or "authentication" not in request.headers:
            return make_response(jsonify({'error': 'Please provide authentication'}), 401)

        else:
            if check_authentication(request.headers["authentication"]) == True:

                if not request.files or 'message' not in request.files:
                    return make_response(jsonify({'Call Failed': "No handwritten message content, please add content"}), 415)
                else:
                    submitted_file = request.files['message']

                if "job_id" not in request.form:
                    return make_response(jsonify({'Call Failed': "No job_id corresponding to previously submitted letter given"}), 415)
                else:
                    job_id = request.form["job_id"]

                hashkey = request.headers['authentication']
                company_id = get_company_id(hashkey)

                cursor.execute("select content from submitted_letters where id = '%s';" % job_id)
                result = str(cursor.fetchone()).replace("(", "").replace("L,)", "")
                print result

                if '1' in result:
                    return make_response(jsonify({'Call Failed': "Message already attached to this letter"}), 415)

                if submitted_file.filename == '' or allowed_file(submitted_file.filename) == False:
                    return make_response(jsonify({'Call Failed': "Incorrect file type"}), 415)

                submitted_filename = str(company_id) + "-" + str(job_id) + "." + str(submitted_file.filename.rsplit('.', 1)[1])
                filename = secure_filename(submitted_filename)
                with open("%s%s" % (UPLOAD_FOLDER, filename), 'wb') as writer:
                    writer.writelines(submitted_file)

                # submitted_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                cursor.execute("update submitted_letters set content = 1 where id = '%s';" % job_id)
                db.commit()

                return make_response(jsonify({'Success': 'Message successfully added to job', "Job_id": job_id }), 200)

    except Exception, e:
        print str(e)
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

                    cursor.execute("select case when datediff(now(),letter_created) <= %s then 'Processing' else 'Sent' end as status, letter_created, first_name, second_name, sub.company, first_line_address, city, postcode, salutation_number, content, sub.id from submitted_letters sub inner join companies com on com.id = sub.submit_company_id where com.hashkey = '%s' and date(letter_created) >= '%s' and date(letter_created) <= '%s';" % (LetterTTC, request.headers['authentication'], start_date, end_date))
                    job_query = cursor.fetchall()

                    jobs= []

                    for job in job_query:

                        param = {}
                        param['Status'] = job[0]
                        param['Letter Created'] = job[1]
                        param['First Name'] = job[2]
                        param['Second Name'] = job[3]
                        param['Company'] = job[4]
                        param['First Line Address'] = job[5]
                        param['City'] = job[6]
                        param['Postcode'] = job[7]
                        param['Salutation Number'] = job[8]
                        if "1" in job[9]:
                            param['Content'] = "Message Attached"
                        else:
                            param['Content'] = "No Message Attached Yet"
                        param['Job Id'] = job[10]

                        jobs.append(param)

                    return make_response(jsonify({'Success': True, "Jobs": jobs}), 200)

            else:
                return make_response(jsonify({'Call Failed': "Unauthenticated Call, Credentials Wrong"}),401)
    except Exception, e:
        print str(e)
        return make_response(jsonify({'error': 'bad request'}), 400)

@app.errorhandler(404)
def not_found(error):
    print error
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    # Open database connection
    db = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWORD, db="brandwritten")
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")

    app.run(host='0.0.0.0', port=10101, debug=True)

    db.close()
