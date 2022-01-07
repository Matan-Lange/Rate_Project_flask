import pickle
from ast import literal_eval
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, session , make_response
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.forms import RegisterForm, LoginForm, RateForm, Compare2, ChangeText
from app.models import User, Group, Question, Rates, Rank
import pdfkit
import os, sys, subprocess, platform
import base64

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/exp')
@login_required
def exp_page():
    items = [item.number for item in Group.query.filter_by(professor=current_user.professor_name)]

    submited_data = db.session.query(Rates).filter(
        Rates.username == current_user.username).all()
    submited_groups = [int(x.group) for x in submited_data]

    items.sort()
    submited_groups.sort()

    return render_template('exp2.html', items=items, submited_groups=submited_groups)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              name = form.name.data,
                              email_address=form.email_address.data,
                              password=form.password1.data,
                              professor_name=form.professor_name.data)

        db.session.add(user_to_create)
        db.session.commit()

        login_user(user_to_create)
        flash(f'Success! you are logged in as :{user_to_create.username}', category='success')


        return redirect(url_for('exp_page'))
    if form.errors != {}:  # if there are no errors from validations
        for err_msg in form.errors.values():
            flash(f'Error found: {err_msg}', category='danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()

    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()

        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! you are logged in as :{attempted_user.username}', category='success')

            return redirect(url_for('exp_page'))
        else:
            flash('User Name and Password are not a match ! try again.', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    session.clear()
    logout_user()
    flash("You have been logged out!", category="info")
    return redirect(url_for('home_page'))


@app.route('/grouprate/<groupnum>', methods=['GET', 'POST'])
@login_required
def rate_page(groupnum):


    groups_rated_by_users = Rates.query.filter_by(username = current_user.username).all()
    groups_rated_by_users = [item.group for item in groups_rated_by_users]

    if groupnum in groups_rated_by_users: # if user inserted rate close page
        return render_template('Access.html')

    form = RateForm()

    if form.validate_on_submit():
        username = current_user.username
        ans_q1 = form.q1.data
        ans_q2 = form.q2.data
        ans_q3 = form.q3.data
        ans_q4 = form.q4.data
        ans_q5 = form.q5.data
        rate = int(form.rate.data)



        rate_to_create = Rates(username=username, group=groupnum, q1=ans_q1,
                               q2=ans_q2, q3=ans_q3,
                               q4=ans_q4, q5=ans_q5, rate=rate)

        same_rate = db.session.query(Rates).filter(
            Rates.username == current_user.username).filter(Rates.rate == rate).filter(Rates.group != groupnum).all()

        exs_rank = Rank.query.filter_by(username=current_user.username, date=datetime.today().date()).first()


        #is experiment group or not
        check_exp = Rank.query.filter_by(username=username).filter_by(
                date = datetime.today().date()).first()
        exp = False
        if check_exp:
            if check_exp.experiment_group == 1:
                exp = True


        if same_rate and exp:
            rate_to_create = repr(pickle.dumps(rate_to_create))
            same_rate_groups = [x for x in literal_eval(exs_rank.list_rank) if int(x[1]) == rate]
            return redirect(
                url_for('compare_page', rate_to_create=rate_to_create, same_rate_groups=repr(same_rate_groups)))

        flash(f'submited evalutation for group {groupnum}', category='info')

        if exs_rank:
            t = literal_eval(exs_rank.list_rank) # t-temp list
        else:
            t = []

        flag = True
        if t == []:
            t.append((int(groupnum), rate))
            flag = False

        if flag:
            tcopy = t.copy()
            for index, elem in enumerate(tcopy):
                if int(elem[1]) < rate:
                    t.insert(index, ((int(groupnum), rate)))
                    flag = False
                    break

        if flag:
            t.insert(len(t), (int(groupnum), rate))

        # save changes to db
        if exs_rank:
            exs_rank.list_rank = repr(t)
            db.session.commit()
        else:
            rank = Rank(username=current_user.username, date=datetime.today().date(), list_rank=repr(t))
            db.session.add(rank)
            db.session.commit()

        db.session.add(rate_to_create)
        db.session.commit()

        return redirect(url_for('exp_page'))
    else:
        if form.errors != {}:  # if there are no errors from validations
            for err_msg in form.errors.values():
                flash(f'Error found: {err_msg}', category='danger')

    date = datetime.today().date()
    time = datetime.now().strftime("%H:%M:%S")

    questions = Question.query.filter_by(professor_name = current_user.professor_name).all()
    groupname = Group.query.filter_by(number=groupnum).first().name

    return render_template('groupRate.html', group=groupnum, date=date, time=time, questions=questions, form=form,groupname = groupname)


@app.route('/compare_page', methods=['GET', 'POST'])
@login_required
def compare_page():

    rate_to_create = request.args.get('rate_to_create')


    rate_to_create = pickle.loads(literal_eval(rate_to_create))
    groupnum = int(rate_to_create.group)
    same_rates = literal_eval(request.args.get('same_rate_groups'))
    form = Compare2()

    exs_rank = Rank.query.filter_by(username=current_user.username, date=datetime.today().date()).first()

    rank_list = literal_eval(exs_rank.list_rank)
    if int(rate_to_create.group) in [int(item[0]) for item in rank_list]:
        return render_template('Access.html')

    if same_rates == []:

        rank_list = literal_eval(exs_rank.list_rank)
        index = len(rank_list)  # if not bigger then any element insert to end of list
        for i, item in enumerate(rank_list):

            if int(item[1]) < int(rate_to_create.rate):
                index = i
                break

        rank_list.insert(index, (groupnum, rate_to_create.rate))
        exs_rank.list_rank = repr(rank_list)
        db.session.commit()
        db.session.add(rate_to_create)
        db.session.commit()
        return redirect(url_for('exp_page'))

    if request.method == 'POST' and form.select.data:

        exs_rank.number_questions += 1
        db.session.commit()

        pref = form.select.data
        if int(pref) == int(rate_to_create.group):

            rank_list = literal_eval(exs_rank.list_rank)
            index = None
            for i, item in enumerate(rank_list):

                if item[0] == same_rates[0][0]:
                    index = i
                    break

            rank_list.insert(index, (groupnum, rate_to_create.rate))
            exs_rank.list_rank = repr(rank_list)
            db.session.commit()
            db.session.add(rate_to_create)
            db.session.commit()
            return redirect(url_for('exp_page'))
        else:

            same_rates = same_rates[1:]

            rate_to_create = repr(pickle.dumps(rate_to_create))
            return redirect(url_for('compare_page', rate_to_create=rate_to_create, same_rate_groups=repr(same_rates)))

    for r in same_rates:

        if int(r[1]) == int(rate_to_create.rate):
            compare_group = r[0]
            form.select.choices = [(groupnum), (compare_group)]

            compare_name = Group.query.filter_by(number = compare_group).first().name
            group_name = Group.query.filter_by(number = groupnum).first().name

            return render_template('compare2groups.html', groupnum=groupnum, compare_group=compare_group, form=form ,compare_name = compare_name ,group_name = group_name  )



@app.route('/change_text/<groupnum>', methods=['GET', 'POST'])
@login_required
def change_text(groupnum):


    old_rate = Rates.query.filter_by(username=current_user.username).filter_by(group=groupnum).first()

    form = ChangeText()


    if form.validate_on_submit():
        username = current_user.username
        ans_q1 = form.q1.data
        ans_q2 = form.q2.data
        ans_q3 = form.q3.data
        ans_q4 = form.q4.data
        ans_q5 = form.q5.data

        old_rate.q1 = ans_q1
        old_rate.q2 = ans_q2
        old_rate.q3 = ans_q3
        old_rate.q4 = ans_q4
        old_rate.q5 = ans_q5


        db.session.commit()
        flash("changes have been saved!", category="info")
        return redirect(url_for('exp_page'))


    form.q1.data = old_rate.q1
    form.q2.data = old_rate.q2
    form.q3.data = old_rate.q3
    form.q4.data = old_rate.q4
    form.q5.data = old_rate.q5

    questions = Question.query.filter_by(professor_name = current_user.professor_name).all()
    groupname = Group.query.filter_by(number=groupnum).first().name
    return render_template('change_text.html', group=groupnum, questions=questions, form=form,groupname=groupname)








@app.route('/exit&save')
def exit_and_save():
    session.clear()
    logout_user()
    flash("You have been logged out information saved!", category="info")
    return redirect(url_for('home_page'))



#allow convert logo to pdf
def image_file_path_to_base64_string(filepath: str) -> str:
  '''
  Takes a filepath and converts the image saved there to its base64 encoding,
  then decodes that into a string.
  '''
  with open(filepath, 'rb') as f:
    return base64.b64encode(f.read()).decode()



# if the use is local use first return statment if not config env variables.
@app.route('/download')
@login_required
def download_pdf():
    os.environ['PATH'] += os.pathsep + os.path.dirname(sys.executable)
    WKHTMLTOPDF_CMD = subprocess.Popen(
         ['which', os.environ.get('WKHTMLTOPDF_BINARY', 'wkhtmltopdf')],
         stdout=subprocess.PIPE).communicate()[0].strip()

    pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)
    wk_options =  {
             'page-size': 'A4',
             'dpi': 400,
         'encoding': 'UTF-8'
         }

    groups = [str(item.number) for item in Group.query.all()]
    #pdf_data = db.session.query(Rates).filter(Rates.group.in_(groups)).filter_by(username=current_user.username).all()
    questions = [item.description for item in Question.query.filter_by(professor_name = current_user.professor_name).all()]

    full_name = current_user.name
    project_names = db.session.query(Rates,Group).outerjoin(Group,Rates.group == Group.number
                                                           ).filter(Rates.group.in_(groups),Rates.username==current_user.username).all()

    img_string = image_file_path_to_base64_string('app/logo.jpg')


    renderd = render_template('pdf_template.html', pdf_data=project_names, date=datetime.today().date(), questions=questions,full_name = full_name,img_string=img_string)

    #return renderd

    pdf = pdfkit.from_string(renderd,False,configuration=pdfkit_config,options=wk_options)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=output.pdf'

    return response
