# Importaciones necesarias
from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_mysqldb import MySQL
from flask_mail import Mail, Message

# Inicialización de la aplicación Flask
app = Flask(__name__, template_folder='template')

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'           
app.config['MYSQL_USER'] = 'root'                
app.config['MYSQL_PASSWORD'] = 'Tu contraseña de MySQL'       
app.config['MYSQL_DB'] = 'El nombre de tu base de datos'                  
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'   # Para obtener resultados como diccionarios

# Configuración de Flask-Mail para envío de correos
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'El correo remitente'
app.config['MAIL_PASSWORD'] = 'La contraseña de aplicaciones de ese correo'

# Inicialización de extensiones
mail = Mail(app)
mysql = MySQL(app)
app.secret_key = 'Tu llave secreta'  # Necesaria para las sesiones y flashes

# Ruta principal, redirige al login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Ruta para la página de administrador
@app.route('/admin')
def admin():
    return render_template('admin.html') 

# Ruta para el login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'txtEmail' in request.form and 'txtPassword' in request.form:
        _correo = request.form['txtEmail']
        _password = request.form['txtPassword']
        
        # Consulta a la base de datos
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s AND password = %s', (_correo, _password))
        account = cur.fetchone()
        cur.close()

        if account:
            # Si la cuenta existe, inicia sesión
            session['logeado'] = True
            session['cedula'] = account['cedula']
            session['id_rol'] = account['id_rol']

            # Redirige según el rol del usuario
            if session['id_rol'] == 1:
                return render_template('admin.html')
            elif session['id_rol'] == 2:
                return render_template('usuario.html')
            
            return render_template('admin.html')
        
        else:
            # Si la cuenta no existe o las credenciales son incorrectas
            return render_template('login.html', mensaje='Usuario o contraseña incorrectos') 
    
    # Si es una petición GET, muestra el formulario de login
    return render_template('login.html')

# Ruta para recuperar contraseña
@app.route('/forgotpass', methods=["GET", "POST"])
def forgotpass():
    if request.method == 'POST' and 'txtEmail' in request.form:
        email = request.form['txtEmail']
        
        # Verifica si el correo existe en la base de datos
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s', (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            # Si el usuario existe, envía un correo con el enlace para restablecer la contraseña
            reset_link = url_for('reset_password', email=email, _external=True)
            msg = Message("Reestablecimiento de contraseña", sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"Para restablecer su contraseña, haga clic en el siguiente enlace: {reset_link}"
            mail.send(msg)

            flash('Se ha enviado un correo con instrucciones para restablecer su contraseña.', 'info')
        else:
            flash('No se encontró una cuenta con ese correo electrónico.', 'error')

        return redirect(url_for('login'))

    # Si es una petición GET, muestra el formulario para ingresar el correo
    return render_template('forgotpass.html')

# Ruta para restablecer la contraseña
@app.route('/reset_password', methods=["GET", "POST"])
def reset_password():
    email = request.args.get('email')
    
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password == confirm_password:
            # Si las contraseñas coinciden, actualiza en la base de datos
            cur = mysql.connection.cursor()
            cur.execute('UPDATE usuarios SET password = %s WHERE correo = %s', (new_password, email))
            mysql.connection.commit()
            cur.close()

            flash('Su contraseña ha sido actualizada con éxito.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Las contraseñas no coinciden.', 'error')

    # Si es una petición GET, muestra el formulario para restablecer la contraseña
    return render_template('reset_password.html', email=email)

# Ruta para el registro de nuevos usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Obtiene los datos del formulario
        cedula = request.form['cedula']
        primer_nombre = request.form['primer_nombre']
        segundo_nombre = request.form['segundo_nombre']
        primer_apellido = request.form['primer_apellido']
        segundo_apellido = request.form['segundo_apellido']
        correo = request.form['correo']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        id_rol = request.form['id_rol']

        # Verifica si las contraseñas coinciden
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('register.html')

        # Verifica si el usuario ya existe
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE cedula = %s OR correo = %s', (cedula, correo))
        account = cur.fetchone()
        
        if account:
            flash('La cuenta ya existe con esta cédula o correo electrónico', 'danger')
        else:
            # Inserta el nuevo usuario en la base de datos
            cur.execute('INSERT INTO usuarios (cedula, primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, correo, password, id_rol) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (cedula, primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, correo, password, id_rol))
            mysql.connection.commit()
            flash('Te has registrado exitosamente', 'success')
            return redirect(url_for('home'))
        
        cur.close()

    # Si es una petición GET, muestra el formulario de registro
    return render_template('register.html')

# Inicia la aplicación si este archivo es ejecutado directamente
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)