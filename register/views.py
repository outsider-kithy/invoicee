from flask import redirect,render_template,request,url_for,flash,Blueprint
from werkzeug.security import generate_password_hash
from models import session,User

register = Blueprint(
    "register",
    __name__,
    template_folder="templates",
)

@register.route("/",methods=("GET","POST"))
def index():
    if request.method=="GET":
        return render_template("register/index.html")
    
    elif request.method=="POST":
        #名前が入力されていなかったら
        if not request.form.get("username"):
            error="名前を入力してください"
            flash(error)
        #パスワードが入力されていなかったら
        elif not request.form.get("password"):
            error="パスワードを入力してください"
            flash(error)
        #パスワードの確認が入力されていなかったら
        elif not request.form.get("confirmation"):
            error="パスワードをもう一度入手してください"
            flash(error)
        else:
            username=request.form.get("username")
            #print(username)
            password=request.form.get("password")
            #print(password)
            confirmation=request.form.get("confirmation")
            #print(confirmation)
        
            #パスワードとパスワードの確認の入力が一致しなかったら
            if password!=confirmation:
                error="入力されたパスワードが一致しません"
                flash(error)
            else:
                error=None
                hashed=generate_password_hash(password)
                #print(hashed)
                session.add(User(username=username,password=hashed))
                session.commit()
                return redirect(url_for('login.index'))
        
        return render_template('register/index.html',error=error)
            