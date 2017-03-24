import os
import datetime
import requests
import json
import redis
from string import ascii_lowercase
from collections import OrderedDict
from operator import itemgetter

from flask import render_template
from flask import Flask, redirect
from flask import request, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.getenv('HOME'), 'temporary')
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = set(['txt'])
outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
jobdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jobdir')
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = outdir
app.config['JOBDIR_FOLDER'] = jobdir

DIRECTORIES = OrderedDict(sorted({
    # "mnsu": "Minnesota State University Mankato",
    "iu": "Indiana University",
    "radu": "Radford University",
    "siuc": "Southern Illinois University Carbondale",
    "osu": "Oklahoma State University",
    # "wsu": "Washington State University",
    "tulane": "Tulane University",
    "wustl": "Washington University in St. Louis",
    "jmu": "James Madison University",
    "odu": "Old Dominion University",
    "uncg": "University of North Carolina at Greensboro",
    "wmuni": "College of William and Mary",
    "gatech": "Georgia Institute of Technology",
    "uindy": "University of Indianapolis",
    "cmich": "Central Michigan University",
    "uoni": "University of Northern Iowa",
    "wfu": "Wake Forest University",
    "uncc": "University of North Carolina Charlotte",
    "uoa": "University of Arizona",
    "uky": "University of Kentucky",
    "uok": "University of Kansas",
    "uoi": "University of Iowa",
    "unl": "University of Nebraska-Lincoln",
    "ust": "University of St. Thomas",
    "colorado": "University of Colorado Boulder",
    "uark": "University of Arkansas",
    "umn": "University of Minnesota",
}.items(), key=itemgetter(1)))

def get_job_data(r, job_id):
    data = json.loads(r.get('job:%s:data' % job_id))
    data['id'] = job_id
    data['progress'] = r.get('job:%s:progress' % data['id']) or 0
    data['dir_name'] = DIRECTORIES.get(data.get('directory', ''), '---')
    return data

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def schedule_spider(data):
    filter_1 = data.get('filter_role', '')
    filter_2 = data.get('filter_campus', '')
    return requests.post("http://localhost:6800/schedule.json", data={
        'project': 'spider',
        'spider': data['directory'],
        'letters': data['letters'],
        'search_type': data['search_type'],
        'output_file': data['output'],
        'input_file': data['input'],
        'filter_role': filter_1,
        'filter_campus': filter_2,
        'setting': 'JOBDIR=%s' % os.path.join(app.config['JOBDIR_FOLDER'], data['jobdir_id'])
    }).json()

@app.route("/", methods=['POST', 'GET'])
def index():
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    notice = None

    if request.method == 'POST':
        spider = request.form.get('directory', None)
        output_file = request.form.get('output', None)
        letters = request.form.getlist('letters', None)
        search_type = request.form.get('search_type', None)
        interval = request.form.get('interval', None)
        input_file = request.files['input']

        extra_data = {}

        for key, value in request.form.iteritems():
            if key.startswith('filter_'):
                extra_data[key] = value

        if not input_file.filename and search_type == 'file':
            notice = 'You want to do a search file, but forgot to send an input file'
        elif not letters and search_type == 'letters':
            notice = 'You want to do a letter search, but did not select any letters'
        elif spider and output_file:
            proxy_file = request.files['proxy']
            input_path = ''

            if input_file.filename:
                filename = secure_filename(input_file.filename)
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                input_file.save(input_path)

            job_data = {
                'search_type': search_type,
                'directory': spider,
                'letters': ','.join(letters),
                'output': output_file,
                'input': input_path,
                'interval': interval,
                'start_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'jobdir_id': datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"),
                'paused': False
            }

            job_data.update(extra_data)
            
            data = schedule_spider(job_data)
            job_data['id'] = data['jobid']
            job_data['orgid'] = data['jobid']

            r.set('job:%s:data' % data['jobid'], json.dumps(job_data))
            r.lpush('jobs', data['jobid'])

            return redirect('/')
        else:
            notice = 'Bad form data'

    job_ids = r.lrange('jobs', 0, -1)
    jobs = []

    # load jobs
    for job_id in job_ids:
        jobs.append(get_job_data(r, job_id))

    return render_template('index.html', alphabet=list(ascii_lowercase), notice=notice, jobs=jobs, dirs=DIRECTORIES)

@app.route('/pause/<jobid>')
def pause(jobid):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    data = get_job_data(r, jobid)

    if data['progress'] == '100':
        return redirect('/')

    if not data['paused']:
        response = requests.post("http://localhost:6800/cancel.json", data={
            'project': 'spider', 
            'job': jobid
        }).json()

        response = requests.get("http://localhost:6800/listjobs.json?project=spider").json()

        data['paused'] = True

        for job in response['running']:
            if job['id'] == jobid:
                data['paused'] = False
    else:
        response = schedule_spider(data)

        r.lrem('jobs', 1, data['id'])

        data['paused'] = False
        jobid = data['id'] = response['jobid']

        r.lpush('jobs', data['id'])


    r.set('job:%s:data' % jobid, json.dumps(data))

    return redirect('/')

@app.route('/output/<path:filename>')
def download_output_file(filename):
    output_dir = os.path.join(os.getenv('HOME'), 'temp_files')
    return send_from_directory(output_dir, filename)

@app.route('/static/<path:filename>')
def static_file(filename):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(base_path, filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4444, debug=True)
