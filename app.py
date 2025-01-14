from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from functools import wraps
import os
from models import PostManager

app = Flask(__name__)
app.secret_key = 'your-secret-key'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'userid' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

manager = PostManager()

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    posts, total_pages = manager.get_all_posts(page=page, per_page=5)
    return render_template('index.html', 
                         posts=posts, 
                         current_page=page, 
                         total_pages=total_pages)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        rst, uname = manager.login_check(userid, password)
        if rst:
            session['userid'] = userid
            session['username'] = uname
            return redirect(url_for('index'))
        return f'<script>alert("로그인에 실패했습니다.");location.href="{url_for('login')}"</script>'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('userid', None)
    session.pop('username', None)
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userid = request.form['userid']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            return f'<script>alert("암호가 일치하지 않습니다.");location.href="{url_for('register')}"</script>'
        if manager.duplicate_member(userid):
            return f'<script>alert("이미 존재하는 아이디 입니다.");location.href="{url_for('register')}"</script>'
        if manager.register_member(userid, username, password):
            return redirect(url_for('index'))
        return f'<script>alert("회원가입에 실패했습니다.");location.href="{url_for('register')}"</script>'
    return render_template('signup.html')

@app.route('/post/add', methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('file')
        
        filename = None
        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        if manager.insert_post(title, content, filename, session.get('userid',None)):
            return redirect(url_for('index'))
        return f'<script>alert("게시글 등록에 실패했습니다.");location.href="{url_for('add_post')}"</script>'
    return render_template('add.html')

@app.route('/post/<int:id>')
@login_required
def view_post(id):
    post = manager.get_post_by_id(id)
    if post:
        return render_template('view.html', post=post)
    return f'<script>alert("존재하지 않는 게시글입니다.");location.href="{url_for('index')}"</script>'

@app.route('/post/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = manager.get_post_by_id(id)
    if not post:
        return f'<script>alert("존재하지 않는 게시글입니다.");location.href="{url_for('index')}"</script>'

    if (post['write_id'] != session['userid']) and post['write_id']:
        return f'<script>alert("작성자만 수정이 가능합니다.");location.href="{url_for('index')}"</script>'
        
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('file')
        
        filename = post['filename']
        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            if post['filename']:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post['filename']))
                except:
                    pass
        
        if manager.update_post(id, title, content, filename):
            return redirect(url_for('view_post', id=id))
        return f'<script>alert("게시글 수정에 실패했습니다.");location.href="{url_for('edit_post', id=id)}"</script>'
    return render_template('edit.html', post=post)

@app.route('/post/delete/<int:id>')
@login_required
def delete_post(id):
    rst, filename = manager.delete_post(id)
    if filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        except OSError:
            pass
    if rst:
        return f'<script>alert("게시글이 성공적으로 삭제되었습니다.");location.href="{url_for('index')}"</script>'
    else:
        return f'<script>alert("게시글 삭제에 실패했습니다.");location.href="{url_for('index')}"</script>'    

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
    #app.run(host="0.0.0.0", port=5003, debug=True)